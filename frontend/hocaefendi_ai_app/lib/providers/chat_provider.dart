import 'dart:async';
import 'dart:io';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import '../models/chat_message.dart';
import '../services/api_service.dart';

class ChatState {
  final List<ChatMessage> messages;
  final bool isLoading;
  final String? error;
  final String currentEmotion;

  ChatState({
    required this.messages,
    this.isLoading = false,
    this.error,
    this.currentEmotion = 'tefekkur',
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isLoading,
    String? error,
    String? currentEmotion,
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
      currentEmotion: currentEmotion ?? this.currentEmotion,
    );
  }
}

class ChatNotifier extends StateNotifier<ChatState> {
  ChatNotifier() : super(ChatState(messages: [
    ChatMessage(
      text: 'Esselâmu aleyküm aziz kardeşim. Gönlünüze takılanları benimle paylaşabilirsiniz.',
      isUserMessage: false,
      timestamp: DateTime.now(),
    ),
  ]));

  Future<void> sendMessage(String text) async {
    final userMessage = ChatMessage(
      text: text,
      isUserMessage: true,
      timestamp: DateTime.now(),
    );

    state = state.copyWith(
      messages: [...state.messages, userMessage],
      isLoading: true,
      error: null,
    );

    final aiPlaceholder = ChatMessage(
      text: '',
      isUserMessage: false,
      timestamp: DateTime.now(),
    );
    state = state.copyWith(
      messages: [...state.messages, aiPlaceholder],
    );

    try {
      final history = state.messages
          .where((m) => m.text.isNotEmpty)
          .map((msg) => {
                'role': msg.isUserMessage ? 'user' : 'assistant',
                'content': msg.text,
              })
          .toList();

      String fullText = '';

      await for (final chunk in ApiService.streamMessage(
        message: text,
        history: history,
      )) {
        fullText += chunk;
        final updatedMessages = [...state.messages];
        updatedMessages[updatedMessages.length - 1] = ChatMessage(
          text: fullText,
          isUserMessage: false,
          timestamp: aiPlaceholder.timestamp,
        );
        state = state.copyWith(
          messages: updatedMessages,
          isLoading: false,
        );
      }

      // Duyguyu al
      final emotionResponse = await ApiService.sendMessage(
        message: text,
        history: history,
      );
      state = state.copyWith(
        currentEmotion: emotionResponse['emotion'] as String? ?? state.currentEmotion,
      );

      // ✅ TTS — try bloğunun İÇİNDE, fullText erişilebilir
      try {
        final audioBytes = await ApiService.synthesizeSpeech(fullText);
        final dir = await getTemporaryDirectory();
        final file = File('${dir.path}/response.wav');
        await file.writeAsBytes(audioBytes);
        final player = AudioPlayer();
        await player.play(DeviceFileSource(file.path));
      } catch (_) {
        // Ses çalma hatası sessizce geç
      }

    } catch (e) {
      final errorMessage = ChatMessage(
        text: 'Bağlantı sorunu: ${e.toString()}',
        isUserMessage: false,
        timestamp: DateTime.now(),
      );
      state = state.copyWith(
        messages: [...state.messages, errorMessage],
        isLoading: false,
      );
    }
  }

  Future<void> sendVoiceMessage(List<int> audioBytes) async {
    state = state.copyWith(isLoading: true, error: null);

    try {
      final text = await ApiService.transcribeAudio(audioBytes);

      if (text.trim().isEmpty) {
        state = state.copyWith(isLoading: false);
        return;
      }

      await sendMessage(text);

    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }
}

final chatProvider = StateNotifierProvider<ChatNotifier, ChatState>(
  (ref) => ChatNotifier(),
);