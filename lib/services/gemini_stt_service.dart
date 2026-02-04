import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'gemini_config.dart';
import '../utils/logger.dart';

/// Serviço de Speech-to-Text usando Gemini
///
/// Converte áudio em texto usando as capacidades multimodais do Gemini
class GeminiSTTService {
  final _logger = ServiceLogger('STT');

  Future<String> transcribe(
    Uint8List audioBytes, {
    String mimeType = 'audio/wav',
  }) async {
    if (!GeminiConfig.isInitialized) {
      _logger.error('GeminiConfig not initialized');
      throw Exception('GeminiConfig not initialized');
    }

    _logger.info('Starting audio transcription');
    LogUtils.logAudioInfo(bytes: audioBytes.length, format: mimeType);

    final timer = PerformanceTimer('STT API Call', logger: _logger);

    try {
      final apiKey = GeminiConfig.apiKey;
      final modelName = 'gemini-2.5-flash';

      final url = Uri.parse(
        'https://generativelanguage.googleapis.com/v1beta/models/$modelName:generateContent?key=$apiKey',
      );

      // Converter áudio para base64
      _logger.debug('Converting audio to base64...');
      final audioBase64 = base64Encode(audioBytes);

      // Construir requisição com áudio inline
      final requestBody = _buildRequestBody(audioBase64, mimeType);

      LogUtils.logApiCall(
        'generatedContent',
        params: {
          'model': modelName,
          'mimeType': mimeType,
          'audioSize': audioBytes.length,
        },
      );

      final response = await http.post(
        url,
        headers: {'Content-Type': 'application/json'},
        body: requestBody,
      );

      LogUtils.logApiResponse(
        'generatedContent',
        response.statusCode,
        bytes: response.bodyBytes.length,
      );

      if (response.statusCode == 200) {
        final transcription = _parseSuccessResponse(response.body);
        timer.stop();

        _logger.success('Transcription sucessful: "$transcription"');
        return transcription;

      } else {
        timer.stop();
        // final errorBody = response.body;
        _handleErrorResponse(response);
        throw Exception('Transcription failed');
      }
    } catch (e, stackTrace) {
      timer.stop();
      _logger.error('STT transcription failed',
      error:e,
      stackTrace: stackTrace
      );
      
      rethrow;
    }
  }

  /// Transcreve áudio de base64
  Future<String> transcribeFromBase64(
    String audioBase64, {
    String mimeType = 'audio/wav',
  }) async {
    final audioBytes = base64Decode(audioBase64);
    return transcribe(audioBytes, mimeType: mimeType);
  }

  void _handleErrorResponse(http.Response response) {
    _logger.error('STT API returned error status: ${response.statusCode}');

    try {
      final errorData = jsonDecode(response.body);
      _logger.error('Error details: ${jsonEncode(errorData)}');

      // Extract specific error message if available
      if (errorData['error'] != null) {
        final errorMessage = errorData['error']['message'] ?? 'Unknown error';
        _logger.error('API Error Message: $errorMessage');
      }
    } catch (e) {
      _logger.error('Raw error response: ${response.body}');
    }

    throw Exception('Gemini STT API error: ${response.statusCode}');
  }

  String _parseSuccessResponse(String responseBody) {
    _logger.debug('Parsing STT response...');

    try {
      final responseData = jsonDecode(responseBody);

      // Extrair texto da resposta
      final candidates = responseData['candidates'] as List?;
      if (candidates == null || candidates.isEmpty) {
        _logger.warning('No candidates in response');
        throw Exception('No candidates in response');
      }

      final parts = candidates[0]['content']['parts'] as List?;
      if (parts == null || parts.isEmpty) {
        _logger.warning('No parts in response');
        throw Exception('No parts in response');
      }

      final transcription = parts[0]['text'] as String?;
      if (transcription == null || transcription.isEmpty) {
        _logger.warning('Empty transcription in response');
        throw Exception('No transcription in response');
      }

      return transcription.trim();
    } catch (e, stackTrace) {
      _logger.error(
        'Failed to parse STT response',
        error: e,
        stackTrace: stackTrace,
      );
      _logger.debug('Response body: $responseBody');
      rethrow;
    }
  }

  String _buildRequestBody(String audioBase64, String mimeType) {
    _logger.debug('Building STT request body...');

    return jsonEncode({
      'contents': [
        {
          'role': 'user',
          'parts': [
            {
              'text':
                  'Transcreva o áudio a seguir em português. Responda APENAS com a transcrição exata:',
            },
          ],
        },

        /// ---- check this later
        {
          'role': 'model',
          'parts': [
            {'text': 'Ok, vou transcrever o áudio.'},
          ],
        },
        {
          'role': 'user',
          'parts': [
            {
              'inlineData': {'mimeType': mimeType, 'data': audioBase64},
            },
          ],
        },
      ],
      'generationConfig': {
        'temperature': 0.1, // Baixa temperatura para transcrição precisa
      },
    });
  }
}
