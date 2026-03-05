
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../models/chat_message.dart';

// 1. StateNotifier Sınıfı: Mesaj listesini tutan ve güncelleyen mantık.
class ChatNotifier extends StateNotifier<List<ChatMessage>> {
  ChatNotifier() : super([]); // Başlangıçta boş bir liste ile başlar.

  void addMessage(String text, MessageSender sender) {
    final newMessage = ChatMessage(
      text: text,
      sender: sender,
      timestamp: DateTime.now(),
    );
    // state, StateNotifier'ın mevcut durumunu (mesaj listesi) temsil eder.
    // Yeni bir liste oluşturarak durumu güncelliyoruz, bu da UI'ın yeniden çizilmesini tetikler.
    state = [...state, newMessage];
  }
}

// 2. StateNotifierProvider: UI'ın ChatNotifier'a erişmesini sağlayan provider.
final chatProvider = StateNotifierProvider<ChatNotifier, List<ChatMessage>>((ref) {
  return ChatNotifier();
});