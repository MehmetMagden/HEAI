import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/chat_provider.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/emotion_image_widget.dart';
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
  String _userName = 'Misafir';

  @override
  void initState() {
    super.initState();
    _loadUserName();
  }

  Future<void> _loadUserName() async {
    final info = await AuthService.getUserInfo();
    setState(() {
      _userName = info['name']?.isNotEmpty == true ? info['name']! : 'Misafir';
    });
  }

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
        title: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('HocaefendiAI',
                style: TextStyle(color: Colors.white, fontSize: 18)),
            Text(
              _userName,
              style: const TextStyle(color: Colors.white70, fontSize: 12),
            ),
          ],
        ),
        centerTitle: true,
        actions: [
          IconButton(
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
          IconButton(
            icon: const Icon(Icons.copy, color: Colors.white),
            tooltip: 'Tüm sohbeti kopyala',
            onPressed: () {
              final chatState = ref.read(chatProvider);
              final allText = chatState.messages
                  .map((m) =>
                      '${m.isUserMessage ? "Sen" : "Hocaefendi"}: ${m.text}')
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
          const EmotionImageWidget(),
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              itemCount: chatState.messages.length,
              itemBuilder: (context, index) {
                return ChatBubble(message: chatState.messages[index]);
              },
            ),
          ),
          if (chatState.isLoading)
            const Padding(
              padding: EdgeInsets.all(8),
              child: CircularProgressIndicator(color: Color(0xFF1B5E20)),
            ),
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