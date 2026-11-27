import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../../app/app_state.dart';
import '../../core/theme.dart';
import '../../core/widgets.dart';
import '../../types/models.dart';
import '../../types/money.dart';

class AccountPage extends StatelessWidget {
  const AccountPage({super.key, required this.account});

  final BankAccount account;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(account.alias), actions: const [EyeButton()]),
      body: FutureBuilder<List<Movement>>(
        future: context.read<AppState>().bank.movements(account.id),
        builder: (context, snapshot) {
          return ListView(
            padding: const EdgeInsets.all(20),
            children: [
              Text(account.productLabel, style: const TextStyle(color: AppColors.muted)),
              const SizedBox(height: 8),
              BalanceText(account.availableBalance, style: const TextStyle(fontSize: 36, fontWeight: FontWeight.w700, color: AppColors.navy)),
              const SizedBox(height: 16),
              _line('Cuenta', account.number),
              _line('CCI', account.cciFormatted),
              const SizedBox(height: 16),
              const Text('Movimientos', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
              if (snapshot.connectionState != ConnectionState.done) const LinearProgressIndicator(),
              if (snapshot.hasError) ErrorNote(snapshot.error.toString()),
              for (final movement in snapshot.data ?? [])
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  title: Text(movement.concept),
                  subtitle: Text(formatLima(movement.occurredAt)),
                  trailing: BalanceText(
                    movement.direction == 'credit' ? movement.amount : '-${movement.amount}',
                    style: TextStyle(
                      color: movement.direction == 'credit' ? AppColors.positive : AppColors.negative,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ),
            ],
          );
        },
      ),
    );
  }

  Widget _line(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(width: 70, child: Text(label, style: const TextStyle(color: AppColors.muted))),
          Expanded(child: Text(value)),
        ],
      ),
    );
  }
}
