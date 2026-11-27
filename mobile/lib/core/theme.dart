import 'package:material_ui/material_ui.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AppColors {
  static const ink = Color(0xFF142033);
  static const navy = Color(0xFF0E2744);
  static const navySoft = Color(0xFF1B3A5F);
  static const gold = Color(0xFFB8925A);
  static const paper = Color(0xFFF6F3EE);
  static const card = Colors.white;
  static const line = Color(0xFFE6E0D6);
  static const positive = Color(0xFF0E7A58);
  static const negative = Color(0xFF9E2A24);
  static const muted = Color(0xFF667085);
}

ThemeData buildTheme() {
  final base = ThemeData(
    useMaterial3: true,
    brightness: Brightness.light,
    scaffoldBackgroundColor: AppColors.paper,
    colorScheme: ColorScheme.fromSeed(
      seedColor: AppColors.navy,
      primary: AppColors.navy,
      secondary: AppColors.gold,
      surface: AppColors.card,
    ),
    dividerColor: AppColors.line,
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      border: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.line)),
      enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.line)),
      focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.navy, width: 1.4)),
      errorBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(14), borderSide: const BorderSide(color: AppColors.negative)),
    ),
  );
  return base.copyWith(
    appBarTheme: const AppBarTheme(
      backgroundColor: AppColors.paper,
      foregroundColor: AppColors.ink,
      elevation: 0,
      centerTitle: false,
    ),
    navigationBarTheme: NavigationBarThemeData(
      backgroundColor: Colors.white,
      indicatorColor: AppColors.gold.withValues(alpha: 0.28),
      labelTextStyle: WidgetStateProperty.all(const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
    ),
  );
}

class BalanceVisibility extends ChangeNotifier {
  bool hidden = false;

  Future<void> initialize() async {
    final preferences = await SharedPreferences.getInstance();
    hidden = preferences.getBool('hide_balances') ?? false;
    notifyListeners();
  }

  Future<void> toggle() async {
    hidden = !hidden;
    notifyListeners();
    final preferences = await SharedPreferences.getInstance();
    await preferences.setBool('hide_balances', hidden);
  }
}
