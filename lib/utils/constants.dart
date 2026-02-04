/// App-wide constants and configuration
class AppConstants {
  // Audio Configuration
  static const int audioSampleRate = 24000;
  static const int audioChannels = 1;
  
  // Voice Detection
  static const Duration silenceThreshold = Duration(seconds: 2);
  static const Duration silenceCheckInterval = Duration(milliseconds: 500);
  static const double voiceAmplitudeThreshold = -40.0;
  
  // AI Configuration
  static const String defaultVoice = 'Zephyr';
  static const String aiName = 'Lumi';
  static const String aiGreeting = 'Toque no microfone para começar a conversar.';
  
  // UI Timing
  static const Duration animationDuration = Duration(milliseconds: 300);
  static const Duration breathingAnimationDuration = Duration(seconds: 2);
  static const Duration postSpeechDelay = Duration(milliseconds: 1000);
  static const Duration processingCheckDelay = Duration(milliseconds: 100);
  
  // UI Sizes
  static const double avatarRadius = 90.0;
  static const double micButtonSize = 50.0;
  static const double micButtonPadding = 30.0;
  
  // Messages
  static const String listeningMessage = '🎤 Estou ouvindo... Fale naturalmente.';
  static const String processingMessage = '⏳ Processando sua mensagem...';
  static const String continuousModeActive = '🔄 Modo contínuo ativo - Toque para começar';
  static const String manualModeActive = '👆 Toque para falar';
  static const String autoStopHint = '🎤 Ouvindo... Para automaticamente após silêncio';
}

/// System prompts for AI
class SystemPrompts {
  static const String lumiContext = 
    'Você é Lumi, uma assistente de voz amigável e prestativa. '
    'Responda de forma natural, conversacional e concisa (1-3 frases). '
    'Seja direta e útil. Evite repetir perguntas do usuário - apenas responda.';
    
  static const String sttPrompt = 
    'Transcreva o áudio a seguir em português. Responda APENAS com a transcrição exata:';
    
  static const String ttsPrompt = 
    'Fale o seguinte texto em português brasileiro com tom natural e amigável:\n\n';
}

/// Logging configuration
class LoggingConfig {
  // Enable/disable logging by environment
  static const bool enableDebugLogs = true;
  static const bool enableInfoLogs = true;
  static const bool enableWarningLogs = true;
  static const bool enableErrorLogs = true;
  
  // Log formatting
  static const bool showTimestamps = true;
  static const bool showEmojis = true;
  
  // Debug panel
  static const bool showDebugPanelInDebug = true;
  static const bool showDebugPanelInRelease = false;
  
  // Performance thresholds (for warnings)
  static const int slowApiCallMs = 3000;
  static const int slowPipelineMs = 7000;
  
  // Log history
  static const int maxLogHistorySize = 100;
}