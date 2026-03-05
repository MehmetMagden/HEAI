import 'package:flutter/material.dart';
import '../models/chat_message.dart';

class ChatBubble extends StatelessWidget {
  final ChatMessage message;

  const ChatBubble({super.key, required this.message});

  @override
  Widget build(BuildContext context) {
    final isUserMessage = message.sender == MessageSender.user;
    
    return Align(
      // Mesajın kullanıcıya mı yoksa AI'a mı ait olduğuna göre hizalama yap
      alignment: isUserMessage ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.symmetric(vertical: 5, horizontal: 10),
        padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 15),
        decoration: BoxDecoration(
          // Mesajın sahibine göre renk belirle
          color: isUserMessage ? Colors.blue[700] : Colors.grey[600],
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(16),
            topRight: const Radius.circular(16),
            bottomLeft: isUserMessage ? const Radius.circular(16) : Radius.zero,
            bottomRight: isUserMessage ? Radius.zero : const Radius.circular(16),
          ),
        ),
        constraints: BoxConstraints(
          // Mesaj balonunun maksimum genişliğini ekranın %75'i ile sınırla
          maxWidth: MediaQuery.of(context).size.width * 0.75,
        ),
        child: Text(
          message.text,
          style: const TextStyle(color: Colors.white, fontSize: 16),
        ),
      ),
    );
  }
}