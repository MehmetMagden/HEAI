import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:audioplayers/audioplayers.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
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
  static const _welcomeMessage = 'Esselâmu aleyküm aziz kardeşim. Gönlünüze takılanları benimle paylaşabilirsiniz.';
  static const _maxHistoryForApi = 20; // Servera gönderilecek max mesaj

  ChatNotifier() : super(ChatState(messages: [])) {
    _loadHistory();
  }

  // Geçmişi yükle
  Future<void> _loadHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final userEmail = prefs.getString('user_email') ?? 'guest';

    // Guest ise geçmiş yükleme, sadece karşılama mesajı göster
    if (userEmail == 'guest') {
      state = state.copyWith(messages: [_welcomeMsg()]);
      return;
    }

    final key = 'chat_history_$userEmail';
    final jsonStr = prefs.getString(key);

    if (jsonStr == null) {
      state = state.copyWith(messages: [_welcomeMsg()]);
      return;
    }

    try {
      final List<dynamic> jsonList = jsonDecode(jsonStr);
      final messages = jsonList
          .map((e) => ChatMessage.fromJson(e as Map<String, dynamic>))
          .toList();
      state = state.copyWith(
        messages: messages.isEmpty ? [_welcomeMsg()] : messages,
      );
    } catch (_) {
      state = state.copyWith(messages: [_welcomeMsg()]);
    }
  }

  // Geçmişi kaydet
  Future<void> _saveHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final userEmail = prefs.getString('user_email') ?? 'guest';

    // Guest ise kaydetme
    if (userEmail == 'guest') return;

    final key = 'chat_history_$userEmail';
    final jsonStr = jsonEncode(
      state.messages.map((m) => m.toJson()).toList(),
    );
    await prefs.setString(key, jsonStr);
  }

  ChatMessage _welcomeMsg() => ChatMessage(
    text: _welcomeMessage,
    isUserMessage: false,
    timestamp: DateTime.now(),
  );

  // Geçmişi temizle
  Future<void> clearHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final userEmail = prefs.getString('user_email') ?? 'guest';
    await prefs.remove('chat_history_$userEmail');
    state = state.copyWith(messages: [_welcomeMsg()]);
  }

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
      // Son 20 mesajı al (API için)
      final allMessages = state.messages.where((m) => m.text.isNotEmpty).toList();
      final recentMessages = allMessages.length > _maxHistoryForApi
          ? allMessages.sublist(allMessages.length - _maxHistoryForApi)
          : allMessages;

      final history = recentMessages
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

      // Geçmişi kaydet
      await _saveHistory();

      // TTS
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