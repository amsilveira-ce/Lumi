import 'dart:typed_data';
import 'package:google_generative_ai/google_generative_ai.dart';
import 'gemini_config.dart';
import 'gemini_stt_service.dart';
import 'gemini_tts_service.dart';
import '../utils/constants.dart';
import '../utils/logger.dart';

/// Voice conversation service integrating STT + LLM + TTS
///
/// This service orchestrates the complete voice interaction pipeline:
/// 1. Speech-to-Text (STT) - Convert audio to text
/// 2. LLM Processing - Generate AI response
/// 3. Text-to-Speech (TTS) - Convert response to audio
///
/// Maintains conversation history for context-aware responses.
class VoiceChatService {
  // === Logger ===
  final _logger = ServiceLogger('VoiceChat');

  // === Services ===
  final GeminiSTTService _sttService = GeminiSTTService();
  final GeminiTTSService _ttsService = GeminiTTSService();

  // === State ===
  final List<Content> _conversationHistory = [];
  bool _isProcessing = false;
  bool _isSpeaking = false;
  String? _lastUserMessage;
  String? _lastAIResponse;

  // === Getters ===
  bool get isProcessing => _isProcessing;
  bool get isSpeaking => _isSpeaking;
  String? get lastUserMessage => _lastUserMessage;
  String? get lastAIResponse => _lastAIResponse;
  List<Content> get conversationHistory => List.unmodifiable(_conversationHistory);

