import 'package:flutter/material.dart';
import '../services/api_service.dart';

class AuthProvider extends ChangeNotifier {
  final ApiService _api = ApiService();

  bool _isLoggedIn = false;
  bool _isLoading = false;
  String _role = '';
  String _userId = '';
  String _name = '';
  String _error = '';

  bool get isLoggedIn => _isLoggedIn;
  bool get isLoading => _isLoading;
  String get role => _role;
  String get userId => _userId;
  String get name => _name;
  String get error => _error;

  Future<bool> login(String userId, String password, String role) async {
    _isLoading = true;
    _error = '';
    notifyListeners();

    try {
      final data = await _api.login(userId, password, role);
      _isLoggedIn = true;
      _role = data['role'];
      _userId = data['user_id'];
      _name = data['name'];
      _isLoading = false;
      notifyListeners();
      return true;
    } catch (e) {
      _isLoading = false;
      if (e is Exception) {
        _error = 'Invalid credentials. Please try again.';
      } else {
        _error = 'Connection error. Check your network.';
      }
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    await _api.logout();
    _isLoggedIn = false;
    _role = '';
    _userId = '';
    _name = '';
    _error = '';
    notifyListeners();
  }
}
