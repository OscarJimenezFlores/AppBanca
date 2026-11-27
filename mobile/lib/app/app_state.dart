import 'package:flutter/foundation.dart';

import '../data/api_bank.dart';
import '../data/api_client.dart';
import '../types/models.dart';

class AppState extends ChangeNotifier {
  AppState({ApiClient? client}) {
    session = SessionStore();
    final api = client ?? ApiClient(session);
    bank = ApiBank(api);
  }

  late final SessionStore session;
  late final ApiBank bank;
  bool ready = false;

  Future<void> initialize() async {
    await session.initialize();
    if (session.accessToken != null) {
      try {
        session.profile = await bank.me();
      } catch (_) {
        await session.clear();
      }
    }
    ready = true;
    notifyListeners();
  }

  Future<void> enter(LoginResult result) async {
    await session.save(result);
    session.profile = await bank.me();
    notifyListeners();
  }

  void rememberProfile(UserProfile profile) {
    session.profile = profile;
    notifyListeners();
  }

  Future<void> exit() async {
    final refresh = session.refreshToken;
    if (refresh != null) {
      try {
        await bank.logout(refresh);
      } catch (_) {}
    }
    await session.clear();
    notifyListeners();
  }
}
