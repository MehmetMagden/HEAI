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
  String _userPhoto = '';

  void _showRagSettings(BuildContext context) {
    final chatState = ref.read(chatProvider);
    int tempTopK = chatState.topK;

    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF2C2C2C),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setModalState) {
            return Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'RAG Kaynak Sayısı',
                    style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'AI cevap verirken $tempTopK kaynak kullanacak',
                    style: const TextStyle(color: Colors.white54, fontSize: 13),
                  ),
                  Slider(
                    value: tempTopK.toDouble(),
                    min: 4,
                    max: 20,
                    divisions: 19,
                    label: '$tempTopK kaynak',
                    activeColor: const Color(0xFF1B5E20),
                    onChanged: (val) {
                      setModalState(() => tempTopK = val.toInt());
                    },
                  ),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('4 (hızlı)', style: TextStyle(color: Colors.white38, fontSize: 11)),
                      const Text('30 (kapsamlı)', style: TextStyle(color: Colors.white38, fontSize: 11)),
                    ],
                  ),
                  const SizedBox(height: 16),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      style: ElevatedButton.styleFrom(backgroundColor: const Color(0xFF1B5E20)),
                      onPressed: () {
                        ref.read(chatProvider.notifier).setTopK(tempTopK);
                        Navigator.pop(ctx);
                      },
                      child: const Text('Kaydet', style: TextStyle(color: Colors.white)),
                    ),
                  ),
                ],
              ),
            );
          },
        );
      },
    );
  }





  @override
  void initState() {
    super.initState();
    _loadUserName();
  }

  Future<void> _loadUserName() async {
    final info = await AuthService.getUserInfo();
    setState(() {
      _userName = info['name']?.isNotEmpty == true ? info['name']! : 'Misafir';
      _userPhoto = info['photo'] ?? '';  // ← ekle
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
      resizeToAvoidBottomInset: true,
      backgroundColor: const Color(0xFF1A1A1A),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1B5E20),
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (_userPhoto.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: CircleAvatar(
                  radius: 16,
                  backgroundImage: NetworkImage(_userPhoto),
                ),
              )
            else
              const Padding(
                padding: EdgeInsets.only(right: 8),
                child: CircleAvatar(
                  radius: 16,
                  backgroundColor: Colors.white24,
                  child: Icon(Icons.person, size: 18, color: Colors.white),
                ),
              ),
            Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('HocaefendiAI',
                    style: TextStyle(color: Colors.white, fontSize: 16)),
                Text(_userName,
                    style: const TextStyle(color: Colors.white70, fontSize: 11)),
              ],
            ),
          ],
        ),
        centerTitle: true,
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline, color: Colors.white),
            tooltip: 'Sohbeti temizle',
            onPressed: () {
              ref.read(chatProvider.notifier).clearHistory();
            },
          ),

          IconButton(
            icon: const Icon(Icons.tune, color: Colors.white),
            tooltip: 'RAG Ayarları',
            onPressed: () => _showRagSettings(context),
          ),


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
      body: Stack(
        children: [
          // Ana içerik — tüm ekranı kaplar
          Column(
            children: [
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

          // Küçük duygu resmi — sağ üst köşe
          Positioned(
            top: 8,
            right: 8,
            child: Builder(
              builder: (context) {
                // Ekranın kısa kenarının %12'si, min 50 max 90 piksel
                final size = (MediaQuery.of(context).size.shortestSide * 0.12)
                    .clamp(50.0, 90.0);
                return ClipRRect(
                  borderRadius: BorderRadius.circular(10),
                  child: SizedBox(
                    width: size,
                    height: size,
                    child: EmotionImageWidget(emotion: chatState.currentEmotion),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}