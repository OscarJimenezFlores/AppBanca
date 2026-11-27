import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../../app/app_state.dart';
import '../../core/widgets.dart';
import '../../domain/validators.dart';
import '../../types/models.dart';

class PaymentPage extends StatefulWidget {
  const PaymentPage({super.key});

  @override
  State<PaymentPage> createState() => _PaymentPageState();
}

class _PaymentPageState extends State<PaymentPage> {
  final _reference = TextEditingController();
  final _amount = TextEditingController();
  final _otp = TextEditingController();
  List<BankAccount> _accounts = [];
  List<ServiceOffer> _services = [];
  String? _originId;
  String? _serviceCode;
  bool _loading = false;
  String? _error;
  TransferReceipt? _receipt;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => initialize());
  }

  Future<void> initialize() async {
    final bank = context.read<AppState>().bank;
    final accounts = await bank.accounts();
    final services = await bank.services();
    if (!mounted) {
      return;
    }
    setState(() {
      _accounts = accounts.where((item) => item.canDebit).toList();
      _services = services;
      _originId ??= _accounts.isEmpty ? null : _accounts.first.id;
      _serviceCode ??= services.isEmpty ? null : services.first.code;
    });
  }

  @override
  void dispose() {
    _reference.dispose();
    _amount.dispose();
    _otp.dispose();
    super.dispose();
  }

  ServiceOffer? get _service {
    for (final item in _services) {
      if (item.code == _serviceCode) {
        return item;
      }
    }
    return null;
  }

  Future<void> _pay() async {
    final service = _service;
    final reference = _reference.text.trim();
    final pattern = service == null ? null : RegExp(service.referencePattern);
    final needsOtp = context.read<AppState>().session.profile?.totpEnabled == true && sanitizePreview(_amount.text.trim()) != null && _atLeast500();
    final errors = <String>[
      if (_originId == null) 'Elija la cuenta de origen.',
      if (service == null) 'Elija un servicio.',
      if (pattern != null && !pattern.hasMatch(reference)) '${service?.referenceLabel ?? 'La referencia'} no tiene el formato pedido.',
      if (amountError(_amount.text.trim(), ceiling: service?.maxAmount ?? '5000.00') != null)
        amountError(_amount.text.trim(), ceiling: service?.maxAmount ?? '5000.00')!,
      if (needsOtp && otpError(_otp.text.trim()) != null) otpError(_otp.text.trim())!,
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
      final receipt = await context.read<AppState>().bank.pay({
        'origin_account_id': _originId,
        'service_code': _serviceCode,
        'reference': reference,
        'amount': _amount.text.trim(),
        if (needsOtp) 'otp_code': _otp.text.trim(),
      });
      setState(() => _receipt = receipt);
    } catch (error) {
      setState(() => _error = error.toString());
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  bool _atLeast500() {
    final parts = _amount.text.trim().split('.');
    if (parts.isEmpty || int.tryParse(parts[0]) == null) {
      return false;
    }
    final whole = int.parse(parts[0]);
    final fraction = parts.length == 1 ? 0 : int.parse(parts[1].padRight(2, '0'));
    return whole * 100 + fraction >= 50000;
  }

  @override
  Widget build(BuildContext context) {
    final service = _service;
    return Scaffold(
      appBar: AppBar(title: const Text('Pagar servicios'), actions: const [EyeButton()]),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (_accounts.isNotEmpty)
            DropdownButtonFormField<String>(
              initialValue: _originId,
              decoration: const InputDecoration(labelText: 'Cuenta'),
              items: [for (final account in _accounts) DropdownMenuItem(value: account.id, child: Text(account.alias))],
              onChanged: (value) => setState(() => _originId = value),
            ),
          const SizedBox(height: 12),
          if (_services.isNotEmpty)
            DropdownButtonFormField<String>(
              initialValue: _serviceCode,
              decoration: const InputDecoration(labelText: 'Servicio'),
              items: [for (final item in _services) DropdownMenuItem(value: item.code, child: Text(item.name))],
              onChanged: (value) => setState(() => _serviceCode = value),
            ),
          const SizedBox(height: 12),
          TextField(
            controller: _reference,
            keyboardType: TextInputType.number,
            decoration: InputDecoration(labelText: service?.referenceLabel ?? 'Referencia'),
          ),
          const SizedBox(height: 12),
          MoneyField(controller: _amount),
          if (context.watch<AppState>().session.profile?.totpEnabled == true) ...[
            const SizedBox(height: 12),
            DigitField(controller: _otp, label: 'Código, si el monto es de S/ 500 o más', maxLength: 6),
          ],
          const SizedBox(height: 16),
          ErrorNote(_error),
          PrimaryButton(label: 'Pagar', loading: _loading, onPressed: _pay),
          if (_receipt != null) ...[
            const SizedBox(height: 16),
            Text('Constancia ${_receipt!.operationCode}', style: const TextStyle(fontWeight: FontWeight.w700)),
            BalanceText(_receipt!.amount, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w700)),
          ],
        ],
      ),
    );
  }
}
