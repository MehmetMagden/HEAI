import 'dart:async';
import 'dart:math';
import 'package:flutter/material.dart';

class EmotionImageWidget extends StatefulWidget {
  final String emotion;
  const EmotionImageWidget({super.key, required this.emotion});

  @override
  State<EmotionImageWidget> createState() => _EmotionImageWidgetState();
}

class _EmotionImageWidgetState extends State<EmotionImageWidget> {
  final _random = Random();
  late String _currentImage;
  Timer? _timer;

  static const _emotionImages = {
    'tefekkur': ['tefekkur_1.jpg', 'tefekkur_2.jpg', 'tefekkur_3.jpg', 'tefekkur_4.jpg'],
    'huzun':    ['huzun_1.jpg',    'huzun_2.jpg',    'huzun_3.jpg',    'huzun_4.jpg'],
    'cosku':    ['cosku_1.jpg',    'cosku_2.jpg'],
    'sefkat':   ['sefkat_1.jpg',   'sefkat_2.jpg',   'sefkat_3.jpg',   'sefkat_4.jpg'],
    'huzur':    ['huzur_1.jpg',    'huzur_2.jpg',    'huzur_3.jpg',    'huzur_4.jpg'],
  };

  String _randomImage(String emotion) {
    final images = _emotionImages[emotion] ?? _emotionImages['tefekkur']!;
    return 'assets/emotions/$emotion/${images[_random.nextInt(images.length)]}';
  }

  @override
  void initState() {
    super.initState();
    _currentImage = _randomImage(widget.emotion);
    _startTimer();
  }

  @override
  void didUpdateWidget(EmotionImageWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.emotion != widget.emotion) {
      setState(() => _currentImage = _randomImage(widget.emotion));
    }
  }

  void _startTimer() {
    _timer = Timer.periodic(const Duration(seconds: 4), (_) {
      if (mounted) {
        setState(() => _currentImage = _randomImage(widget.emotion));
      }
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // Ekran yüksekliğinin %20'si — telefonda ~150px, masaüstünde ~180px
    final imageHeight = MediaQuery.of(context).size.height * 0.20;

    return SizedBox(
      height: imageHeight,
      width: double.infinity,
      child: AnimatedSwitcher(
        duration: const Duration(milliseconds: 800),
        child: Image.asset(
          _currentImage,
          key: ValueKey(_currentImage),
          fit: BoxFit.cover,
          errorBuilder: (_, __, ___) => Container(
            color: const Color(0xFF2A2A2A),
            child: const Icon(Icons.image_not_supported,
                color: Colors.white24, size: 40),
          ),
        ),
      ),
    );
  }
}