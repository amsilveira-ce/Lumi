import 'package:flutter_dotenv/flutter_dotenv.dart';
import 'package:google_generative_ai/google_generative_ai.dart';

class GeminiConfig {
  static String? _apiKey;
  static GenerativeModel? _model;

  /// Initialize the Gemini API configuration
  static Future<void> initialize() async {
    await dotenv.load(fileName: ".env");
    _apiKey = dotenv.env['GEMINI_API_KEY'];

    if (_apiKey == null || _apiKey!.isEmpty) {
      throw Exception('GEMINI_API_KEY not found in environment variables');
    }

    // Initialize the Gemini model for text generation
    _model = GenerativeModel(
      model: 'gemini-2.0-flash-exp',
      apiKey: _apiKey!,
    );
  }

  /// Get the API key
  static String get apiKey {
    if (_apiKey == null) {
      throw Exception('GeminiConfig not initialized. Call initialize() first.');
    }
    return _apiKey!;
  }

  /// Get the Gemini model instance
  static GenerativeModel get model {
    if (_model == null) {
      throw Exception('GeminiConfig not initialized. Call initialize() first.');
    }
    return _model!;
  }

  /// Check if the configuration is initialized
  static bool get isInitialized => _apiKey != null && _model != null;
}
