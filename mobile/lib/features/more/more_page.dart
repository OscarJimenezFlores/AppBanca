import 'package:material_ui/material_ui.dart';
import 'package:geolocator/geolocator.dart';
import 'package:provider/provider.dart';
import 'package:qr_flutter/qr_flutter.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../app/app_state.dart';
import '../../core/theme.dart';
import '../../core/widgets.dart';
import '../../domain/validators.dart';
import '../../types/models.dart';

class MorePage extends StatelessWidget {
  const MorePage({super.key});

  @override
  Widget build(BuildContext context) {
    final profile = context.watch<AppState>().session.profile;
    return Scaffold(
      appBar: AppBar(title: const Text('Más'), actions: const [EyeButton()]),
      body: ListView(
        children: [
          ListTile(title: Text(profile?.fullName ?? ''), subtitle: Text(profile?.email ?? '')),
          ListTile(
            leading: const Icon(Icons.shield_outlined),
            title: const Text('Doble factor'),
            subtitle: Text(profile?.totpEnabled == true ? 'Activo' : 'Desactivado'),
            onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const SecurityPage())),
          ),
          ListTile(
            leading: const Icon(Icons.place_outlined),
            title: const Text('Agencias y cajeros'),
            onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const BranchesPage())),
          ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Cerrar sesión'),
            onTap: () => context.read<AppState>().exit(),
          ),
        ],
      ),
    );
  }
}

class SecurityPage extends StatefulWidget {
  const SecurityPage({super.key});

  @override
  State<SecurityPage> createState() => _SecurityPageState();
}

class _SecurityPageState extends State<SecurityPage> {
  TotpSetup? _setup;
  final _code = TextEditingController();
  final _password = TextEditingController();
  String? _error;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    initialize();
  }

  void initialize() {}

  @override
  void dispose() {
    _code.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _begin() async {
    setState(() => _loading = true);
    try {
      final setup = await context.read<AppState>().bank.setupTotp();
      setState(() => _setup = setup);
    } catch (error) {
      setState(() => _error = error.toString());
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _confirm() async {
    final problem = otpError(_code.text.trim());
    if (problem != null) {
      setState(() => _error = problem);
      return;
    }
    try {
      final app = context.read<AppState>();
      await app.bank.confirmTotp(_code.text.trim());
      final profile = await app.bank.me();
      if (!mounted) {
        return;
      }
      app.rememberProfile(profile);
      setState(() => _error = null);
    } catch (error) {
      setState(() => _error = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final enabled = context.watch<AppState>().session.profile?.totpEnabled == true;
    return Scaffold(
      appBar: AppBar(title: const Text('Doble factor')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          const Text(
            'AndesBank usa TOTP, el mismo estándar que Microsoft Authenticator, Google Authenticator y Authy. En Microsoft Authenticator: + → Otra cuenta → escanear el código.',
            style: TextStyle(height: 1.4),
          ),
          const SizedBox(height: 8),
          const Text(
            'Ocultar el saldo en Inicio es una preferencia visual de este teléfono. El API sigue enviando el monto.',
            style: TextStyle(color: AppColors.muted, height: 1.4),
          ),
          const SizedBox(height: 16),
          if (!enabled) PrimaryButton(label: 'Generar código', loading: _loading, onPressed: _begin),
          if (_setup != null) ...[
            const SizedBox(height: 16),
            Center(child: QrImageView(data: _setup!.otpauthUri, size: 200, backgroundColor: Colors.white)),
            const SizedBox(height: 8),
            SelectableText(_setup!.secret, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            DigitField(controller: _code, label: 'Código de confirmación', maxLength: 6),
            const SizedBox(height: 12),
            PrimaryButton(label: 'Activar', onPressed: _confirm),
          ],
          if (enabled) ...[
            const Text('El factor ya está activo. Para apagarlo hace falta la clave y un código vigente.'),
            const SizedBox(height: 12),
            TextField(controller: _password, obscureText: true, decoration: const InputDecoration(labelText: 'Clave')),
            const SizedBox(height: 12),
            DigitField(controller: _code, label: 'Código', maxLength: 6),
            const SizedBox(height: 12),
            PrimaryButton(
              label: 'Desactivar',
              onPressed: () async {
                final app = context.read<AppState>();
                try {
                  await app.bank.disableTotp(_password.text, _code.text.trim());
                  final profile = await app.bank.me();
                  if (!mounted) {
                    return;
                  }
                  app.rememberProfile(profile);
                } catch (error) {
                  setState(() => _error = error.toString());
                }
              },
            ),
          ],
          ErrorNote(_error),
        ],
      ),
    );
  }
}

class BranchesPage extends StatefulWidget {
  const BranchesPage({super.key});

  @override
  State<BranchesPage> createState() => _BranchesPageState();
}

class _BranchesPageState extends State<BranchesPage> {
  List<BranchOffice> _branches = [];
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => initialize());
  }

  Future<void> initialize() async {
    final app = context.read<AppState>();
    double? latitude;
    double? longitude;
    try {
      var permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
      }
      if (permission == LocationPermission.always || permission == LocationPermission.whileInUse) {
        final position = await Geolocator.getCurrentPosition();
        latitude = position.latitude;
        longitude = position.longitude;
      }
    } catch (_) {
      latitude = null;
    }
    try {
      final branches = await app.bank.branches(latitude: latitude, longitude: longitude);
      if (mounted) {
        setState(() => _branches = branches);
      }
    } catch (error) {
      setState(() => _error = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Agencias')),
      body: ListView(
        children: [
          if (_error != null) Padding(padding: const EdgeInsets.all(16), child: ErrorNote(_error)),
          for (final branch in _branches)
            ListTile(
              title: Text(branch.name),
              subtitle: Text('${branch.address}, ${branch.district}\n${branch.hours}${branch.distanceKm == null ? '' : '\n${branch.distanceKm!.toStringAsFixed(1)} km'}'),
              isThreeLine: true,
              trailing: const Icon(Icons.map_outlined),
              onTap: () => launchUrl(Uri.parse('https://www.openstreetmap.org/?mlat=${branch.latitude}&mlon=${branch.longitude}#map=17/${branch.latitude}/${branch.longitude}')),
            ),
        ],
      ),
    );
  }
}
