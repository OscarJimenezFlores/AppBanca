import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../../app/app_state.dart';
import '../../core/theme.dart';
import '../../core/widgets.dart';
import '../../domain/validators.dart';
import '../../types/models.dart';

class TransferPage extends StatefulWidget {
  const TransferPage({super.key});

  @override
  State<TransferPage> createState() => _TransferPageState();
}

class _TransferPageState extends State<TransferPage> {
  final _destination = TextEditingController();
  final _holder = TextEditingController();
  final _amount = TextEditingController();
  final _concept = TextEditingController(text: 'Transferencia');
  final _otp = TextEditingController();
  List<BankAccount> _accounts = [];
  List<Beneficiary> _people = [];
  String? _originId;
  bool _cci = false;
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
    final people = await bank.beneficiaries();
    if (!mounted) {
      return;
    }
    setState(() {
      _accounts = accounts.where((item) => item.canDebit).toList();
      _people = people;
      _originId ??= _accounts.isEmpty ? null : _accounts.first.id;
    });
  }

  @override
  void dispose() {
    _destination.dispose();
    _holder.dispose();
    _amount.dispose();
    _concept.dispose();
    _otp.dispose();
    super.dispose();
  }

  Future<void> _send() async {
    final amountProblem = amountError(_amount.text.trim(), ceiling: '10000.00');
    final destinationProblem = _cci ? cciError(_destination.text.trim()) : accountNumberError(_destination.text.trim());
    final concept = _concept.text.trim();
    final profile = context.read<AppState>().session.profile;
    final needsOtp = profile?.totpEnabled == true && _centsAtLeast(_amount.text.trim(), 50000);
    final errors = <String>[
      if (_originId == null) 'Elija la cuenta de origen.',
      if (destinationProblem != null) destinationProblem,
      if (amountProblem != null) amountProblem,
      if (concept.isEmpty || concept.length > 80) 'El concepto es obligatorio y admite 80 caracteres.',
      if (_cci && nameError(_holder.text, 'El titular') != null) nameError(_holder.text, 'El titular')!,
      if (needsOtp && otpError(_otp.text.trim()) != null) 'Esta operación pide el código de 6 dígitos.',
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
      final body = <String, dynamic>{
        'origin_account_id': _originId,
        'amount': _amount.text.trim(),
        'concept': concept,
        if (_cci) 'destination_cci': _destination.text.trim(),
        if (_cci) 'destination_holder': _holder.text.trim(),
        if (!_cci) 'destination_account_number': _destination.text.trim(),
        if (needsOtp) 'otp_code': _otp.text.trim(),
      };
      final receipt = await context.read<AppState>().bank.transfer(body);
      if (mounted) {
        setState(() => _receipt = receipt);
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
    final needsOtp = context.watch<AppState>().session.profile?.totpEnabled == true && _centsAtLeast(_amount.text.trim(), 50000);
    return Scaffold(
      appBar: AppBar(title: const Text('Transferir'), actions: const [EyeButton()]),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          if (_accounts.isEmpty) const Text('No hay una cuenta habilitada para debitar.') else
            DropdownButtonFormField<String>(
              initialValue: _originId,
              decoration: const InputDecoration(labelText: 'Cuenta de origen'),
              items: [
                for (final account in _accounts)
                  DropdownMenuItem(value: account.id, child: Text('${account.alias} · ${account.numberMasked}')),
              ],
              onChanged: (value) => setState(() => _originId = value),
            ),
          const SizedBox(height: 12),
          SegmentedButton<bool>(
            segments: const [
              ButtonSegment(value: false, label: Text('Cuenta')),
              ButtonSegment(value: true, label: Text('CCI')),
            ],
            selected: {_cci},
            onSelectionChanged: (value) => setState(() => _cci = value.first),
          ),
          const SizedBox(height: 12),
          if (_people.isNotEmpty)
            SizedBox(
              height: 40,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: [
                  for (final person in _people)
                    Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ActionChip(
                        label: Text(person.alias),
                        onPressed: () {
                          setState(() {
                            _cci = person.cci != null;
                            _destination.text = person.accountNumber ?? person.cci ?? '';
                            _holder.text = person.holderName;
                          });
                        },
                      ),
                    ),
                ],
              ),
            ),
          const SizedBox(height: 12),
          DigitField(controller: _destination, label: _cci ? 'CCI' : 'Número de cuenta', maxLength: _cci ? 20 : 14),
          if (_cci) ...[
            const SizedBox(height: 12),
            TextField(controller: _holder, textCapitalization: TextCapitalization.words, decoration: const InputDecoration(labelText: 'Titular')),
          ],
          const SizedBox(height: 12),
          MoneyField(controller: _amount),
          const SizedBox(height: 12),
          TextField(controller: _concept, decoration: const InputDecoration(labelText: 'Concepto')),
          if (needsOtp) ...[
            const SizedBox(height: 12),
            DigitField(controller: _otp, label: 'Código del autenticador', maxLength: 6),
            const Text('Desde S/ 500.00, con el doble factor activo, la operación pide el código.', style: TextStyle(color: AppColors.muted, fontSize: 12)),
          ],
          const SizedBox(height: 16),
          ErrorNote(_error),
          PrimaryButton(label: 'Transferir', loading: _loading, onPressed: _send),
          if (_receipt != null) ...[
            const SizedBox(height: 20),
            Text('Operación ${_receipt!.operationCode}', style: const TextStyle(fontWeight: FontWeight.w700)),
            Text('${_receipt!.status} · ${_receipt!.destinationHolder}'),
            BalanceText(_receipt!.amount, style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w700)),
            if (_receipt!.commission != '0.00') Text('Comisión S/ ${_receipt!.commission}'),
          ],
        ],
      ),
    );
  }
}

bool _centsAtLeast(String raw, int cents) {
  if (sanitizePreview(raw) == null) {
    return false;
  }
  final parts = raw.split('.');
  final whole = int.parse(parts[0]);
  final fraction = parts.length == 1 ? 0 : int.parse(parts[1].padRight(2, '0'));
  return whole * 100 + fraction >= cents;
}
