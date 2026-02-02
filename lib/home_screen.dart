import 'dart:async';
import 'dart:math';
import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:waveform_flutter/waveform_flutter.dart';

class CloseByHome extends StatefulWidget {
  const CloseByHome({super.key});

  @override
  State<CloseByHome> createState() => _CloseByHomeState();
}

class _CloseByHomeState extends State<CloseByHome> with TickerProviderStateMixin {
  bool isListening = false;
  
  // FIX: Nullable controller to prevent LateInitializationError
  AnimationController? _pulseController;

  @override
  void initState() {
    super.initState();
    // Initialize the breathing animation safely
    _pulseController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
      lowerBound: 0.95,
      upperBound: 1.05,
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    // FIX: Check for null before disposing to prevent errors
    _pulseController?.dispose();
    super.dispose();
  }

  // Helper to create a stream of amplitude data for the waveform
  Stream<Amplitude> _createAmplitudeStream() {
    return Stream.periodic(
      const Duration(milliseconds: 100),
      (_) => Amplitude(
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
          // 1. Background Environment
          _buildBlurredBackground(),

          SafeArea(
            child: Column(
              children: [
                // EMERGENCY PROTOCOL & HEADER
                _buildHeader(),

                // 2. CENTRALIZED CORE: Persona -> Context -> Visual Guidance
                Expanded(
                  child: Center(
                    child: SingleChildScrollView(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          _buildPresenceAvatar(),
                          const SizedBox(height: 32),
                          
                          // Dynamic Dialogue
                          _buildDialogueArea(),
                          
                          const SizedBox(height: 24),

                          // VOICE-FIRST VISUAL NAVIGATION
                          // Shows buttons only when not actively listening to prevent clutter
                          if (!isListening) _buildContextualActions(),

                          const SizedBox(height: 32),

                          // EMOTION-AWARE WAVEFORM
                          SizedBox(
                            height: 60,
                            width: 200,
                            child: AnimatedOpacity(
                              opacity: isListening ? 1.0 : 0.3,
                              duration: const Duration(milliseconds: 500),
                              child: AnimatedWaveList(
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

          // 3. PROACTIVE MANAGEMENT (Floating Reminder)
          Positioned(
            top: 100,
            right: 20,
            child: _buildMemoryPromptCard(),
          ),
        ],
      ),
    );
  }

  // --- UI Component Builders ---

  Widget _buildPresenceAvatar() {
    // FIX: Use a default value if controller isn't ready yet
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
              color: isListening ? Colors.blueAccent.withOpacity(0.4) : Colors.blueAccent.withOpacity(0.1),
              blurRadius: isListening ? 60 : 30,
              spreadRadius: isListening ? 15 : 5,
            )
          ],
        ),
        child: CircleAvatar(
          radius: 90,
          backgroundColor: Colors.white10,
          child: const CircleAvatar(
            radius: 86,
            backgroundImage: AssetImage('assets/images/elder_woman_profile.jpeg'),
          ),
        ),
      ),
    );
  }

  Widget _buildDialogueArea() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 40),
      child: Column(
        children: [
          Text(
            "\"I found those photos of Leo.\"",
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 20,
              fontStyle: FontStyle.italic,
            ),
          ),
          const SizedBox(height: 12),
          const Text(
            "Shall we call him now?",
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Colors.white,
              fontSize: 32,
              fontWeight: FontWeight.w500,
              height: 1.2,
            ),
          ),
        ],
      ),
    );
  }

  // Visual cues to guide the user (Voice-First Navigation)
  Widget _buildContextualActions() {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        _buildActionButton(
          label: "No, later", 
          icon: Icons.close, 
          color: Colors.white24
        ),
        const SizedBox(width: 20),
        _buildActionButton(
          label: "Yes, Call", 
          icon: Icons.videocam_rounded, 
          color: const Color(0xFF4CAF50), // Green for positive action
          isPrimary: true
        ),
      ],
    );
  }

  Widget _buildActionButton({required String label, required IconData icon, required Color color, bool isPrimary = false}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
      decoration: BoxDecoration(
        color: color,
        borderRadius: BorderRadius.circular(30),
        boxShadow: isPrimary ? [
           BoxShadow(color: color.withOpacity(0.4), blurRadius: 12, offset: const Offset(0, 4))
        ] : [],
      ),
      child: Row(
        children: [
          Icon(icon, color: Colors.white, size: 28),
          const SizedBox(width: 12),
          Text(
            label,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.bold,
            ),
          ),
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
          // Health Status
          const Row(
            children: [
              Icon(Icons.favorite, color: Colors.redAccent, size: 20),
              SizedBox(width: 8),
              Text("72 BPM", style: TextStyle(color: Colors.white60, fontSize: 16)),
            ],
          ),
          
          // EMERGENCY PROTOCOL BUTTON
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: const Color(0xFFD32F2F).withOpacity(0.2), // Red tint
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: Colors.redAccent.withOpacity(0.5)),
            ),
            child: const Row(
              children: [
                Icon(Icons.shield, color: Colors.redAccent, size: 20),
                SizedBox(width: 8),
                Text("HELP", style: TextStyle(color: Colors.redAccent, fontWeight: FontWeight.bold)),
              ],
            ),
          )
        ],
      ),
    ); 
  }

  // PROACTIVE DAILY MANAGEMENT CARD
  Widget _buildMemoryPromptCard() { 
    return Container(
      width: 220,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.grey[900]!.withOpacity(0.9),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white10),
        boxShadow: [
          BoxShadow(color: Colors.black.withOpacity(0.5), blurRadius: 10, offset: const Offset(0, 4))
        ]
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(6),
                decoration: const BoxDecoration(color: Colors.orangeAccent, shape: BoxShape.circle),
                child: const Icon(Icons.medication, size: 16, color: Colors.black),
              ),
              const SizedBox(width: 10),
              const Text("REMINDER", style: TextStyle(color: Colors.orangeAccent, fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            "Blood pressure pill",
            style: TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const Text(
            "Due in 15 mins",
            style: TextStyle(color: Colors.white54, fontSize: 14),
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
          GestureDetector(
            onTap: () => setState(() => isListening = !isListening),
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 300),
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: isListening ? Colors.white : Colors.white10,
                boxShadow: isListening ? [
                   BoxShadow(color: Colors.white.withOpacity(0.3), blurRadius: 30, spreadRadius: 5)
                ] : [],
              ),
              child: Icon(
                isListening ? Icons.mic : Icons.mic_none,
                color: isListening ? Colors.black : Colors.white,
                size: 44,
              ),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            isListening ? "I'm listening, Mary..." : "Tap to speak",
            style: TextStyle(
              color: isListening ? Colors.white : Colors.white38,
              fontWeight: FontWeight.w600,
              letterSpacing: 1.2,
              fontSize: 16,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBlurredBackground() {
    return Positioned.fill(
      child: Image.asset(
        'assets/images/calm_living_room.png',
        fit: BoxFit.cover,
        color: Colors.black.withOpacity(0.6),
        colorBlendMode: BlendMode.darken,
      ),
    );
  }
}