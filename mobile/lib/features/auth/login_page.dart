import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../../app/app_state.dart';
import '../../core/theme.dart';
import '../../core/widgets.dart';
import '../../domain/validators.dart';
import '../../types/models.dart';
import 'otp_page.dart';
import 'register_page.dart';

class LoginViewModel extends ChangeNotifier {
  bool dniMode = true;
  bool loading = false;
  bool obscure = true;
  String? error;
  LoginResult? result;

  void initialize() {}

  void setMode(bool dni) {
    dniMode = dni;
    error = null;
    notifyListeners();
  }

  void toggleObscure() {
    obscure = !obscure;
    notifyListeners();
  }

  void beginRequest() {
    loading = true;
    error = null;
    notifyListeners();
  }

  void fail(String message) {
    loading = false;
    error = message;
    notifyListeners();
  }

  Future<bool> submit(String identifier, String password) async {
    final problem = dniMode ? dniError(identifier.trim()) : emailError(identifier.trim());
    if (problem != null) {
      error = problem;
      notifyListeners();
      return false;
    }
    if (password.isEmpty) {
      error = 'Ingrese la clave.';
      notifyListeners();
      return false;
    }
    return true;
  }
}

class LoginPage extends StatefulWidget {
  const LoginPage({super.key});

  @override
  State<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends State<LoginPage> {
  final _model = LoginViewModel();
  final _identifier = TextEditingController();
  final _password = TextEditingController();

  @override
  void initState() {
    super.initState();
    _model.initialize();
  }

  @override
  void dispose() {
    _model.dispose();
    _identifier.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final valid = await _model.submit(_identifier.text, _password.text);
    if (!valid || !mounted) {
      return;
    }
    _model.beginRequest();
    try {
      final bank = context.read<AppState>().bank;
      final result = await bank.login(_identifier.text.trim(), _password.text);
      if (!mounted) {
        return;
      }
      if (result.requiresOtp) {
        final confirmed = await Navigator.of(context).push<LoginResult>(
          MaterialPageRoute(builder: (_) => OtpPage(challengeToken: result.challengeToken ?? '')),
        );
        if (confirmed != null && mounted) {
          await context.read<AppState>().enter(confirmed);
        }
      } else {
        await context.read<AppState>().enter(result);
      }
    } catch (error) {
      if (mounted) {
        _model.fail(error.toString());
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _model,
      builder: (context, _) {
        return Scaffold(
          body: SafeArea(
            child: ListView(
              padding: const EdgeInsets.fromLTRB(24, 28, 24, 24),
              children: [
                const MountainMark(size: 64),
                const SizedBox(height: 18),
                const Text('AndesBank', style: TextStyle(fontSize: 34, fontWeight: FontWeight.w700, color: AppColors.navy)),
                const Text('Banca de laboratorio · SI-988', style: TextStyle(color: AppColors.muted)),
                const SizedBox(height: 28),
                SegmentedButton<bool>(
                  segments: const [
                    ButtonSegment(value: true, label: Text('DNI')),
                    ButtonSegment(value: false, label: Text('Correo')),
                  ],
                  selected: {_model.dniMode},
                  onSelectionChanged: (value) => _model.setMode(value.first),
                ),
                const SizedBox(height: 16),
                if (_model.dniMode)
                  DigitField(controller: _identifier, label: 'DNI', maxLength: 8)
                else
                  TextField(
                    controller: _identifier,
                    keyboardType: TextInputType.emailAddress,
                    autocorrect: false,
                    decoration: const InputDecoration(labelText: 'Correo'),
                  ),
                const SizedBox(height: 12),
                TextField(
                  controller: _password,
                  obscureText: _model.obscure,
                  decoration: InputDecoration(
                    labelText: 'Clave',
                    suffixIcon: IconButton(
                      onPressed: _model.toggleObscure,
                      icon: Icon(_model.obscure ? Icons.visibility_outlined : Icons.visibility_off_outlined),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                ErrorNote(_model.error),
                PrimaryButton(label: 'Entrar', loading: _model.loading, onPressed: _submit),
                TextButton(
                  onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const RegisterPage())),
                  child: const Text('Crear una cuenta de laboratorio'),
                ),
                const SizedBox(height: 12),
                const Text(
                  'No es una entidad supervisada. Los saldos y los movimientos son de demostración.',
                  style: TextStyle(color: AppColors.muted, fontSize: 12),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
