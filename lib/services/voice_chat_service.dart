import 'dart:typed_data';
import 'package:google_generative_ai/google_generative_ai.dart';
import 'gemini_config.dart';
import 'gemini_stt_service.dart';
import 'gemini_tts_service.dart';

/// Serviço de conversação por voz com IA
///
/// Integra STT (Speech-to-Text) + LLM + TTS (Text-to-Speech)
/// para criar uma experiência completa de conversação por voz
class VoiceChatService {
  final GeminiSTTService _sttService = GeminiSTTService();
  final GeminiTTSService _ttsService = GeminiTTSService();

  // Histórico de conversação
  final List<Content> _conversationHistory = [];

  // Estado
  bool _isProcessing = false;
  bool _isSpeaking = false;
  String? _lastUserMessage;
  String? _lastAIResponse;

  /// Getter para verificar se está processando
  bool get isProcessing => _isProcessing;

  /// Getter para verificar se está falando
  bool get isSpeaking => _isSpeaking;

  /// Getter para última mensagem do usuário
  String? get lastUserMessage => _lastUserMessage;

  /// Getter para última resposta da IA
  String? get lastAIResponse => _lastAIResponse;

  /// Getter para histórico
  List<Content> get conversationHistory => List.unmodifiable(_conversationHistory);

  /// Processa áudio do usuário e retorna resposta falada
  ///
  /// Fluxo: Áudio → STT → LLM → TTS → Áudio
  Future<String> processVoiceInput(Uint8List audioBytes, {String mimeType = 'audio/wav'}) async {
    if (_isProcessing) {
      throw Exception('Already processing a message');
    }

    _isProcessing = true;

    try {
      // 1. STT: Converter áudio em texto
      print('🎤 Step 1: Transcribing audio...');
      final userText = await _sttService.transcribe(audioBytes, mimeType: mimeType);
      _lastUserMessage = userText;
      print('📝 User said: $userText');

      // 2. LLM: Gerar resposta da IA
      print('🤖 Step 2: Generating AI response...');
      final aiResponse = await _generateAIResponse(userText);
      _lastAIResponse = aiResponse;
      print('💭 AI response: $aiResponse');

      // 3. TTS: Converter resposta em áudio e reproduzir
      print('🔊 Step 3: Speaking response...');
      _isSpeaking = true;

      try {
        await _ttsService.speak(aiResponse, voiceName: 'Zephyr');

        // Aguardar um pouco após terminar de falar
        await Future.delayed(const Duration(milliseconds: 500));
      } finally {
        _isSpeaking = false;
      }

      return aiResponse;

    } catch (e) {
      print('❌ Error in voice chat: $e');
      rethrow;
    } finally {
      _isProcessing = false;
    }
  }

  /// Gera resposta da IA usando Gemini LLM
  Future<String> _generateAIResponse(String userMessage) async {
    if (!GeminiConfig.isInitialized) {
      throw Exception('GeminiConfig not initialized');
    }

    try {
      final model = GeminiConfig.model;

      // Adicionar mensagem do usuário ao histórico
      _conversationHistory.add(Content.text(userMessage));

      // Gerar resposta
      final response = await model.generateContent(_conversationHistory);

      final aiText = response.text ?? 'Desculpe, não consegui gerar uma resposta.';

      // Adicionar resposta da IA ao histórico
      _conversationHistory.add(Content.model([TextPart(aiText)]));

      return aiText;

    } catch (e) {
      print('Error generating AI response: $e');
      return 'Desculpe, ocorreu um erro ao processar sua mensagem.';
    }
  }

  /// Envia mensagem de texto (sem áudio) e recebe resposta falada
  Future<String> sendTextMessage(String message) async {
    if (_isProcessing) {
      throw Exception('Already processing a message');
    }

    _isProcessing = true;

    try {
      _lastUserMessage = message;
      print('📝 User text: $message');

      // Gerar resposta da IA
      print('🤖 Generating AI response...');
      final aiResponse = await _generateAIResponse(message);
      _lastAIResponse = aiResponse;
      print('💭 AI response: $aiResponse');

      // Falar resposta
      print('🔊 Speaking response...');
      _isSpeaking = true;

      try {
        await _ttsService.speak(aiResponse, voiceName: 'Zephyr');

        // Aguardar um pouco após terminar de falar
        await Future.delayed(const Duration(milliseconds: 500));
      } finally {
        _isSpeaking = false;
      }

      return aiResponse;

    } catch (e) {
      print('❌ Error in text chat: $e');
      rethrow;
    } finally {
      _isProcessing = false;
    }
  }

  /// Define o contexto/personalidade da IA
  void setSystemContext(String context) {
    _conversationHistory.clear();

    // Adicionar como system instruction (user + model response para simular)
    _conversationHistory.add(Content.text(context));
    _conversationHistory.add(Content.model([
      TextPart('Entendido! Estou pronta para conversar como Lumi.')
    ]));
  }

  /// Limpa o histórico de conversação
  void clearHistory() {
    _conversationHistory.clear();
    _lastUserMessage = null;
    _lastAIResponse = null;
  }

  /// Para a reprodução de áudio atual
  Future<void> stopSpeaking() async {
    await _ttsService.stop();
  }

  /// Limpa recursos
  void dispose() {
    _ttsService.dispose();
  }
}
