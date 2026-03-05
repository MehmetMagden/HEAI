
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/chat_provider.dart';
import '../widgets/chat_bubble.dart';
import '../models/chat_message.dart';

// ConsumerWidget, Riverpod provider'larını dinlemek için kullanılır.
class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final _textController = TextEditingController();
  final _scrollController = ScrollController();

  @override
  void dispose() {
    _textController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _sendMessage() {
    final text = _textController.text.trim();
    if (text.isNotEmpty) {
      // Kullanıcı mesajını provider aracılığıyla state'e ekle
      ref.read(chatProvider.notifier).addMessage(text, MessageSender.user);
      _textController.clear();

      // TODO: Backend'e istek gönderip AI cevabını alacak mantık buraya eklenecek.
      // Şimdilik sahte bir AI cevabı ekleyelim.
      Future.delayed(const Duration(seconds: 1), () {
        ref.read(chatProvider.notifier).addMessage("Bu, yapay zekadan gelen bir yanıttır.", MessageSender.ai);
      });
    }
  }

  void _scrollToBottom() {
    // Yeni mesaj geldiğinde listenin en altına kaydır
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    // chatProvider'ı dinle. Mesaj listesi değiştiğinde bu widget yeniden çizilir.
    final messages = ref.watch(chatProvider);
    
    // Her build işleminde listenin sonuna kaydırmayı tetikle
    ref.listen(chatProvider, (_, __) => _scrollToBottom());

    return Scaffold(
      appBar: AppBar(
        title: const Text('HocaefendiAI'),
        backgroundColor: Colors.blueGrey[800],
        foregroundColor: Colors.white,
      ),
      body: Column(
        children: [
          // Mesaj listesi
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(8.0),
              itemCount: messages.length,
              itemBuilder: (context, index) {
                return ChatBubble(message: messages[index]);
              },
            ),
          ),
          // Metin giriş alanı
          _buildTextInputArea(),
        ],
      ),
    );
  }

  Widget _buildTextInputArea() {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8.0, vertical: 10.0),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        boxShadow: [
          BoxShadow(
            offset: const Offset(0, -1),
            blurRadius: 2,
            color: Colors.black.withOpacity(0.1),
          ),
        ],
      ),
      child: SafeArea(
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: _textController,
                decoration: const InputDecoration.collapsed(
                  hintText: 'Bir mesaj yazın...',
                ),
                onSubmitted: (_) => _sendMessage(),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.send),
              onPressed: _sendMessage,
              color: Theme.of(context).primaryColor,
            ),
          ],
        ),
      ),
    );
  }
}