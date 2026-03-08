class ChatMessage {
  final String text;
  final bool isUserMessage;
  final DateTime timestamp;

  ChatMessage({
    required this.text,
    required this.isUserMessage,
    required this.timestamp,
  });

  Map<String, dynamic> toJson() => {
    'text': text,
    'isUserMessage': isUserMessage,
    'timestamp': timestamp.toIso8601String(),
  };

  factory ChatMessage.fromJson(Map<String, dynamic> json) => ChatMessage(
    text: json['text'] as String,
    isUserMessage: json['isUserMessage'] as bool,
    timestamp: DateTime.parse(json['timestamp'] as String),
  );
}