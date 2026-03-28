import 'dart:async';
import 'package:flutter/material.dart';
import '../services/api_service.dart';

class SessionProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  Map<String, dynamic>? _currentSession;
  String _currentToken = '';
  String _qrData = '';
  String _expiresAt = '';
  List<dynamic> _attendanceList = [];
  int _presentCount = 0;
  bool _isLoading = false;
  Timer? _tokenTimer;
  Timer? _attendanceTimer;

  Map<String, dynamic>? get currentSession => _currentSession;
  String get currentToken => _currentToken;
  String get qrData => _qrData;
  String get expiresAt => _expiresAt;
  List<dynamic> get attendanceList => _attendanceList;
  int get presentCount => _presentCount;
  bool get isLoading => _isLoading;
  bool get hasActiveSession => _currentSession != null;

  Future<bool> createSession(String subject, String className) async {
    _isLoading = true;
    notifyListeners();

    try {
      final session = await _api.createSession(subject, className);
      _currentSession = session;
      _isLoading = false;
      notifyListeners();

      // Start token rotation
      await _refreshToken();
      _startTokenRotation();
      _startAttendancePolling();

      return true;
    } catch (e) {
      _isLoading = false;
      notifyListeners();
      return false;
    }
  }

  Future<void> _refreshToken() async {
    if (_currentSession == null) return;

    try {
      final tokenData = await _api.generateToken(_currentSession!['id']);
      _currentToken = tokenData['token'];
      _qrData = tokenData['qr_data'];
      _expiresAt = tokenData['expires_at'];
      notifyListeners();
    } catch (e) {
      debugPrint('Token refresh error: $e');
    }
  }

  void _startTokenRotation() {
    _tokenTimer?.cancel();
    _tokenTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      _refreshToken();
    });
  }

  void _startAttendancePolling() {
    _attendanceTimer?.cancel();
    _attendanceTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      _fetchAttendance();
    });
  }

  Future<void> _fetchAttendance() async {
    if (_currentSession == null) return;

    try {
      final data = await _api.getSessionAttendance(_currentSession!['id']);
      _attendanceList = data['records'] ?? [];
      _presentCount = data['total_present'] ?? 0;
      notifyListeners();
    } catch (e) {
      debugPrint('Attendance fetch error: $e');
    }
  }

  Future<void> endSession() async {
    if (_currentSession == null) return;

    try {
      await _api.endSession(_currentSession!['id']);
    } catch (_) {}

    _tokenTimer?.cancel();
    _attendanceTimer?.cancel();
    _currentSession = null;
    _currentToken = '';
    _qrData = '';
    _attendanceList = [];
    _presentCount = 0;
    notifyListeners();
  }

  @override
  void dispose() {
    _tokenTimer?.cancel();
    _attendanceTimer?.cancel();
    super.dispose();
  }
}
