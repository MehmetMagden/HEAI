
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'screens/chat_screen.dart';

void main() {
  // ProviderScope, tüm widget ağacının provider'lara erişebilmesini sağlar.
  runApp(const ProviderScope(child: HocaefendiAIApp()));
}

class HocaefendiAIApp extends StatelessWidget {
  const HocaefendiAIApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'HocaefendiAI',
      theme: ThemeData(
        primarySwatch: Colors.blueGrey,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      debugShowCheckedModeBanner: false,
      home: const ChatScreen(),
    );
  }
}