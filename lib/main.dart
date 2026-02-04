import 'package:flutter/material.dart';
import 'home_screen.dart';
import 'services/gemini_config.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Gemini API configuration
  try {
    await GeminiConfig.initialize();
    print('Gemini API initialized successfully');
  } catch (e) {
    print('Error initializing Gemini API: $e');
  }

  runApp(const CloseByApp());
}

class CloseByApp extends StatelessWidget {
  const CloseByApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CloseBy',
      debugShowCheckedModeBanner: false,
      // 2. Apply the Elder-First Theme we discussed
      theme: ThemeData(
        useMaterial3: true,
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueAccent),
        textTheme: const TextTheme(
          displayLarge: TextStyle(fontSize: 32, fontWeight: FontWeight.bold),
          bodyLarge: TextStyle(fontSize: 22),
        ),
      ),
      // 3. Set CloseByHome as the starting screen
      home: const CloseByHome(), 
    );
  }
}