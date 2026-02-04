import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:audioplayers/audioplayers.dart';
import 'gemini_config.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import '../utils/logger.dart';

// Import condicional para dart:io (não disponível na web)
import 'dart:io' if (dart.library.html) 'dart:io';
import 'package:path_provider/path_provider.dart';

/// Serviço de Text-to-Speech usando Gemini 2.5 Flash TTS
///
/// Baseado na documentação oficial do Google:
/// https://ai.google.dev/gemini-api/docs/audio
class GeminiTTSService {
  final _logger = ServiceLogger('TTS');
  final AudioPlayer _audioPlayer = AudioPlayer();
  bool _isPlaying = false;

  /// Vozes disponíveis no Gemini TTS
  static const String _defaultVoice = 'Zephyr';

  static const List<String> availableVoices = [
    'Puck',     // Voz natural e amigável
    'Charon',   // Voz mais profunda
    'Kore',     // Voz feminina suave
    'Fenrir',   // Voz masculina forte
    'Aoede',    // Voz melodiosa
    'Zephyr',   // Voz suave e calorosa
  ];

  /// Check if TTS is currently playing
  bool get isPlaying => _isPlaying;

  /// Convert text to speech using Gemini 2.5 Flash TTS
  Future<void> speak(String text, {String? voiceName}) async {
    if (!GeminiConfig.isInitialized) {
      _logger.error('GeminiConfig not initialized');
      throw Exception('GeminiConfig not initialized');
    }

    _logger.info('Starting TTS synthesis');
    _logger.debug('Text to speak: "$text"');
    
    final timer = PerformanceTimer('TTS Full Pipeline', logger: _logger);

    try {
      // Stop any currently playing audio
      await stop();

      final voice = voiceName ?? _defaultVoice;
      _logger.debug('Using voice: $voice');

      // Generate audio from API
      final audioData = await _generateSpeech(text, voice);
      
      // Play the audio
      await _playAudio(audioData);

      timer.stop();
      _logger.success('TTS playback completed successfully');

    } catch (e, stackTrace) {
      timer.stop();
      _logger.error(
        'TTS synthesis/playback failed',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// Generate speech audio from text
  Future<Uint8List> _generateSpeech(String text, String voice) async {
    _logger.info('Generating speech audio from API');
    
    final apiTimer = PerformanceTimer('TTS API Call', logger: _logger);

    try {
      final apiKey = GeminiConfig.apiKey;
      final modelName = 'gemini-2.5-flash-preview-tts';

      // Usar o modelo correto
      final url = Uri.parse(
        'https://generativelanguage.googleapis.com/v1beta/models/$modelName:generateContent?key=$apiKey'
      );

      // Construir requisição seguindo o formato oficial
      final requestBody = _buildRequestBody(text, voice);

      LogUtils.logApiCall(
        'generateContent (TTS)',
        params: {
          'model': modelName,
          'voice': voice,
          'textLength': text.length,
        },
      );

      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
        },
        body: requestBody,
      );

      LogUtils.logApiResponse(
        'generateContent (TTS)',
        response.statusCode,
        bytes: response.bodyBytes.length,
      );

      if (response.statusCode == 200) {
        final wavData = _parseAudioResponse(response.body);
        apiTimer.stop();
        
        LogUtils.logAudioInfo(
          bytes: wavData.length,
          format: 'WAV',
        );
        
        return wavData;

      } else {
        apiTimer.stop();
        _handleErrorResponse(response);
        throw Exception('TTS generation failed');
      }

    } catch (e, stackTrace) {
      apiTimer.stop();
      _logger.error(
        'TTS API call failed',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// Build TTS API request body
  String _buildRequestBody(String text, String voice) {
    _logger.debug('Building TTS request body...');
    
    return jsonEncode({
      'contents': [
        {
          'role': 'user',
          'parts': [
            {'text': 'Fale o seguinte texto em português brasileiro com tom natural e amigável:\n\n$text'}
          ]
        }
      ],
      'generationConfig': {
        'temperature': 1.0,
        'responseModalities': ['audio'],
        'speechConfig': {
          'voiceConfig': {
            'prebuiltVoiceConfig': {
              'voiceName': voice,
            }
          }
        }
      }
    });
  }

  /// Parse audio from API response
  Uint8List _parseAudioResponse(String responseBody) {
    _logger.debug('Parsing TTS audio response...');
    
    final parseTimer = PerformanceTimer('Parse Audio Response', logger: _logger);

    try {
      final responseData = jsonDecode(responseBody);

      // Extract audio data from response
      final candidates = responseData['candidates'] as List?;
      if (candidates == null || candidates.isEmpty) {
        _logger.warning('No candidates in TTS response');
        throw Exception('No candidates in response');
      }

      final parts = candidates[0]['content']['parts'] as List?;
      if (parts == null || parts.isEmpty) {
        _logger.warning('No parts in TTS response');
        throw Exception('No parts in response');
      }

      String? audioBase64;
      String? mimeType;

      // Procurar dados de áudio inline
      for (var part in parts) {
        if (part['inlineData'] != null) {
          final inlineData = part['inlineData'];
          final mime = inlineData['mimeType'] as String?;

          if (mime != null && mime.contains('audio')) {
            audioBase64 = inlineData['data'];
            mimeType = mime;
            _logger.debug('Found audio data: $mimeType');
            break;
          }
        }
      }

      if (audioBase64 == null) {
        _logger.error('No audio data found in response');
        _logger.debug('Response structure: ${jsonEncode(responseData)}');
        throw Exception('No audio data in response');
      }

      // Decode base64 audio (PCM raw)
      final pcmData = base64Decode(audioBase64);
      _logger.debug('PCM decoded: ${pcmData.length} bytes');

      // Converter PCM para WAV
      final wavData = _convertPcmToWav(pcmData, mimeType ?? 'audio/L16;rate=24000');
      _logger.debug('Converted to WAV: ${wavData.length} bytes');

      parseTimer.stop();
      return wavData;

    } catch (e, stackTrace) {
      parseTimer.stop();
      _logger.error(
        'Failed to parse TTS audio response',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// Play audio data
  Future<void> _playAudio(Uint8List wavData) async {
    _logger.info('Starting audio playback');
    
    final playTimer = PerformanceTimer('Audio Playback', logger: _logger);

    _isPlaying = true;
    LogUtils.logStateChange('not playing', 'playing', tag: 'TTS');

    try {
      if (kIsWeb) {
        await _playAudioWeb(wavData);
      } else {
        await _playAudioNative(wavData);
      }

      playTimer.stop();

    } catch (e, stackTrace) {
      playTimer.stop();
      _logger.error(
        'Audio playback failed',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// Play audio on web platform
  Future<void> _playAudioWeb(Uint8List wavData) async {
    _logger.debug('Using web audio playback (data URL)');
    
    final base64Audio = base64Encode(wavData);
    final dataUrl = 'data:audio/wav;base64,$base64Audio';

    await _audioPlayer.play(UrlSource(dataUrl));

    // Listen for completion
    _audioPlayer.onPlayerComplete.listen((_) {
      _isPlaying = false;
      LogUtils.logStateChange('playing', 'complete', tag: 'TTS');
      _logger.debug('Web audio playback completed');
    });
  }

  /// Play audio on native platforms (iOS, Android, Desktop)
  Future<void> _playAudioNative(Uint8List wavData) async {
    _logger.debug('Using native audio playback (temp file)');
    
    try {
      final tempDir = await getTemporaryDirectory();
      final tempFile = File(
        '${tempDir.path}/gemini_tts_${DateTime.now().millisecondsSinceEpoch}.wav'
      );
      
      await tempFile.writeAsBytes(wavData);
      _logger.debug('Audio saved to: ${tempFile.path}');

      await _audioPlayer.play(DeviceFileSource(tempFile.path));

      // Listen for completion and cleanup
      _audioPlayer.onPlayerComplete.listen((_) {
        _isPlaying = false;
        LogUtils.logStateChange('playing', 'complete', tag: 'TTS');
        _logger.debug('Native audio playback completed');
        
        tempFile.delete().catchError((e) {
          _logger.warning('Failed to delete temp file', error: e);
        });
      });

    } catch (e, stackTrace) {
      _logger.error(
        'Native audio playback setup failed',
        error: e,
        stackTrace: stackTrace,
      );
      rethrow;
    }
  }

  /// Handle error response from API
  void _handleErrorResponse(http.Response response) {
    _logger.error('TTS API returned error status: ${response.statusCode}');
    
    try {
      final errorData = jsonDecode(response.body);
      _logger.error('Error details: ${jsonEncode(errorData)}');
      
      if (errorData['error'] != null) {
        final errorMessage = errorData['error']['message'] ?? 'Unknown error';
        _logger.error('API Error Message: $errorMessage');
      }
    } catch (e) {
      _logger.error('Raw error response: ${response.body}');
    }

    throw Exception('Gemini TTS API error: ${response.statusCode}');
  }

  /// Converte dados PCM raw para formato WAV
  /// Baseado no código Python oficial do Google
  Uint8List _convertPcmToWav(Uint8List pcmData, String mimeType) {
    _logger.debug('Converting PCM to WAV format...');
    
    // Parse parameters do mime type
    final params = _parseAudioMimeType(mimeType);
    final bitsPerSample = params['bitsPerSample'] ?? 16;
    final sampleRate = params['rate'] ?? 24000;

    _logger.debug('WAV params: ${bitsPerSample}bit, ${sampleRate}Hz');

    final numChannels = 1; // Mono
    final dataSize = pcmData.length;
    final bytesPerSample = bitsPerSample ~/ 8;
    final blockAlign = numChannels * bytesPerSample;
    final byteRate = sampleRate * blockAlign;
    final chunkSize = 36 + dataSize;

    // Criar WAV header (44 bytes)
    final header = ByteData(44);

    // RIFF chunk
    header.setUint8(0, 0x52); // 'R'
    header.setUint8(1, 0x49); // 'I'
    header.setUint8(2, 0x46); // 'F'
    header.setUint8(3, 0x46); // 'F'
    header.setUint32(4, chunkSize, Endian.little);

    // WAVE format
    header.setUint8(8, 0x57);  // 'W'
    header.setUint8(9, 0x41);  // 'A'
    header.setUint8(10, 0x56); // 'V'
    header.setUint8(11, 0x45); // 'E'

    // fmt subchunk
    header.setUint8(12, 0x66); // 'f'
    header.setUint8(13, 0x6D); // 'm'
    header.setUint8(14, 0x74); // 't'
    header.setUint8(15, 0x20); // ' '
    header.setUint32(16, 16, Endian.little); // Subchunk1Size (16 for PCM)
    header.setUint16(20, 1, Endian.little);  // AudioFormat (1 = PCM)
    header.setUint16(22, numChannels, Endian.little);
    header.setUint32(24, sampleRate, Endian.little);
    header.setUint32(28, byteRate, Endian.little);
    header.setUint16(32, blockAlign, Endian.little);
    header.setUint16(34, bitsPerSample, Endian.little);

    // data subchunk
    header.setUint8(36, 0x64); // 'd'
    header.setUint8(37, 0x61); // 'a'
    header.setUint8(38, 0x74); // 't'
    header.setUint8(39, 0x61); // 'a'
    header.setUint32(40, dataSize, Endian.little);

    // Combinar header + dados PCM
    final wavData = Uint8List(44 + dataSize);
    wavData.setRange(0, 44, header.buffer.asUint8List());
    wavData.setRange(44, 44 + dataSize, pcmData);

    return wavData;
  }

  /// Parse bits per sample e rate do mime type
  Map<String, int> _parseAudioMimeType(String mimeType) {
    int bitsPerSample = 16;
    int rate = 24000;

    // Exemplo: "audio/L16;rate=24000"
    final parts = mimeType.split(';');

    for (var part in parts) {
      part = part.trim();

      // Extrair rate
      if (part.toLowerCase().startsWith('rate=')) {
        try {
          final rateStr = part.split('=')[1];
          rate = int.parse(rateStr);
        } catch (e) {
          _logger.warning('Error parsing rate from mime type', error: e);
        }
      }

      // Extrair bits per sample de "audio/L16"
      if (part.startsWith('audio/L')) {
        try {
          final bitsStr = part.split('L')[1];
          bitsPerSample = int.parse(bitsStr);
        } catch (e) {
          _logger.warning('Error parsing bits per sample', error: e);
        }
      }
    }

    return {'bitsPerSample': bitsPerSample, 'rate': rate};
  }

  /// Stop current playback
  Future<void> stop() async {
    if (_isPlaying) {
      _logger.info('Stopping TTS playback');
      await _audioPlayer.stop();
      _isPlaying = false;
      LogUtils.logStateChange('playing', 'stopped', tag: 'TTS');
    }
  }

  /// Pause current playback
  Future<void> pause() async {
    if (_isPlaying) {
      _logger.info('Pausing TTS playback');
      await _audioPlayer.pause();
      LogUtils.logStateChange('playing', 'paused', tag: 'TTS');
    }
  }

  /// Resume paused playback
  Future<void> resume() async {
    if (!_isPlaying) {
      _logger.info('Resuming TTS playback');
      await _audioPlayer.resume();
      _isPlaying = true;
      LogUtils.logStateChange('paused', 'playing', tag: 'TTS');
    }
  }

  /// Clean up resources
  void dispose() {
    _logger.info('Disposing TTS service');
    _audioPlayer.dispose();
    _logger.success('TTS service disposed');
  }

  /// Speak multiple sentences with natural pauses
  Future<void> speakWithPauses(
    List<String> sentences, {
    Duration pauseDuration = const Duration(milliseconds: 500),
    String? voiceName,
  }) async {
    _logger.info('Speaking ${sentences.length} sentences with pauses');
    
    for (int i = 0; i < sentences.length; i++) {
      _logger.debug('Speaking sentence ${i + 1}/${sentences.length}');
      await speak(sentences[i], voiceName: voiceName);

      // Wait for current speech to finish
      while (_isPlaying) {
        await Future.delayed(const Duration(milliseconds: 100));
      }

      // Add pause between sentences (except after the last one)
      if (i < sentences.length - 1) {
        _logger.debug('Pausing ${pauseDuration.inMilliseconds}ms');
        await Future.delayed(pauseDuration);
      }
    }
    
    _logger.success('Completed speaking all sentences');
  }
}