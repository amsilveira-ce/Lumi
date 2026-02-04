import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:audioplayers/audioplayers.dart';
import 'gemini_config.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

// Import condicional para dart:io (não disponível na web)
import 'dart:io' if (dart.library.html) 'dart:io';
import 'package:path_provider/path_provider.dart';

/// Serviço de Text-to-Speech usando Gemini 2.5 Flash TTS
///
/// Baseado na documentação oficial do Google:
/// https://ai.google.dev/gemini-api/docs/audio
class GeminiTTSService {
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
      throw Exception('GeminiConfig not initialized');
    }

    try {
      // Stop any currently playing audio
      await stop();

      final apiKey = GeminiConfig.apiKey;
      final voice = voiceName ?? _defaultVoice;

      // Usar o modelo correto: gemini-2.5-flash-preview-tts
      final url = Uri.parse(
        'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key=$apiKey'
      );

      // Construir requisição seguindo o formato oficial
      final requestBody = jsonEncode({
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

      print('Requesting Gemini TTS with model: gemini-2.5-flash-preview-tts');
      print('Voice: $voice');
      print('Text: $text');

      final response = await http.post(
        url,
        headers: {
          'Content-Type': 'application/json',
        },
        body: requestBody,
      );

      print('Response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        final responseData = jsonDecode(response.body);

        // Extract audio data from response
        final candidates = responseData['candidates'] as List?;
        if (candidates == null || candidates.isEmpty) {
          throw Exception('No candidates in response');
        }

        final parts = candidates[0]['content']['parts'] as List?;
        if (parts == null || parts.isEmpty) {
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
              print('Found audio data with mime type: $mimeType');
              break;
            }
          }
        }

        if (audioBase64 == null) {
          throw Exception('No audio data in response. Response: ${jsonEncode(responseData)}');
        }

        // Decode base64 audio (PCM raw)
        final pcmData = base64Decode(audioBase64);
        print('Audio decoded: ${pcmData.length} bytes');

        // Converter PCM para WAV
        final wavData = _convertPcmToWav(pcmData, mimeType ?? 'audio/L16;rate=24000');
        print('Converted to WAV: ${wavData.length} bytes');

        // Play the audio (diferente para web e mobile)
        _isPlaying = true;

        if (kIsWeb) {
          // Web: usar data URL (base64)
          final base64Audio = base64Encode(wavData);
          final dataUrl = 'data:audio/wav;base64,$base64Audio';
          print('Using data URL for web playback');

          await _audioPlayer.play(UrlSource(dataUrl));

          // Listen for completion
          _audioPlayer.onPlayerComplete.listen((_) {
            _isPlaying = false;
          });
        } else {
          // Mobile/Desktop: usar arquivo temporário
          final tempDir = await getTemporaryDirectory();
          final tempFile = File(
            '${tempDir.path}/gemini_tts_${DateTime.now().millisecondsSinceEpoch}.wav'
          );
          await tempFile.writeAsBytes(wavData);
          print('Audio saved to: ${tempFile.path}');

          await _audioPlayer.play(DeviceFileSource(tempFile.path));

          // Listen for completion and cleanup
          _audioPlayer.onPlayerComplete.listen((_) {
            _isPlaying = false;
            tempFile.delete().catchError((e) {
              print('Error deleting temp file: $e');
            });
          });
        }

      } else {
        final errorBody = response.body;
        throw Exception('Gemini TTS API error: ${response.statusCode} - $errorBody');
      }

    } catch (e) {
      _isPlaying = false;
      print('Error in Gemini TTS: $e');
      rethrow;
    }
  }

  /// Converte dados PCM raw para formato WAV
  /// Baseado no código Python oficial do Google
  Uint8List _convertPcmToWav(Uint8List pcmData, String mimeType) {
    // Parse parameters do mime type
    final params = _parseAudioMimeType(mimeType);
    final bitsPerSample = params['bitsPerSample'] ?? 16;
    final sampleRate = params['rate'] ?? 24000;

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
          print('Error parsing rate: $e');
        }
      }

      // Extrair bits per sample de "audio/L16"
      if (part.startsWith('audio/L')) {
        try {
          final bitsStr = part.split('L')[1];
          bitsPerSample = int.parse(bitsStr);
        } catch (e) {
          print('Error parsing bits per sample: $e');
        }
      }
    }

    return {'bitsPerSample': bitsPerSample, 'rate': rate};
  }

  /// Stop current playback
  Future<void> stop() async {
    if (_isPlaying) {
      await _audioPlayer.stop();
      _isPlaying = false;
    }
  }

  /// Pause current playback
  Future<void> pause() async {
    if (_isPlaying) {
      await _audioPlayer.pause();
    }
  }

  /// Resume paused playback
  Future<void> resume() async {
    if (!_isPlaying) {
      await _audioPlayer.resume();
      _isPlaying = true;
    }
  }

  /// Clean up resources
  void dispose() {
    _audioPlayer.dispose();
  }

  /// Speak multiple sentences with natural pauses
  Future<void> speakWithPauses(
    List<String> sentences, {
    Duration pauseDuration = const Duration(milliseconds: 500),
    String? voiceName,
  }) async {
    for (int i = 0; i < sentences.length; i++) {
      await speak(sentences[i], voiceName: voiceName);

      // Wait for current speech to finish
      while (_isPlaying) {
        await Future.delayed(const Duration(milliseconds: 100));
      }

      // Add pause between sentences (except after the last one)
      if (i < sentences.length - 1) {
        await Future.delayed(pauseDuration);
      }
    }
  }
}
