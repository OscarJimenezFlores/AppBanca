import 'package:material_ui/material_ui.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../types/money.dart';

class MountainMark extends StatelessWidget {
  const MountainMark({super.key, this.size = 42});

  final double size;

  @override
  Widget build(BuildContext context) {
    return CustomPaint(size: Size(size, size * 0.72), painter: _MountainPainter());
  }
}

class _MountainPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final gold = Paint()..color = AppColors.gold;
    final navy = Paint()..color = Colors.white;
    final peak = Path()
      ..moveTo(0, size.height)
      ..lineTo(size.width * 0.38, size.height * 0.18)
      ..lineTo(size.width * 0.62, size.height)
      ..close();
    final far = Path()
      ..moveTo(size.width * 0.28, size.height)
      ..lineTo(size.width * 0.66, size.height * 0.34)
      ..lineTo(size.width, size.height)
      ..close();
    canvas.drawPath(far, gold);
    canvas.drawPath(peak, navy);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class BalanceText extends StatelessWidget {
  const BalanceText(this.raw, {super.key, this.style, this.hidden});

  final String raw;
  final TextStyle? style;
  final bool? hidden;

  @override
  Widget build(BuildContext context) {
    final hide = hidden ?? context.watch<BalanceVisibility>().hidden;
    final text = hide ? Money.hidden : Money.parse(raw).signed;
    return Text(text, style: style);
  }
}

class EyeButton extends StatelessWidget {
  const EyeButton({super.key, this.light = false});

  final bool light;

  @override
  Widget build(BuildContext context) {
    final visibility = context.watch<BalanceVisibility>();
    return IconButton(
      tooltip: visibility.hidden ? 'Mostrar saldos' : 'Ocultar saldos',
      onPressed: () => context.read<BalanceVisibility>().toggle(),
      icon: Icon(
        visibility.hidden ? Icons.visibility_off_outlined : Icons.visibility_outlined,
        color: light ? Colors.white : AppColors.ink,
      ),
    );
  }
}

class PrimaryButton extends StatelessWidget {
  const PrimaryButton({super.key, required this.label, required this.onPressed, this.loading = false});

  final String label;
  final VoidCallback? onPressed;
  final bool loading;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 52,
      child: FilledButton(
        style: FilledButton.styleFrom(backgroundColor: AppColors.navy, shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14))),
        onPressed: loading ? null : onPressed,
        child: loading
            ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
            : Text(label),
      ),
    );
  }
}

class MoneyField extends StatelessWidget {
  const MoneyField({super.key, required this.controller, this.label = 'Monto', this.error});

  final TextEditingController controller;
  final String label;
  final String? error;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      inputFormatters: [FilteringTextInputFormatter.allow(RegExp(r'[0-9.]')), _MoneyFormatter()],
      decoration: InputDecoration(labelText: label, prefixText: 'S/ ', errorText: error),
    );
  }
}

class DigitField extends StatelessWidget {
  const DigitField({
    super.key,
    required this.controller,
    required this.label,
    required this.maxLength,
    this.error,
    this.obscure = false,
  });

  final TextEditingController controller;
  final String label;
  final int maxLength;
  final String? error;
  final bool obscure;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      keyboardType: TextInputType.number,
      obscureText: obscure,
      maxLength: maxLength,
      inputFormatters: [FilteringTextInputFormatter.digitsOnly],
      decoration: InputDecoration(labelText: label, counterText: '', errorText: error),
    );
  }
}

class _MoneyFormatter extends TextInputFormatter {
  @override
  TextEditingValue formatEditUpdate(TextEditingValue oldValue, TextEditingValue newValue) {
    final text = sanitizeMoney(newValue.text);
    return TextEditingValue(text: text, selection: TextSelection.collapsed(offset: text.length));
  }
}

class ErrorNote extends StatelessWidget {
  const ErrorNote(this.message, {super.key});

  final String? message;

  @override
  Widget build(BuildContext context) {
    if (message == null || message!.isEmpty) {
      return const SizedBox.shrink();
    }
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(message!, style: const TextStyle(color: AppColors.negative)),
    );
  }
}
