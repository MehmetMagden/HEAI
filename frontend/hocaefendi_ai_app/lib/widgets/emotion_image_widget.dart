import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../providers/chat_provider.dart';


class EmotionImageWidget extends ConsumerStatefulWidget {
  const EmotionImageWidget({super.key});

  @override
  ConsumerState<EmotionImageWidget> createState() => _EmotionImageWidgetState();
}

class _EmotionImageWidgetState extends ConsumerState<EmotionImageWidget> {
  final Map<String, List<String>> _emotionImages = {
    'huzur':    ['huzur_1.jpg', 'huzur_2.jpg', 'huzur_3.jpg', 'huzur_4.jpg'],
    'huzun':    ['huzun_1.jpg', 'huzun_2.jpg', 'huzun_3.jpg', 'huzun_4.jpg'],
    'cosku':    ['cosku_1.jpg', 'cosku_2.jpg', 'cosku_3.jpg', 'cosku_4.jpg'],
    'sefkat':   ['sefkat_1.jpg', 'sefkat_2.jpg', 'sefkat_3.jpg', 'sefkat_4.jpg'],
    'tefekkur': ['tefekkur_1.jpg', 'tefekkur_2.jpg', 'tefekkur_3.jpg', 'tefekkur_4.jpg'],
  };

  String _currentEmotion = 'tefekkur';
  String _currentImage = 'assets/emotions/tefekkur/tefekkur_1.jpg';
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    _startTimer();
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 4), (_) {
      _pickRandomImage(_currentEmotion);
    });
  }

  void _pickRandomImage(String emotion) {
    final images = _emotionImages[emotion] ?? _emotionImages['tefekkur']!;
    final random = Random().nextInt(images.length);
    setState(() {
      _currentImage = 'assets/emotions/$emotion/${images[random]}';
    });
  }

  @override
  Widget build(BuildContext context) {
    final emotion = ref.watch(
      chatProvider.select((state) => state.currentEmotion),
    );

    // Duygu değişince hemen yeni resim göster
    if (emotion != _currentEmotion) {
      _currentEmotion = emotion;
      Future.microtask(() => _pickRandomImage(emotion));
    }

    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 800),
      transitionBuilder: (child, animation) {
        return FadeTransition(
          opacity: animation,
          child: child,
        );
      },
      child: Image.asset(
        _currentImage,
        key: ValueKey(_currentImage),
        height: 500,
        width: double.infinity,
        fit: BoxFit.contain,
        errorBuilder: (_, __, ___) => Container(
          height: 500,
          color: Colors.grey[800],
          child: const Icon(Icons.image, color: Colors.white54, size: 60),
        ),
      ),
    );
  }
}