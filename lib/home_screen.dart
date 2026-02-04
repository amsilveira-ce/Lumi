import 'dart:async';
import 'dart:math';
import 'dart:typed_data';
import 'dart:convert';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:waveform_flutter/waveform_flutter.dart' as waveform;
import 'package:record/record.dart';
import 'package:http/http.dart' as http;
import 'services/voice_chat_service.dart';

class CloseByHome extends StatefulWidget {
  const CloseByHome({super.key});

  @override
  State<CloseByHome> createState() => _CloseByHomeState();
}

class _CloseByHomeState extends State<CloseByHome> with TickerProviderStateMixin {
  bool isListening = false;
  bool isProcessing = false;
  bool _continuousMode = true; // Modo conversação contínua (ativado por padrão)

  // Controllers
  AnimationController? _pulseController;

  // Services
  final VoiceChatService _voiceChatService = VoiceChatService();
  final AudioRecorder _audioRecorder = AudioRecorder();

  // Voice Activity Detection
  Timer? _silenceTimer;
  DateTime? _lastSoundDetected;
  static const Duration _silenceThreshold = Duration(seconds: 2); // 2 segundos de silêncio

  // Estado da conversa
  String _userMessage = "";
  String _aiMessage = "Toque no microfone para começar a conversar.";
  bool _userHasInteracted = false;

  @override
  void initState() {
    super.initState();

    // Initialize breathing animation
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
      lowerBound: 0.95,
      upperBound: 1.05,
    )..repeat(reverse: true);

    // Definir contexto da IA
    _voiceChatService.setSystemContext(
      'Você é Lumi, uma assistente de voz amigável e prestativa. '
      'Responda de forma natural, conversacional e concisa (1-3 frases). '
      'Seja direta e útil. Evite repetir perguntas do usuário - apenas responda.'
    );

