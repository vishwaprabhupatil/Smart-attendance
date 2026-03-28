import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const String baseUrl = 'http://10.167.250.226:8000'; 
  // For Android Emulator, use: 'http://10.0.2.2:8000'
  // Your detected machine IP: 'http://10.167.250.226:8000'

  final Dio _dio;
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  ApiService()
      : _dio = Dio(BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 10),
          receiveTimeout: const Duration(seconds: 10),
          headers: {'Content-Type': 'application/json'},
        )) {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'access_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ));
  }

  // ─── Auth ──────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> login(String userId, String password, String role) async {
    final response = await _dio.post('/auth/login', data: {
      'user_id': userId,
      'password': password,
      'role': role,
    });
    final data = response.data;
    await _storage.write(key: 'access_token', value: data['access_token']);
    return data;
  }

  Future<void> logout() async {
    await _storage.delete(key: 'access_token');
  }

  // ─── Sessions ──────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> createSession(String subject, String className) async {
    final response = await _dio.post('/sessions/create', data: {
      'subject': subject,
      'class': className,
    });
    return response.data;
  }

  Future<Map<String, dynamic>> generateToken(String sessionId) async {
    final response = await _dio.get('/sessions/$sessionId/token');
    return response.data;
  }

  Future<void> endSession(String sessionId) async {
    await _dio.post('/sessions/$sessionId/end');
  }

  // ─── Attendance ────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> markAttendance(String studentId, String token) async {
    final response = await _dio.post('/attendance/mark', data: {
      'student_id': studentId,
      'token': token,
    });
    return response.data;
  }

  Future<Map<String, dynamic>> getSessionAttendance(String sessionId) async {
    final response = await _dio.get('/attendance/session/$sessionId');
    return response.data;
  }
}
