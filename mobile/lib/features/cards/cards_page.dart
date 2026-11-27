import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../../app/app_state.dart';
import '../../core/theme.dart';
import '../../core/widgets.dart';
import '../../types/models.dart';

class CardsPage extends StatefulWidget {
  const CardsPage({super.key});

  @override
  State<CardsPage> createState() => _CardsPageState();
}

class _CardsPageState extends State<CardsPage> {
  List<CardProduct> _cards = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => initialize());
  }

  Future<void> initialize() async {
    setState(() => _loading = true);
    try {
      final cards = await context.read<AppState>().bank.cards();
      if (mounted) {
        setState(() => _cards = cards);
      }
    } catch (error) {
      setState(() => _error = error.toString());
    } finally {
      if (mounted) {
        setState(() => _loading = false);
      }
    }
  }

  Future<void> _toggle(CardProduct card) async {
    try {
      final updated = await context.read<AppState>().bank.setBlocked(card.id, card.status != 'blocked');
      setState(() {
        _cards = [for (final item in _cards) item.id == updated.id ? updated : item];
      });
    } catch (error) {
      setState(() => _error = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Tarjetas')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                ErrorNote(_error),
                for (final card in _cards)
                  Container(
                    margin: const EdgeInsets.only(bottom: 14),
                    padding: const EdgeInsets.all(18),
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(22),
                      gradient: const LinearGradient(colors: [AppColors.navy, AppColors.navySoft]),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(card.brand.toUpperCase(), style: const TextStyle(color: AppColors.gold, letterSpacing: 1.4)),
                        const SizedBox(height: 18),
                        Text(card.panMasked, style: const TextStyle(color: Colors.white, fontSize: 20, letterSpacing: 1.2)),
                        const SizedBox(height: 12),
                        Text(card.holderName, style: const TextStyle(color: Colors.white)),
                        Text('Vence ${card.expiry}${card.expired ? ' · vencida' : ''}', style: const TextStyle(color: Color(0xFFD5D0C8))),
                        SwitchListTile(
                          contentPadding: EdgeInsets.zero,
                          value: card.status != 'blocked',
                          activeThumbColor: AppColors.gold,
                          title: Text(card.status == 'blocked' ? 'Bloqueada' : 'Activa', style: const TextStyle(color: Colors.white)),
                          onChanged: (_) => _toggle(card),
                        ),
                      ],
                    ),
                  ),
              ],
            ),
    );
  }
}
