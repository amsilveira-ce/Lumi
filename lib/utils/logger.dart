import 'package:flutter/foundation.dart';

/// Log levels for categorizing messages
enum LogLevel {
  debug,   // Detailed debugging information
  info,    // General informational messages
  warning, // Warning messages for potential issues
  error,   // Error messages for failures
  success, // Success messages for completed operations
}

/// Centralized logging service for consistent, structured logging
/// 
/// Features:
/// - Color-coded console output
/// - Log levels for filtering
/// - Timestamps for tracking
/// - Service/component tagging
/// - Performance timing
/// - Stack trace on errors
class AppLogger {
  static bool _enableDebugLogs = kDebugMode; // Auto-disable in release
  static bool _enableTimestamps = true;
  static bool _enableStackTraces = true;

  // ANSI color codes for terminal output
  static const String _reset = '\x1B[0m';
  static const String _red = '\x1B[31m';
  static const String _green = '\x1B[32m';
  static const String _yellow = '\x1B[33m';
  static const String _blue = '\x1B[34m';
  static const String _magenta = '\x1B[35m';
  static const String _cyan = '\x1B[36m';
  static const String _white = '\x1B[37m';
  static const String _bold = '\x1B[1m';

  /// Configure logging behavior
  static void configure({
    bool? enableDebugLogs,
    bool? enableTimestamps,
    bool? enableStackTraces,
  }) {
    if (enableDebugLogs != null) _enableDebugLogs = enableDebugLogs;
    if (enableTimestamps != null) _enableTimestamps = enableTimestamps;
    if (enableStackTraces != null) _enableStackTraces = enableStackTraces;
  }

  /// Log a debug message
  static void debug(String message, {String? tag}) {
    if (!_enableDebugLogs) return;
    _log(LogLevel.debug, message, tag: tag);
  }

  /// Log an info message
  static void info(String message, {String? tag}) {
    _log(LogLevel.info, message, tag: tag);
  }

  /// Log a warning message
  static void warning(String message, {String? tag, Object? error}) {
    _log(LogLevel.warning, message, tag: tag, error: error);
  }

  /// Log an error message
  static void error(String message, {String? tag, Object? error, StackTrace? stackTrace}) {
    _log(LogLevel.error, message, tag: tag, error: error, stackTrace: stackTrace);
  }

  /// Log a success message
  static void success(String message, {String? tag}) {
    _log(LogLevel.success, message, tag: tag);
  }

  /// Log with custom level
  static void _log(
    LogLevel level,
    String message, {
    String? tag,
    Object? error,
    StackTrace? stackTrace,
  }) {
    final buffer = StringBuffer();

    // Add timestamp
    if (_enableTimestamps) {
      buffer.write(_getTimestamp());
      buffer.write(' ');
    }

    // Add level indicator with color
    buffer.write(_getLevelIndicator(level));
    buffer.write(' ');

    // Add tag if provided
    if (tag != null) {
      buffer.write(_cyan);
      buffer.write('[$tag]');
      buffer.write(_reset);
      buffer.write(' ');
    }

    // Add message
    buffer.write(_getColorForLevel(level));
    buffer.write(message);
    buffer.write(_reset);

    // Print main log line
    debugPrint(buffer.toString());

    // Add error details if provided
    if (error != null) {
      debugPrint('$_red  ↳ Error: $error$_reset');
    }

    // Add stack trace for errors if enabled
    if (stackTrace != null && _enableStackTraces && level == LogLevel.error) {
      debugPrint('$_red  ↳ Stack Trace:$_reset');
      final lines = stackTrace.toString().split('\n');
      for (int i = 0; i < lines.length && i < 5; i++) {
        debugPrint('$_red    ${lines[i]}$_reset');
      }
    }
  }

  /// Get timestamp string
  static String _getTimestamp() {
    final now = DateTime.now();
    return '$_white${now.hour.toString().padLeft(2, '0')}:'
        '${now.minute.toString().padLeft(2, '0')}:'
        '${now.second.toString().padLeft(2, '0')}.'
        '${now.millisecond.toString().padLeft(3, '0')}$_reset';
  }

  /// Get level indicator emoji/text
  static String _getLevelIndicator(LogLevel level) {
    switch (level) {
      case LogLevel.debug:
        return '$_blue🔍 DEBUG$_reset';
      case LogLevel.info:
        return '$_cyan ℹ️  INFO$_reset';
      case LogLevel.warning:
        return '$_yellow⚠️  WARN$_reset';
      case LogLevel.error:
        return '$_red❌ ERROR$_reset';
      case LogLevel.success:
        return '$_green✅ SUCCESS$_reset';
    }
  }

