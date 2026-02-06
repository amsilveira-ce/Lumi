import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'gemini_config.dart';

/// Serviço de Speech-to-Text usando Gemini
///
/// Converte áudio em texto usando as capacidades multimodais do Gemini
class GeminiSTTService {
  /// Transcreve áudio para texto usando Gemini
  ///
  /// [audioBytes] - Dados do áudio em formato WAV ou outros formatos suportados
  /// [mimeType] - Tipo MIME do áudio (ex: 'audio/wav', 'audio/webm')
  Future<String> transcribe(Uint8List audioBytes, {String mimeType = 'audio/wav'}) async {
    if (!GeminiConfig.isInitialized) {
      throw Exception('GeminiConfig not initialized');
    }

    try {
      final apiKey = GeminiConfig.apiKey;

      // Usar Gemini 2.5 Flash (modelo estável mais recente com suporte a áudio)
      final url = Uri.parse(
        'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$apiKey'
      );

      // Converter áudio para base64
      final audioBase64 = base64Encode(audioBytes);

      // Construir requisição com áudio inline
      final requestBody = jsonEncode({
        'contents': [
          {
            'role': 'user',
            'parts': [
              {
                'text': 'Transcreva o áudio a seguir em português. Responda APENAS com a transcrição exata:'
              }
            ]
          },
          {
            'role': 'model',
            'parts': [
              {
                'text': 'Ok, vou transcrever o áudio.'
              }
            ]
          },
          {
            'role': 'user',
            'parts': [
              {
                'inlineData': {
                  'mimeType': mimeType,
                  'data': audioBase64
                }
              }
            ]
          }
        ],
        'generationConfig': {
          'temperature': 0.1, // Baixa temperatura para transcrição precisa
        }
      });

      print('Requesting Gemini STT transcription');
      print('Audio size: ${audioBytes.length} bytes');
      print('Mime type: $mimeType');

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

        // Extrair texto da resposta
        final candidates = responseData['candidates'] as List?;
        if (candidates == null || candidates.isEmpty) {
          throw Exception('No candidates in response');
        }

        final parts = candidates[0]['content']['parts'] as List?;
        if (parts == null || parts.isEmpty) {
          throw Exception('No parts in response');
        }

        final transcription = parts[0]['text'] as String?;
        if (transcription == null || transcription.isEmpty) {
          throw Exception('No transcription in response');
        }

        print('Transcription: $transcription');
        return transcription.trim();

      } else {
        final errorBody = response.body;
        throw Exception('Gemini STT API error: ${response.statusCode} - $errorBody');
      }

    } catch (e) {
      print('Error in Gemini STT: $e');
      rethrow;
    }
  }

  /// Transcreve áudio de base64
  Future<String> transcribeFromBase64(String audioBase64, {String mimeType = 'audio/wav'}) async {
    final audioBytes = base64Decode(audioBase64);
    return transcribe(audioBytes, mimeType: mimeType);
  }
}