  /// Process voice input through complete pipeline
  ///
  /// Flow: Audio bytes → STT → LLM → TTS → Audio playback
  ///
  /// [audioBytes] - Raw audio data from microphone
  /// [mimeType] - Audio format (default: 'audio/wav')
  ///
  /// Returns: AI response text
  /// Throws: Exception if any step fails
  Future<String> processVoiceInput(
    Uint8List audioBytes, {
    String mimeType = 'audio/wav',
  }) async {
    if (_isProcessing) {
      _logger.warning('Already processing a message - ignoring new request');
      throw Exception('Already processing a message');
    }

    LogUtils.logVoiceFlowStart('Voice Input Processing');
    final timer = PerformanceTimer('Full Voice Pipeline', logger: _logger);

    _isProcessing = true;
    LogUtils.logStateChange('idle', 'processing', tag: 'VoiceChat');

    try {
      // Log audio input details
      LogUtils.logAudioInfo(
        bytes: audioBytes.length,
        format: mimeType,
      );

      // Step 1: Speech-to-Text
      final userText = await _transcribeAudio(audioBytes, mimeType);
      
      if (userText.isEmpty) {
        _logger.warning('Empty transcription received');
        throw Exception('No speech detected in audio');
      }

      // Step 2: Generate AI Response
      final aiResponse = await _generateAIResponse(userText);

      // Step 3: Text-to-Speech
      await _speakResponse(aiResponse);

      timer.stop();
      _logger.success('Voice interaction completed successfully');
      
      return aiResponse;

    } catch (e, stackTrace) {
      timer.stop();
      _logger.error(
        'Voice pipeline failed',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    } finally {
      _isProcessing = false;
      LogUtils.logStateChange('processing', 'idle', tag: 'VoiceChat');
    }
  }

  /// Send text message (skip STT, still use TTS for response)
  ///
  /// Useful for:
  /// - Manual text input
  /// - Replaying AI responses
  /// - Testing without microphone
  Future<String> sendTextMessage(String message) async {
    if (_isProcessing) {
      _logger.warning('Already processing - cannot send text message');
      throw Exception('Already processing a message');
    }

    LogUtils.logVoiceFlowStart('Text Message Processing');
    LogUtils.logUserAction('Sent text: "$message"');
    
    final timer = PerformanceTimer('Text Message Pipeline', logger: _logger);

    _isProcessing = true;

    try {
      _lastUserMessage = message;

      final aiResponse = await _generateAIResponse(message);
      await _speakResponse(aiResponse);

      timer.stop();
      _logger.success('Text message processed successfully');

      return aiResponse;

    } catch (e, stackTrace) {
      timer.stop();
      _logger.error(
        'Text message pipeline failed',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    } finally {
      _isProcessing = false;
    }
  }

  // ============================================================================
  // PRIVATE METHODS - Pipeline Steps
  // ============================================================================

  /// Step 1: Convert audio to text using Gemini STT
  Future<String> _transcribeAudio(Uint8List audioBytes, String mimeType) async {
    _logger.info('━━━ Step 1/3: Speech-to-Text ━━━');
    
    final timer = PerformanceTimer('STT Transcription', logger: _logger);

    try {
      final userText = await _sttService.transcribe(audioBytes, mimeType: mimeType);
      
      _lastUserMessage = userText;
      timer.stop();
      
      _logger.success('Transcribed: "$userText"');
      
      return userText;

    } catch (e, stackTrace) {
      timer.stop();
      _logger.error(
        'STT transcription failed',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// Step 2: Generate AI response using Gemini LLM
  Future<String> _generateAIResponse(String userMessage) async {
    _logger.info('━━━ Step 2/3: LLM Response Generation ━━━');
    
    if (!GeminiConfig.isInitialized) {
      _logger.error('GeminiConfig not initialized');
      throw Exception('GeminiConfig not initialized');
    }

    final timer = PerformanceTimer('LLM Generation', logger: _logger);

    try {
      final model = GeminiConfig.model;

      // Add user message to history
      _conversationHistory.add(Content.text(userMessage));
      _logger.debug('Conversation history size: ${_conversationHistory.length} messages');

      // Generate response with conversation context
      _logger.debug('Calling Gemini LLM...');
      final response = await model.generateContent(_conversationHistory);

      final aiText = response.text ?? _getDefaultErrorResponse();

      // Add AI response to history
      _conversationHistory.add(Content.model([TextPart(aiText)]));

      _lastAIResponse = aiText;
      timer.stop();
      
      _logger.success('AI Response: "$aiText"');

      return aiText;

    } catch (e, stackTrace) {
      timer.stop();
      _logger.error(
        'LLM generation failed',
        error: e,
        stackTrace: stackTrace,
      );
      
      // Return friendly error message to user
      final errorResponse = _getDefaultErrorResponse();
      _lastAIResponse = errorResponse;
      return errorResponse;
    }
  }

  /// Step 3: Convert text to speech and play
  Future<void> _speakResponse(String text) async {
    _logger.info('━━━ Step 3/3: Text-to-Speech ━━━');
    
    final timer = PerformanceTimer('TTS Playback', logger: _logger);

    _isSpeaking = true;
    LogUtils.logStateChange('not speaking', 'speaking', tag: 'VoiceChat');

    try {
      _logger.debug('Speaking: "$text"');
      await _ttsService.speak(text, voiceName: AppConstants.defaultVoice);

      // Small delay after speaking to ensure audio completes
      await Future.delayed(const Duration(milliseconds: 500));

      timer.stop();
      _logger.success('TTS playback completed');

    } catch (e, stackTrace) {
      timer.stop();
      _logger.error(
        'TTS playback failed',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    } finally {
      _isSpeaking = false;
      LogUtils.logStateChange('speaking', 'not speaking', tag: 'VoiceChat');
    }
  }

  // ============================================================================
  // CONFIGURATION & MANAGEMENT
  // ============================================================================

  /// Set AI personality and behavior
  ///
  /// This sets the system context that guides the AI's responses.
  /// Should be called once during initialization.
  void setSystemContext(String context) {
    _logger.info('Setting system context');
    
    _conversationHistory.clear();

    // Simulate system instruction using user + model pair
    _conversationHistory.add(Content.text(context));
    _conversationHistory.add(Content.model([
      TextPart('Entendido! Estou pronta para conversar como ${AppConstants.aiName}.')
    ]));

    _logger.success('System context configured');
    _logger.debug('Context: "$context"');
  }

  /// Clear conversation history
  ///
  /// Useful for:
  /// - Starting fresh conversation
  /// - Clearing context after error
  /// - Reset button functionality
  void clearHistory() {
    final previousCount = _conversationHistory.length;
    
    _conversationHistory.clear();
    _lastUserMessage = null;
    _lastAIResponse = null;
    
    _logger.info('Conversation history cleared ($previousCount messages removed)');
  }

  /// Stop current audio playback
  Future<void> stopSpeaking() async {
    if (_isSpeaking) {
      _logger.info('Stopping current speech playback');
      await _ttsService.stop();
      _isSpeaking = false;
      LogUtils.logStateChange('speaking', 'stopped', tag: 'VoiceChat');
    }
  }

  /// Get conversation summary for debugging
  String getConversationSummary() {
    final userMessages = _conversationHistory
        .where((c) => c.role == 'user')
        .length;
    final modelMessages = _conversationHistory
        .where((c) => c.role == 'model')
        .length;

    return 'Messages: $userMessages user, $modelMessages AI';
  }

  /// Log current state for debugging
  void logDebugState() {
    _logger.debug('═══ VoiceChat State ═══');
    _logger.debug('Processing: $_isProcessing');
    _logger.debug('Speaking: $_isSpeaking');
    _logger.debug('Conversation: ${getConversationSummary()}');
    _logger.debug('Last User: "$_lastUserMessage"');
    _logger.debug('Last AI: "$_lastAIResponse"');
  }

  // ============================================================================
  // HELPERS
  // ============================================================================

  String _getDefaultErrorResponse() {
    return 'Desculpe, ocorreu um erro ao processar sua mensagem.';
  }

  /// Clean up resources
  void dispose() {
    _logger.info('Disposing VoiceChatService');
    
    _ttsService.dispose();
    _conversationHistory.clear();
    
    _logger.success('VoiceChatService disposed');
  }
}