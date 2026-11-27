import 'package:material_ui/material_ui.dart';

import '../cards/cards_page.dart';
import '../home/home_page.dart';
import '../more/more_page.dart';
import '../payment/payment_page.dart';
import '../transfer/transfer_page.dart';

class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _index = 0;

  @override
  void initState() {
    super.initState();
    initialize();
  }

  void initialize() {}

  @override
  Widget build(BuildContext context) {
    final pages = const [HomePage(), TransferPage(), PaymentPage(), CardsPage(), MorePage()];
    return Scaffold(
      body: IndexedStack(index: _index, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (value) => setState(() => _index = value),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Inicio'),
          NavigationDestination(icon: Icon(Icons.swap_horiz), label: 'Transferir'),
          NavigationDestination(icon: Icon(Icons.receipt_long_outlined), label: 'Pagar'),
          NavigationDestination(icon: Icon(Icons.credit_card), label: 'Tarjetas'),
          NavigationDestination(icon: Icon(Icons.menu), label: 'Más'),
        ],
      ),
    );
  }
}
