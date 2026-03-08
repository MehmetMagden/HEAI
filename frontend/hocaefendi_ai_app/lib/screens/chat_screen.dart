import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/chat_provider.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/emotion_image_widget.dart';
import 'package:flutter/services.dart';
import '../widgets/voice_button.dart';
import '../services/auth_service.dart';
import 'auth_screen.dart';

class ChatScreen extends ConsumerStatefulWidget {
  const ChatScreen({super.key});

  @override
  ConsumerState<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends ConsumerState<ChatScreen> {
  final TextEditingController _controller = TextEditingController();
  final ScrollController _scrollController = ScrollController();

  void _sendMessage() {
    final text = _controller.text.trim();
    if (text.isEmpty) return;
    _controller.clear();
    ref.read(chatProvider.notifier).sendMessage(text);
    Future.delayed(const Duration(milliseconds: 300), _scrollToBottom);
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    final chatState = ref.watch(chatProvider);

    return Scaffold(
      backgroundColor: const Color(0xFF1A1A1A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1B5E20),
        title: const Text('HocaefendiAI', style: TextStyle(color: Colors.white)),
        centerTitle: true,
        actions: [
          // const VoiceButton(),
          // const SizedBox(width: 8),

          IconButton( // cikis buttonu
            icon: const Icon(Icons.logout, color: Colors.white),
            tooltip: 'Çıkış yap',
            onPressed: () async {
              await AuthService.signOut();
              if (context.mounted) {
                Navigator.of(context).pushReplacement(
                  MaterialPageRoute(builder: (_) => const AuthScreen()),
                );
              }
            },
          ),

          IconButton(  // kopyala buttonu
            icon: const Icon(Icons.copy, color: Colors.white),
            tooltip: 'Tüm sohbeti kopyala',
            onPressed: () {
              final chatState = ref.read(chatProvider);
              final allText = chatState.messages
                  .map((m) => '${m.isUserMessage ? "Sen" : "Hocaefendi"}: ${m.text}')
                  .join('\n\n');
              Clipboard.setData(ClipboardData(text: allText));
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Sohbet kopyalandı!')),
              );
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Duygu görseli
          const EmotionImageWidget(),

          // Mesaj listesi
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              itemCount: chatState.messages.length,
              itemBuilder: (context, index) {
                return ChatBubble(message: chatState.messages[index]);
              },
            ),
          ),

          // Yükleniyor göstergesi
          if (chatState.isLoading)
            const Padding(
              padding: EdgeInsets.all(8),
              child: CircularProgressIndicator(color: Color(0xFF1B5E20)),
            ),

          // Mesaj giriş alanı
          Container(
            padding: const EdgeInsets.all(8),
            color: const Color(0xFF2C2C2C),
            child: Row(
              children: [
                const VoiceButton(),
                const SizedBox(width: 8),

                Expanded(
                  child: TextField(
                    controller: _controller,
                    style: const TextStyle(color: Colors.white),
                    decoration: InputDecoration(
                      hintText: 'Mesajınızı yazın...',
                      hintStyle: const TextStyle(color: Colors.white54),
                      filled: true,
                      fillColor: const Color(0xFF3C3C3C),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                      contentPadding: const EdgeInsets.symmetric(
                        horizontal: 16, vertical: 10,
                      ),
                    ),
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: chatState.isLoading ? null : _sendMessage,
                  icon: const Icon(Icons.send, color: Color(0xFF1B5E20)),
                  iconSize: 28,
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}