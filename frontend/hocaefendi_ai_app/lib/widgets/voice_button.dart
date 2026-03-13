import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:record/record.dart';
import 'package:http/http.dart' as http;
import '../providers/chat_provider.dart';

class VoiceButton extends ConsumerStatefulWidget {
  const VoiceButton({super.key});

  @override
  ConsumerState<VoiceButton> createState() => _VoiceButtonState();
}

class _VoiceButtonState extends ConsumerState<VoiceButton> {
  final AudioRecorder _recorder = AudioRecorder();
  bool _isRecording = false;

  @override
  void dispose() {
    _recorder.dispose();
    super.dispose();
  }

  Future<void> _startRecording() async {
    // record paketi web'de tarayıcı iznini otomatik ister
    final hasPermission = await _recorder.hasPermission();
    if (!hasPermission) {
      debugPrint('Mikrofon izni reddedildi');
      return;
    }

    try {
      await _recorder.start(
        const RecordConfig(
          encoder: AudioEncoder.wav,
          sampleRate: 16000,
          numChannels: 1,
        ),
        path: '', // Web'de path yok sayılır
      );
      setState(() => _isRecording = true);
    } catch (e) {
      debugPrint('Kayıt başlatma hatası: $e');
    }
  }

  Future<void> _stopRecording() async {
    try {
      final blobUrl = await _recorder.stop();
      setState(() => _isRecording = false);

      if (blobUrl == null || blobUrl.isEmpty) {
        debugPrint('Blob URL boş');
        return;
      }

      debugPrint('Blob URL: $blobUrl');

      // Web'de blob URL'i fetch ederek byte'lara çevir
      final response = await http.get(Uri.parse(blobUrl));
      if (response.statusCode == 200) {
        final audioBytes = response.bodyBytes;
        debugPrint('Ses boyutu: ${audioBytes.length} byte');
        await ref.read(chatProvider.notifier).sendVoiceMessage(audioBytes);
      } else {
        debugPrint('Blob fetch hatası: ${response.statusCode}');
      }
    } catch (e) {
      debugPrint('Kayıt durdurma hatası: $e');
      setState(() => _isRecording = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final isLoading = ref.watch(chatProvider.select((s) => s.isLoading));

    return GestureDetector(
      onLongPressStart: isLoading ? null : (_) => _startRecording(),
      onLongPressEnd: isLoading ? null : (_) => _stopRecording(),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 200),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: isLoading
              ? Colors.grey
              : _isRecording
                  ? Colors.red
                  : const Color(0xFF1B5E20),
          shape: BoxShape.circle,
        ),
        child: Icon(
          isLoading
              ? Icons.hourglass_empty
              : (_isRecording ? Icons.stop : Icons.mic),
          color: Colors.white,
          size: 28,
        ),
      ),
    );
  }
}