  /// Get color for log level
  static String _getColorForLevel(LogLevel level) {
    switch (level) {
      case LogLevel.debug:
        return _blue;
      case LogLevel.info:
        return _cyan;
      case LogLevel.warning:
        return _yellow;
      case LogLevel.error:
        return _red;
      case LogLevel.success:
        return _green;
    }
  }
}

/// Service-specific loggers for better organization
class ServiceLogger {
  final String serviceName;

  ServiceLogger(this.serviceName);

  void debug(String message) => AppLogger.debug(message, tag: serviceName);
  void info(String message) => AppLogger.info(message, tag: serviceName);
  void warning(String message, {Object? error}) => 
      AppLogger.warning(message, tag: serviceName, error: error);
  void error(String message, {Object? error, StackTrace? stackTrace}) => 
      AppLogger.error(message, tag: serviceName, error: error, stackTrace: stackTrace);
  void success(String message) => AppLogger.success(message, tag: serviceName);
}

/// Performance timer for measuring execution time
class PerformanceTimer {
  final String operation;
  final Stopwatch _stopwatch = Stopwatch();
  final ServiceLogger? _logger;

  PerformanceTimer(this.operation, {ServiceLogger? logger}) : _logger = logger {
    _stopwatch.start();
    _logger?.debug('Started: $operation');
  }

  /// Stop the timer and log the duration
  void stop() {
    _stopwatch.stop();
    final duration = _stopwatch.elapsedMilliseconds;
    final message = 'Completed: $operation (${duration}ms)';
    
    if (duration > 1000) {
      _logger?.warning(message); // Slow operation
    } else {
      _logger?.success(message);
    }
  }

  /// Get elapsed time without stopping
  Duration get elapsed => _stopwatch.elapsed;
}

/// Extension for logging exceptions
extension ExceptionLogging on Exception {
  void log(String message, {String? tag, StackTrace? stackTrace}) {
    AppLogger.error(message, tag: tag, error: this, stackTrace: stackTrace);
  }
}

/// Logging utilities for common patterns
class LogUtils {
  /// Log the start of a voice interaction flow
  static void logVoiceFlowStart(String step) {
    AppLogger.info('═══ Voice Flow: $step ═══', tag: 'FLOW');
  }

  /// Log an API call
  static void logApiCall(String endpoint, {Map<String, dynamic>? params}) {
    final buffer = StringBuffer('API Call: $endpoint');
    if (params != null && params.isNotEmpty) {
      buffer.write(' | Params: $params');
    }
    AppLogger.debug(buffer.toString(), tag: 'API');
  }

  /// Log API response
  static void logApiResponse(String endpoint, int statusCode, {int? bytes}) {
    final buffer = StringBuffer('API Response: $endpoint | Status: $statusCode');
    if (bytes != null) {
      buffer.write(' | Size: ${_formatBytes(bytes)}');
    }
    
    if (statusCode >= 200 && statusCode < 300) {
      AppLogger.success(buffer.toString(), tag: 'API');
    } else {
      AppLogger.error(buffer.toString(), tag: 'API');
    }
  }

  /// Log state change
  static void logStateChange(String from, String to, {String? tag}) {
    AppLogger.info('State: $from → $to', tag: tag ?? 'STATE');
  }

  /// Log user interaction
  static void logUserAction(String action) {
    AppLogger.info('User: $action', tag: 'UI');
  }

  /// Format bytes for display
  static String _formatBytes(int bytes) {
    if (bytes < 1024) return '${bytes}B';
    if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(1)}KB';
    return '${(bytes / (1024 * 1024)).toStringAsFixed(1)}MB';
  }

  /// Log audio processing details
  static void logAudioInfo({
    required int bytes,
    required String format,
    int? sampleRate,
    int? duration,
  }) {
    final buffer = StringBuffer('Audio: ${_formatBytes(bytes)} | Format: $format');
    if (sampleRate != null) buffer.write(' | Rate: ${sampleRate}Hz');
    if (duration != null) buffer.write(' | Duration: ${duration}ms');
    
    AppLogger.debug(buffer.toString(), tag: 'AUDIO');
  }
}