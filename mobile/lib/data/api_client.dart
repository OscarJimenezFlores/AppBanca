import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../types/models.dart';

class SessionStore {
  SessionStore({FlutterSecureStorage? storage}) : _storage = storage ?? const FlutterSecureStorage();

  final FlutterSecureStorage _storage;
  String? accessToken;
  String? refreshToken;
  UserProfile? profile;
  bool ready = false;

  Future<void> initialize() async {
    accessToken = await _storage.read(key: 'access');
    refreshToken = await _storage.read(key: 'refresh');
    ready = true;
  }

  Future<void> save(LoginResult result) async {
    accessToken = result.accessToken;
    refreshToken = result.refreshToken;
    if (accessToken != null) {
      await _storage.write(key: 'access', value: accessToken);
    }
    if (refreshToken != null) {
      await _storage.write(key: 'refresh', value: refreshToken);
    }
  }

  Future<void> clear() async {
    accessToken = null;
    refreshToken = null;
    profile = null;
    await _storage.deleteAll();
  }
}

class ApiClient {
  ApiClient(this.session, {String? baseUrl})
      : _dio = Dio(
          BaseOptions(
            baseUrl: baseUrl ?? const String.fromEnvironment('API_BASE_URL', defaultValue: 'http://10.0.2.2:8080'),
            connectTimeout: const Duration(seconds: 15),
            receiveTimeout: const Duration(seconds: 20),
            headers: {'Content-Type': 'application/json'},
          ),
        ) {
    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          final token = session.accessToken;
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          final status = error.response?.statusCode;
          final path = error.requestOptions.path;
          final retried = error.requestOptions.extra['retried'] == true;
          if (status == 401 && !retried && !path.contains('/auth/') && session.refreshToken != null) {
            final renewed = await _refresh();
            if (renewed) {
              final request = error.requestOptions;
              request.extra['retried'] = true;
              request.headers['Authorization'] = 'Bearer ${session.accessToken}';
              try {
                final response = await _dio.fetch(request);
                handler.resolve(response);
                return;
              } on DioException catch (retryError) {
                handler.next(retryError);
                return;
              }
            }
          }
          handler.next(error);
        },
      ),
    );
  }

  final SessionStore session;
  final Dio _dio;
  Future<bool>? _refreshing;

  Future<Map<String, dynamic>> get(String path, {Map<String, dynamic>? query}) async {
    try {
      final response = await _dio.get(path, queryParameters: query);
      return _map(response.data);
    } on DioException catch (error) {
      throw _exception(error);
    }
  }

  Future<List<dynamic>> getList(String path, {Map<String, dynamic>? query}) async {
    try {
      final response = await _dio.get(path, queryParameters: query);
      final data = response.data;
      if (data is List) {
        return data;
      }
      throw ApiException(code: 'FORMAT', message: 'La respuesta no es una lista.');
    } on DioException catch (error) {
      throw _exception(error);
    }
  }

  Future<Map<String, dynamic>> post(String path, Map<String, dynamic> body) async {
    try {
      final response = await _dio.post(path, data: body);
      if (response.data == null || response.data == '') {
        return {};
      }
      return _map(response.data);
    } on DioException catch (error) {
      throw _exception(error);
    }
  }

  Future<void> postEmpty(String path, Map<String, dynamic> body) async {
    try {
      await _dio.post(path, data: body);
    } on DioException catch (error) {
      throw _exception(error);
    }
  }

  Future<bool> _refresh() {
    return _refreshing ??= _doRefresh().whenComplete(() => _refreshing = null);
  }

  Future<bool> _doRefresh() async {
    final token = session.refreshToken;
    if (token == null) {
      return false;
    }
    try {
      final response = await _dio.post('/api/v1/auth/refresh', data: {'refresh_token': token});
      final body = _map(response.data);
      await session.save(
        LoginResult(
          requiresOtp: false,
          accessToken: body['access_token'] as String?,
          refreshToken: body['refresh_token'] as String?,
        ),
      );
      return session.accessToken != null;
    } catch (_) {
      await session.clear();
      return false;
    }
  }

  Map<String, dynamic> _map(Object? data) {
    if (data is Map<String, dynamic>) {
      return data;
    }
    if (data is Map) {
      return data.map((key, value) => MapEntry(key.toString(), value));
    }
    throw ApiException(code: 'FORMAT', message: 'La respuesta no tiene la forma esperada.');
  }

  ApiException _exception(DioException error) {
    final data = error.response?.data;
    if (data is Map) {
      final details = data['details'];
      return ApiException(
        code: (data['code'] ?? 'ERROR').toString(),
        message: (data['message'] ?? 'No se pudo completar la operación.').toString(),
        status: error.response?.statusCode,
        details: details is List ? details.map((item) => item.toString()).toList() : const [],
      );
    }
    return ApiException(
      code: 'NETWORK',
      message: 'No hay conexión con AndesBank. Revise que el API esté en marcha.',
      status: error.response?.statusCode,
    );
  }
}
