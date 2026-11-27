import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../features/auth/login_page.dart';
import '../features/shell/main_shell.dart';
import 'app_state.dart';

class AndesApp extends StatefulWidget {
  const AndesApp({super.key, this.state});

  final AppState? state;

  @override
  State<AndesApp> createState() => _AndesAppState();
}

class _AndesAppState extends State<AndesApp> {
  late final AppState appState;
  late final BalanceVisibility visibility;

  @override
  void initState() {
    super.initState();
    appState = widget.state ?? AppState();
    visibility = BalanceVisibility();
    WidgetsBinding.instance.addPostFrameCallback((_) => _boot());
  }

  Future<void> _boot() async {
    await visibility.initialize();
    await appState.initialize();
  }

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<AppState>.value(value: appState),
        ChangeNotifierProvider<BalanceVisibility>.value(value: visibility),
      ],
      child: MaterialApp(
        title: 'AndesBank',
        debugShowCheckedModeBanner: false,
        theme: buildTheme(),
        home: const _Gate(),
      ),
    );
  }
}

class _Gate extends StatelessWidget {
  const _Gate();

  @override
  Widget build(BuildContext context) {
    final state = context.watch<AppState>();
    if (!state.ready) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }
    if (state.session.accessToken == null) {
      return const LoginPage();
    }
    return const MainShell();
  }
}
