import 'dart:async';
import 'dart:convert';


import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:shared_preferences/shared_preferences.dart';
import '../models/chat_message.dart';
import '../services/api_service.dart';
import 'package:just_audio/just_audio.dart';
import 'package:http/http.dart' as http;
import 'package:flutter/foundation.dart';



class ChatState {
  final List<ChatMessage> messages;
  final bool isLoading;
  final String? error;
  final String currentEmotion;
  final int topK; 

  ChatState({
    required this.messages,
    this.isLoading = false,
    this.error,
    this.currentEmotion = 'tefekkur',
    this.topK = 15,
  });

  ChatState copyWith({
    List<ChatMessage>? messages,
    bool? isLoading,
    String? error,
    String? currentEmotion,
    int? topK,   
  }) {
    return ChatState(
      messages: messages ?? this.messages,
      isLoading: isLoading ?? this.isLoading,
      error: error ?? this.error,
      currentEmotion: currentEmotion ?? this.currentEmotion,
      topK: topK ?? this.topK,
    );
  }
}

class ChatNotifier extends StateNotifier<ChatState> {
  static const _welcomeMessage = 'Esselâmu aleyküm aziz kardeşim. Gönlünüze takılanları benimle paylaşabilirsiniz.';
  static const _maxHistoryForApi = 20; // Servera gönderilecek max mesaj
  // TTS kuyruk sistemi
  final List<String> _audioQueue = [];
  bool _isPlaying = false;
  AudioPlayer? _audioPlayer;
  final String _baseUrl = 'https://aimaden.com'; // ApiService'teki base URL ne ise onu yaz



  
  String _detectEmotion(String text) {
    final lower = text.toLowerCase();
    if (lower.contains('hüzün') || lower.contains('keder') || lower.contains('ağla') || lower.contains('elem')) return 'huzun';
    if (lower.contains('coşku') || lower.contains('sevinç') || lower.contains('neşe') || lower.contains('müjde')) return 'cosku';
    if (lower.contains('şefkat') || lower.contains('merhamet') || lower.contains('sevgi') || lower.contains('muhabbet')) return 'sefkat';
    if (lower.contains('ümit') || lower.contains('umut') || lower.contains('inşallah')) return 'umut';
    return 'tefekkur';
  }


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

  void setTopK(int value) {
    state = state.copyWith(topK: value);
  }


  Future<void> _startStreamingTTS(String text, String sessionId) async {
    try {
      final client = http.Client();
      final request = http.Request(
        'POST',
        Uri.parse('$_baseUrl/voice/synthesize-stream'),
      );
      request.headers['Content-Type'] = 'application/json';
      request.body = jsonEncode({'text': text, 'session_id': sessionId});

      final response = await client.send(request);

      await for (final chunk in response.stream.transform(utf8.decoder)) {
        final lines = chunk.split('\n');
        for (final line in lines) {
          if (!line.startsWith('data: ')) continue;
          final jsonStr = line.substring(6).trim();
          if (jsonStr.isEmpty) continue;

          try {
            final data = jsonDecode(jsonStr) as Map<String, dynamic>;
            if (data['done'] == true) {
              client.close();
              break;
            }
            final audioUrl = data['url'] as String?;
            if (audioUrl != null) {
              _audioQueue.add('$_baseUrl$audioUrl');
              if (!_isPlaying) {
                _playNext();
              }
            }
          } catch (_) {}
        }
      }
      client.close();
    } catch (e) {
      // TTS hatası sessizce geç
    }
  }

  Future<void> _playNext() async {
    if (_audioQueue.isEmpty) {
      _isPlaying = false;
      return;
    }

    _isPlaying = true;
    final url = _audioQueue.removeAt(0);

    try {
      _audioPlayer ??= AudioPlayer();
      await _audioPlayer!.stop();
      await _audioPlayer!.setUrl(url);
      await _audioPlayer!.play();

      // Cümle bitene kadar bekle, sonra sıradakine geç
      await _audioPlayer!.playerStateStream.firstWhere(
        (s) =>
            s.processingState == ProcessingState.completed ||
            s.processingState == ProcessingState.idle,
      );

      await _playNext();
    } catch (e) {
      debugPrint('Ses çalma hatası: $e');
      await _playNext(); // Hata varsa atla
    }
  }

