import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../../app/app_state.dart';
import '../../core/widgets.dart';
import '../../domain/validators.dart';

class RegisterPage extends StatefulWidget {
  const RegisterPage({super.key});

  @override
  State<RegisterPage> createState() => _RegisterPageState();
}

class _RegisterPageState extends State<RegisterPage> {
  final _names = TextEditingController();
  final _paternal = TextEditingController();
  final _maternal = TextEditingController();
  final _dni = TextEditingController();
  final _phone = TextEditingController();
  final _email = TextEditingController();
  final _password = TextEditingController();
  final _confirm = TextEditingController();
  bool _accepted = false;
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
    for (final controller in [_names, _paternal, _maternal, _dni, _phone, _email, _password, _confirm]) {
      controller.dispose();
    }
    super.dispose();
  }

  Future<void> _submit() async {
    final errors = <String>[
      if (nameError(_names.text, 'Los nombres') != null) nameError(_names.text, 'Los nombres')!,
      if (nameError(_paternal.text, 'El apellido paterno') != null) nameError(_paternal.text, 'El apellido paterno')!,
      if (nameError(_maternal.text, 'El apellido materno') != null) nameError(_maternal.text, 'El apellido materno')!,
      if (dniError(_dni.text.trim()) != null) dniError(_dni.text.trim())!,
      if (phoneError(_phone.text.trim()) != null) phoneError(_phone.text.trim())!,
      if (emailError(_email.text.trim()) != null) emailError(_email.text.trim())!,
      ...passwordErrors(_password.text),
      if (_password.text != _confirm.text) 'La confirmación no coincide.',
      if (!_accepted) 'Debe aceptar que este es un entorno de laboratorio.',
    ];
    if (errors.isNotEmpty) {
      setState(() => _error = errors.join('\n'));
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final result = await context.read<AppState>().bank.register({
        'dni': _dni.text.trim(),
        'email': _email.text.trim(),
        'phone': _phone.text.trim(),
        'given_names': _names.text.trim(),
        'paternal_surname': _paternal.text.trim(),
        'maternal_surname': _maternal.text.trim(),
        'password': _password.text,
      });
      if (!mounted) {
        return;
      }
      await context.read<AppState>().enter(result);
      if (mounted) {
        Navigator.of(context).pop();
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
      appBar: AppBar(title: const Text('Nueva cuenta')),
      body: ListView(
        padding: const EdgeInsets.all(24),
        children: [
          TextField(controller: _names, textCapitalization: TextCapitalization.words, decoration: const InputDecoration(labelText: 'Nombres')),
          const SizedBox(height: 12),
          TextField(controller: _paternal, textCapitalization: TextCapitalization.words, decoration: const InputDecoration(labelText: 'Apellido paterno')),
          const SizedBox(height: 12),
          TextField(controller: _maternal, textCapitalization: TextCapitalization.words, decoration: const InputDecoration(labelText: 'Apellido materno')),
          const SizedBox(height: 12),
          DigitField(controller: _dni, label: 'DNI', maxLength: 8),
          const SizedBox(height: 12),
          DigitField(controller: _phone, label: 'Celular', maxLength: 9),
          const SizedBox(height: 12),
          TextField(controller: _email, keyboardType: TextInputType.emailAddress, decoration: const InputDecoration(labelText: 'Correo')),
          const SizedBox(height: 12),
          TextField(controller: _password, obscureText: true, decoration: const InputDecoration(labelText: 'Clave')),
          const SizedBox(height: 12),
          TextField(controller: _confirm, obscureText: true, decoration: const InputDecoration(labelText: 'Confirmar clave')),
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            value: _accepted,
            onChanged: (value) => setState(() => _accepted = value ?? false),
            title: const Text('Entiendo que AndesBank es un laboratorio y no un banco.'),
          ),
          ErrorNote(_error),
          PrimaryButton(label: 'Crear cuenta', loading: _loading, onPressed: _submit),
        ],
      ),
    );
  }
}
