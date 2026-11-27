import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../../app/app_state.dart';
import '../../core/widgets.dart';
import '../../domain/validators.dart';
import '../../types/models.dart';

class OtpPage extends StatefulWidget {
  const OtpPage({super.key, required this.challengeToken});

  final String challengeToken;

  @override
  State<OtpPage> createState() => _OtpPageState();
}

class _OtpPageState extends State<OtpPage> {
  final _code = TextEditingController();
  bool _loading = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    initialize();
  }

  void initialize() {}

  @override
  void dispose() {
    _code.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    final problem = otpError(_code.text.trim());
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await context.read<AppState>().bank.verifyOtp(widget.challengeToken, _code.text.trim());
      if (mounted) {
        Navigator.of(context).pop<LoginResult>(result);
      }
    } catch (error) {
      setState(() => _error = error.toString());
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Verificación')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          const Text('Ingrese el código de 6 dígitos de Microsoft Authenticator, o de otra aplicación TOTP.', style: TextStyle(height: 1.4)),
          const SizedBox(height: 20),
          DigitField(controller: _code, label: 'Código', maxLength: 6),
          const SizedBox(height: 16),
          ErrorNote(_error),
          PrimaryButton(label: 'Confirmar', loading: _loading, onPressed: _submit),
        ],
      ),
    );
  }
}