  void _stopTTS() {
    _audioQueue.clear();
    _audioPlayer?.stop();
    _isPlaying = false;
  }











  



  Future<void> sendMessage(String text, {bool isVoice = false}) async {
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
      List<Map<String, String>> sources = [];

      bool collectingSources = false;
      String sourcesBuffer = '';

      await for (final chunk in ApiService.streamMessage(
        message: text,
        history: history,
        topK: state.topK,
      )) {
        String processedChunk = chunk;

        if (collectingSources) {
          // Sources JSON'unu biriktirmeye devam et
          sourcesBuffer += chunk;
          if (sourcesBuffer.contains('[/SOURCES]')) {
            final sourcesEnd = sourcesBuffer.indexOf('[/SOURCES]');
            final sourcesJson = sourcesBuffer.substring(0, sourcesEnd);
            try {
              final decoded = jsonDecode(sourcesJson) as List<dynamic>;
              sources = decoded
                  .map((e) => Map<String, String>.from(e as Map))
                  .toList();
            } catch (_) {}
            processedChunk = sourcesBuffer.substring(sourcesEnd + '[/SOURCES]'.length);
            collectingSources = false;
            sourcesBuffer = '';
            if (processedChunk.isEmpty) continue;
          } else {
            continue; // Henüz tamamlanmadı, biriktirmeye devam
          }
        } else if (chunk.contains('[SOURCES]')) {
          final sourcesStart = chunk.indexOf('[SOURCES]') + '[SOURCES]'.length;
          sourcesBuffer = chunk.substring(sourcesStart);

          if (sourcesBuffer.contains('[/SOURCES]')) {
            // Şanslı durum: tek chunk'ta tamamlandı
            final sourcesEnd = sourcesBuffer.indexOf('[/SOURCES]');
            final sourcesJson = sourcesBuffer.substring(0, sourcesEnd);
            try {
              final decoded = jsonDecode(sourcesJson) as List<dynamic>;
              sources = decoded
                  .map((e) => Map<String, String>.from(e as Map))
                  .toList();
            } catch (_) {}
            processedChunk = sourcesBuffer.substring(sourcesEnd + '[/SOURCES]'.length);
            sourcesBuffer = '';
            if (processedChunk.isEmpty) continue;
          } else {
            // Büyük JSON, birden fazla chunk'a bölündü
            collectingSources = true;
            continue;
          }
        }

        fullText += processedChunk;
        final updatedMessages = [...state.messages];
        updatedMessages[updatedMessages.length - 1] = ChatMessage(
          text: fullText,
          isUserMessage: false,
          timestamp: aiPlaceholder.timestamp,
          sources: sources,
        );
        state = state.copyWith(
          messages: updatedMessages,
          isLoading: false,
        );
      }

      // Duyguyu al
      // final emotionResponse = await ApiService.sendMessage(
      //   message: text,
      //   history: history,
      // );
      // state = state.copyWith(
      //   currentEmotion: emotionResponse['emotion'] as String? ?? state.currentEmotion,
      // );

      // Duyguyu client-side tespit et
      final emotion = _detectEmotion(fullText);
      state = state.copyWith(currentEmotion: emotion);

      // Geçmişi kaydet
      await _saveHistory();

      // TTS - Streaming
      if (isVoice && fullText.isNotEmpty) {
        final sessionId = DateTime.now().millisecondsSinceEpoch.toString();
        _stopTTS(); // Önceki çalmayı durdur
        _startStreamingTTS(fullText, sessionId);
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
      await sendMessage(text, isVoice: true);  // ← isVoice: true eklendi
    } catch (e) {
      state = state.copyWith(
        isLoading: false,
        error: e.toString(),
      );
    }
  }

  @override
  void dispose() {
    _stopTTS();
    _audioPlayer?.dispose();
    super.dispose();
  }  







}

final chatProvider = StateNotifierProvider<ChatNotifier, ChatState>(
  (ref) => ChatNotifier(),
);