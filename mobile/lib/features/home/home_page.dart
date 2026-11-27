import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../../app/app_state.dart';
import '../../core/theme.dart';
import '../../core/widgets.dart';
import '../../types/models.dart';
import '../../types/money.dart';
import '../accounts/account_page.dart';

class HomeViewModel extends ChangeNotifier {
  bool loading = true;
  String? error;
  List<BankAccount> accounts = [];
  List<Movement> recent = [];

  Future<void> initialize(AppState app) async {
    loading = true;
    error = null;
    notifyListeners();
    try {
      accounts = await app.bank.accounts();
      if (accounts.isNotEmpty) {
        recent = await app.bank.movements(accounts.first.id);
      }
    } catch (caught) {
      error = caught.toString();
    } finally {
      loading = false;
      notifyListeners();
    }
  }
}

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _model = HomeViewModel();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _model.initialize(context.read<AppState>()));
  }

  @override
  void dispose() {
    _model.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final profile = context.watch<AppState>().session.profile;
    return AnimatedBuilder(
      animation: _model,
      builder: (context, _) {
        return Scaffold(
          body: RefreshIndicator(
            onRefresh: () => _model.initialize(context.read<AppState>()),
            child: ListView(
              padding: const EdgeInsets.only(bottom: 24),
              children: [
                _Header(name: profile?.firstName ?? ''),
                if (_model.loading) const Padding(padding: EdgeInsets.all(32), child: Center(child: CircularProgressIndicator())),
                if (_model.error != null) Padding(padding: const EdgeInsets.all(24), child: ErrorNote(_model.error)),
                if (!_model.loading && _model.accounts.isNotEmpty) ...[
                  SizedBox(
                    height: 168,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      itemCount: _model.accounts.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 12),
                      itemBuilder: (context, index) {
                        final account = _model.accounts[index];
                        return _AccountCard(
                          account: account,
                          onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => AccountPage(account: account))),
                        );
                      },
                    ),
                  ),
                  const Padding(
                    padding: EdgeInsets.fromLTRB(24, 22, 24, 8),
                    child: Text('Movimientos', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                  ),
                  for (final movement in _model.recent.take(8)) _MovementTile(movement: movement),
                ],
              ],
            ),
          ),
        );
      },
    );
  }
}

class _Header extends StatelessWidget {
  const _Header({required this.name});

  final String name;

  @override
  Widget build(BuildContext context) {
    final hour = DateTime.now().toUtc();
    return Container(
      margin: const EdgeInsets.fromLTRB(16, 16, 16, 18),
      padding: const EdgeInsets.fromLTRB(20, 18, 8, 20),
      decoration: BoxDecoration(color: AppColors.navy, borderRadius: BorderRadius.circular(28)),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const MountainMark(),
              const Spacer(),
              const EyeButton(light: true),
            ],
          ),
          Text('${greetingFor(hour)}, $name', style: const TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          const Text('Saldos de la sesión de laboratorio', style: TextStyle(color: Color(0xFFD5D0C8))),
        ],
      ),
    );
  }
}

class _AccountCard extends StatelessWidget {
  const _AccountCard({required this.account, required this.onTap});

  final BankAccount account;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(22),
      child: InkWell(
        borderRadius: BorderRadius.circular(22),
        onTap: onTap,
        child: Container(
          width: 250,
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(borderRadius: BorderRadius.circular(22), border: Border.all(color: AppColors.line)),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(account.alias, style: const TextStyle(fontWeight: FontWeight.w700)),
              Text(account.productLabel, style: const TextStyle(color: AppColors.muted, fontSize: 12)),
              const Spacer(),
              BalanceText(account.availableBalance, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w700, color: AppColors.navy)),
              const SizedBox(height: 6),
              Text(account.numberMasked, style: const TextStyle(letterSpacing: 0.6)),
            ],
          ),
        ),
      ),
    );
  }
}

class _MovementTile extends StatelessWidget {
  const _MovementTile({required this.movement});

  final Movement movement;

  @override
  Widget build(BuildContext context) {
    final credit = movement.direction == 'credit';
    return ListTile(
      title: Text(movement.concept),
      subtitle: Text('${movement.counterpartyName} · ${formatLima(movement.occurredAt)}'),
      trailing: BalanceText(
        '${credit ? '' : '-'}${movement.amount}',
        style: TextStyle(color: credit ? AppColors.positive : AppColors.negative, fontWeight: FontWeight.w700),
      ),
    );
  }
}
