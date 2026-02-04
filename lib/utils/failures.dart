sealed class VoiceChatFailure {
  final String message;
  final String? debugInfo;

  const VoiceChatFailure({
    required this.message,
    this.debugInfo,
  });

  @override
  String toString() => '$runtimeType: $message';
}


/// API configuration failure
class ConfigurationFailure extends VoiceChatFailure {
  const ConfigurationFailure({
    required super.message,
    super.debugInfo,
  });
}