    // Não falar automaticamente - aguardar interação do usuário
  }

  @override
  void dispose() {
    _pulseController?.dispose();
    _voiceChatService.dispose();
    _audioRecorder.dispose();
    _silenceTimer?.cancel();
    super.dispose();
  }

  /// Toggle listening (um toque liga/desliga)
  Future<void> _toggleListening() async {
    if (isProcessing) return;

    // Marcar que usuário interagiu (para permitir autoplay)
    _userHasInteracted = true;

    if (isListening) {
      // Parar manualmente
      await _stopRecording();
    } else {
      // Iniciar gravação com detecção de silêncio
      await _startRecording();
    }
  }

  /// Inicia gravação de áudio com detecção de silêncio
  Future<void> _startRecording() async {
    try {
      // Verificar permissão
      if (await _audioRecorder.hasPermission()) {
        setState(() {
          isListening = true;
          _userMessage = "🎤 Estou ouvindo... Fale naturalmente.";
        });

        // Iniciar gravação
        await _audioRecorder.start(
          RecordConfig(
            encoder: AudioEncoder.wav,
            sampleRate: 24000,
            numChannels: 1,
          ),
          path: '', // Empty path lets the plugin choose the location
        );

        print('🎤 Recording started with silence detection');

        // Inicializar detecção de silêncio
        _lastSoundDetected = DateTime.now();
        _startSilenceDetection();
      } else {
        _showError('Permissão de microfone negada');
      }
    } catch (e) {
      print('Error starting recording: $e');
      _showError('Erro ao iniciar gravação');
    }
  }

  /// Inicia monitoramento de amplitude para detecção de silêncio
  void _startSilenceDetection() {
    _silenceTimer?.cancel();

    _silenceTimer = Timer.periodic(const Duration(milliseconds: 500), (timer) async {
      if (!isListening) {
        timer.cancel();
        return;
      }

      // Se a IA está falando, pausar detecção
      if (_voiceChatService.isSpeaking) {
        print('🔇 AI is speaking - pausing detection');
        return;
      }

      try {
        // Obter amplitude atual
        final amplitude = await _audioRecorder.getAmplitude();
        final currentAmplitude = amplitude.current;

        // Detectar se há som (threshold de -40 dB é típico para voz)
        final isSpeaking = currentAmplitude > -40.0;

        if (isSpeaking) {
          // Reset timer se detectar fala
          _lastSoundDetected = DateTime.now();

          // Atualizar UI para mostrar que está detectando voz
          if (mounted) {
            setState(() {
              _userMessage = "🎤 Ouvindo... (Detectando voz)";
            });
          }
        } else {
          // Verificar quanto tempo de silêncio
          final silenceDuration = DateTime.now().difference(_lastSoundDetected!);

          if (silenceDuration >= _silenceThreshold) {
            // Silêncio detectado - parar e processar
            print('🔇 Silence detected - stopping recording');
            timer.cancel();
            await _stopRecording();
          } else {
            // Ainda no período de tolerância
            if (mounted) {
              setState(() {
                _userMessage = "🎤 Ouvindo... (${_silenceThreshold.inSeconds - silenceDuration.inSeconds}s)";
              });
            }
          }
        }
      } catch (e) {
        print('Error in silence detection: $e');
      }
    });
  }

  /// Para gravação e processa o áudio
  Future<void> _stopRecording() async {
    try {
      // Cancelar timer de silêncio
      _silenceTimer?.cancel();

      setState(() {
        isListening = false;
        isProcessing = true;
        _userMessage = "⏳ Processando sua mensagem...";
      });

      // Parar gravação e obter dados
      final path = await _audioRecorder.stop();

      if (path != null) {
        print('🎤 Recording stopped: $path');

        // Ler bytes do arquivo de áudio
        final audioBytes = await _readAudioFile(path);

        if (audioBytes != null) {
          // Processar com VoiceChatService (STT + LLM + TTS)
          final aiResponse = await _voiceChatService.processVoiceInput(
            audioBytes,
            mimeType: 'audio/wav',
          );

          // Atualizar UI
          setState(() {
            _userMessage = _voiceChatService.lastUserMessage ?? 'Não foi possível transcrever';
            _aiMessage = aiResponse;
            isProcessing = false;
          });

          // Se em modo contínuo, reiniciar gravação automaticamente
          if (_continuousMode && mounted) {
            // Aguardar a IA terminar de falar completamente
            print('⏳ Waiting for AI to finish speaking...');
            while (_voiceChatService.isSpeaking && mounted) {
              await Future.delayed(const Duration(milliseconds: 100));
            }

            // Aguardar mais um pouco para garantir que o áudio do speaker terminou
            await Future.delayed(const Duration(milliseconds: 1000));

            if (mounted && !isListening && !isProcessing) {
              print('🔄 Continuous mode: restarting listening');
              await _startRecording();
            }
          }
        } else {
          _showError('Erro ao ler arquivo de áudio');
          setState(() => isProcessing = false);
        }
      } else {
        _showError('Gravação cancelada');
        setState(() => isProcessing = false);
      }
    } catch (e) {
      print('Error processing audio: $e');
      _showError('Erro ao processar áudio: $e');
      setState(() {
        isProcessing = false;
        _userMessage = "";
      });
    }
  }

  /// Lê bytes do arquivo de áudio
  Future<Uint8List?> _readAudioFile(String path) async {
    try {
      if (kIsWeb) {
        // Para web, o path pode ser data URL ou blob URL
        if (path.startsWith('data:')) {
          // Extrair base64 da data URL
          final base64Data = path.split(',')[1];
          return base64Decode(base64Data);
        } else if (path.startsWith('blob:')) {
          // Ler blob URL usando http.get
          print('Reading blob URL: $path');
          final response = await http.get(Uri.parse(path));
          if (response.statusCode == 200) {
            print('Blob read successfully: ${response.bodyBytes.length} bytes');
            return response.bodyBytes;
          } else {
            print('Failed to read blob: ${response.statusCode}');
            return null;
          }
        } else {
          print('Unexpected path format on web: $path');
          return null;
        }
      } else {
        // Para mobile/desktop, ler arquivo
        final file = File(path);
        final bytes = await file.readAsBytes();
        return Uint8List.fromList(bytes);
      }
    } catch (e) {
      print('Error reading audio file: $e');
      return null;
    }
  }

  /// Fala uma mensagem usando TTS
  Future<void> _speakMessage(String message) async {
    // Marcar que usuário interagiu
    _userHasInteracted = true;

    // Parar gravação se estiver ativa (para não captar o próprio áudio)
    if (isListening) {
      _silenceTimer?.cancel();
      await _audioRecorder.stop();
      setState(() => isListening = false);
      print('🔇 Stopped recording before speaking');
    }

    try {
      await _voiceChatService.sendTextMessage(message);
    } catch (e) {
      print('Error speaking: $e');
      // Ignorar erros de autoplay se usuário ainda não interagiu
      if (!e.toString().contains('play()') || _userHasInteracted) {
        _showError('Erro ao falar: $e');
      }
    }
  }

  /// Mostra erro para o usuário
  void _showError(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: Colors.red,
          duration: const Duration(seconds: 2),
        ),
      );
    }
  }

  /// Mostra informação para o usuário
  void _showInfo(String message) {
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(message),
          backgroundColor: Colors.blueAccent,
          duration: const Duration(seconds: 2),
        ),
      );
    }
  }

  // Helper to create a stream of amplitude data for the waveform
  Stream<waveform.Amplitude> _createAmplitudeStream() {
    return Stream.periodic(
      const Duration(milliseconds: 100),
      (_) => waveform.Amplitude(
        current: isListening ? (Random().nextDouble() * 80 + 20) : 10,
        max: 100,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(
        children: [
          // Background
          _buildBlurredBackground(),

          SafeArea(
            child: Column(
              children: [
                // Header
                _buildHeader(),

                // Main Content
                Expanded(
                  child: Center(
                    child: SingleChildScrollView(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          _buildPresenceAvatar(),
                          const SizedBox(height: 32),

                          // Conversation Area
                          _buildConversationArea(),

                          const SizedBox(height: 32),

                          // Waveform
                          SizedBox(
                            height: 60,
                            width: 200,
                            child: AnimatedOpacity(
                              opacity: isListening ? 1.0 : 0.3,
                              duration: const Duration(milliseconds: 500),
                              child: waveform.AnimatedWaveList(
                                stream: _createAmplitudeStream(),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),

                _buildControlFooter(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  // --- UI Component Builders ---

  Widget _buildPresenceAvatar() {
    final animation = _pulseController ?? const AlwaysStoppedAnimation(1.0);

    return ScaleTransition(
      scale: animation,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 300),
        decoration: BoxDecoration(
          shape: BoxShape.circle,
          border: isListening
            ? Border.all(color: Colors.blueAccent.withOpacity(0.5), width: 4)
            : Border.all(color: Colors.transparent, width: 4),
          boxShadow: [
            BoxShadow(
              color: isListening
                ? Colors.blueAccent.withOpacity(0.4)
                : Colors.blueAccent.withOpacity(0.1),
              blurRadius: isListening ? 60 : 30,
              spreadRadius: isListening ? 15 : 5,
            )
          ],
        ),
        child: CircleAvatar(
          radius: 90,
          backgroundColor: Colors.white10,
          child: Icon(
            Icons.assistant,
            size: 80,
            color: Colors.white.withOpacity(0.9),
          ),
        ),
      ),
    );
  }

  Widget _buildConversationArea() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40),
      child: Column(
        children: [
          // User message
          if (_userMessage.isNotEmpty) ...[
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white10,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Row(
                children: [
                  const Icon(Icons.person, color: Colors.white70, size: 20),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      _userMessage,
                      style: const TextStyle(
                        color: Colors.white70,
                        fontSize: 16,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],

          // AI message
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.blueAccent.withOpacity(0.2),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: Colors.blueAccent.withOpacity(0.3)),
            ),
            child: Row(
              children: [
                const Icon(Icons.assistant, color: Colors.blueAccent, size: 20),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    _aiMessage,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 18,
                      height: 1.4,
                    ),
                  ),
                ),
                if (!isProcessing)
                  IconButton(
                    icon: const Icon(Icons.volume_up_outlined, color: Colors.blueAccent),
                    onPressed: () => _speakMessage(_aiMessage),
                  ),
              ],
            ),
          ),

          // Processing indicator
          if (isProcessing) ...[
            const SizedBox(height: 16),
            const CircularProgressIndicator(
              valueColor: AlwaysStoppedAnimation<Color>(Colors.blueAccent),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          // App Title
          const Row(
            children: [
              Icon(Icons.auto_awesome, color: Colors.blueAccent, size: 24),
              SizedBox(width: 8),
              Text(
                "Lumi Assistant",
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),

          // Clear conversation button
          IconButton(
            icon: const Icon(Icons.refresh, color: Colors.white60),
            onPressed: () {
              _voiceChatService.clearHistory();
              setState(() {
                _userMessage = "";
                _aiMessage = "Conversa reiniciada. Como posso ajudar?";
              });
              if (_userHasInteracted) {
                _speakMessage(_aiMessage);
              }
            },
          ),
        ],
      ),
    );
  }

  Widget _buildControlFooter() {
    return Padding(
      padding: const EdgeInsets.only(bottom: 40),
      child: Column(
        children: [
          // Botão Principal - Um toque para ligar/desligar
          GestureDetector(
            onTap: isProcessing ? null : _toggleListening,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              padding: const EdgeInsets.all(30),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isListening
                  ? Colors.red
                  : isProcessing
                    ? Colors.orange
                    : Colors.blueAccent,
                boxShadow: isListening ? [
                   BoxShadow(
                     color: Colors.red.withOpacity(0.5),
                     blurRadius: 30,
                     spreadRadius: 5,
                   )
                ] : [],
              ),
              child: Icon(
                isListening
                  ? Icons.graphic_eq
                  : isProcessing
                    ? Icons.hourglass_empty
                    : Icons.mic,
                color: Colors.white,
                size: 50,
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            isListening
              ? "🎤 Ouvindo... Para automaticamente após silêncio"
              : isProcessing
                ? "⏳ Processando sua mensagem..."
                : _continuousMode
                  ? "🔄 Modo contínuo ativo - Toque para começar"
                  : "👆 Toque para falar",
            textAlign: TextAlign.center,
            style: TextStyle(
              color: isListening ? Colors.white : Colors.white70,
              fontWeight: FontWeight.w600,
              letterSpacing: 1.2,
              fontSize: 16,
            ),
          ),

          // Toggle para modo contínuo
          const SizedBox(height: 20),
          GestureDetector(
            onTap: () {
              setState(() {
                _continuousMode = !_continuousMode;
              });

              if (_continuousMode) {
                _showInfo('Modo contínuo ativado - Conversação fluida! 🔄');
              } else {
                _showInfo('Modo contínuo desativado');
              }
            },
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              decoration: BoxDecoration(
                color: _continuousMode ? Colors.blueAccent.withOpacity(0.3) : Colors.white10,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(
                  color: _continuousMode ? Colors.blueAccent : Colors.white30,
                ),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    _continuousMode ? Icons.all_inclusive : Icons.chat_bubble_outline,
                    color: Colors.white70,
                    size: 18,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    _continuousMode ? "Conversação Contínua" : "Modo Manual",
                    style: const TextStyle(
                      color: Colors.white70,
                      fontSize: 14,
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBlurredBackground() {
    return Container(
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            Colors.black,
            Colors.blue.shade900.withOpacity(0.3),
            Colors.black,
          ],
        ),
      ),
    );
  }
}
