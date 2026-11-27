class Money {
  const Money(this.cents);

  final int cents;

  factory Money.parse(String raw) {
    final text = raw.trim();
    final match = RegExp(r'^-?(?:0|[1-9]\d*)(?:\.\d{1,2})?$').firstMatch(text);
    if (match == null) {
      throw FormatException('Monto ilegible: $raw');
    }
    final negative = text.startsWith('-');
    final unsigned = negative ? text.substring(1) : text;
    final parts = unsigned.split('.');
    final whole = int.parse(parts[0]);
    final fraction = parts.length == 1 ? 0 : int.parse(parts[1].padRight(2, '0'));
    final cents = whole * 100 + fraction;
    return Money(negative ? -cents : cents);
  }

  String get signed {
    final negative = cents < 0;
    final absolute = cents.abs();
    final whole = absolute ~/ 100;
    final fraction = (absolute % 100).toString().padLeft(2, '0');
    final digits = whole.toString();
    final grouped = StringBuffer();
    for (var index = 0; index < digits.length; index++) {
      if (index > 0 && (digits.length - index) % 3 == 0) {
        grouped.write(',');
      }
      grouped.write(digits[index]);
    }
    return '${negative ? '-' : ''}S/ $grouped.$fraction';
  }

  static const hidden = 'S/ ••••••';
}

String sanitizeMoney(String raw) {
  final cleaned = raw.replaceAll(RegExp(r'[^0-9.]'), '');
  final dot = cleaned.indexOf('.');
  if (dot < 0) {
    return cleaned;
  }
  final whole = cleaned.substring(0, dot);
  final fraction = cleaned.substring(dot + 1).replaceAll('.', '');
  final tail = fraction.length <= 2 ? fraction : fraction.substring(0, 2);
  return '$whole.$tail';
}

String sanitizeDigits(String raw, int max) {
  final digits = raw.replaceAll(RegExp(r'\D'), '');
  if (digits.length <= max) {
    return digits;
  }
  return digits.substring(0, max);
}

String greetingFor(DateTime utc) {
  final hour = utc.toUtc().add(const Duration(hours: -5)).hour;
  if (hour < 12) {
    return 'Buenos días';
  }
  if (hour < 19) {
    return 'Buenas tardes';
  }
  return 'Buenas noches';
}

const _months = [
  'ene', 'feb', 'mar', 'abr', 'may', 'jun',
  'jul', 'ago', 'set', 'oct', 'nov', 'dic',
];

String formatLima(DateTime value) {
  final lima = value.toUtc().add(const Duration(hours: -5));
  final hour = lima.hour.toString().padLeft(2, '0');
  final minute = lima.minute.toString().padLeft(2, '0');
  return '${lima.day} ${_months[lima.month - 1]} ${lima.year} · $hour:$minute';
}
