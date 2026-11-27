import 'package:flutter_test/flutter_test.dart';

import 'package:andesbank/domain/geo.dart';
import 'package:andesbank/domain/validators.dart';
import 'package:andesbank/types/money.dart';

void main() {
  test('el monto se agrupa como en una cartilla bancaria', () {
    expect(Money.parse('12847.35').signed, 'S/ 12,847.35');
    expect(Money.parse('1000').signed, 'S/ 1,000.00');
    expect(Money.parse('-25.5').signed, '-S/ 25.50');
    expect(Money.parse('0.5').signed, 'S/ 0.50');
    expect(() => Money.parse('1,500.00'), throwsFormatException);
    expect(() => Money.parse('10.555'), throwsFormatException);
  });

  test('el teclado de monto deja un solo punto y dos decimales', () {
    expect(sanitizeMoney('12a.3.99'), '12.39');
    expect(sanitizeMoney('S/ 10'), '10');
    expect(sanitizeDigits('DNI 45-821.367', 8), '45821367');
  });

  test('el saludo usa la hora de Perú, sin horario de verano', () {
    expect(greetingFor(DateTime.utc(2026, 11, 26, 14)), 'Buenos días');
    expect(greetingFor(DateTime.utc(2026, 11, 26, 18)), 'Buenas tardes');
    expect(greetingFor(DateTime.utc(2026, 11, 27, 2)), 'Buenas noches');
    expect(formatLima(DateTime.utc(2026, 11, 26, 3, 30)), '25 nov 2026 · 22:30');
  });

  test('las validaciones de captura rechazan los bordes', () {
    expect(dniError('45821367'), isNull);
    expect(dniError('00000000'), isNotNull);
    expect(dniError('1234567'), isNotNull);
    expect(phoneError('952418763'), isNull);
    expect(phoneError('052418763'), isNotNull);
    expect(emailError('maria.quispe@correo.pe'), isNull);
    expect(passwordErrors('abc').length, greaterThan(3));
    expect(passwordErrors('Clave.2026'), isEmpty);
    expect(passwordErrors('Andes.2026'), isNotEmpty);
    expect(amountError('0.50', ceiling: '10000.00'), isNotNull);
    expect(amountError('10000.01', ceiling: '10000.00'), isNotNull);
    expect(amountError('25.50', ceiling: '10000.00'), isNull);
    expect(amountError('1.500', ceiling: '10000.00'), isNotNull);
    expect(otpError('12345'), isNotNull);
    expect(accountNumberError('00110000004821'), isNull);
    expect(cciError('99800112345678901234'), isNull);
  });

  test('la distancia entre el centro y Pocollay está en el rango urbano', () {
    final distance = haversineKm(-18.01397, -70.25362, -17.99620, -70.21840);
    expect(distance, greaterThan(3));
    expect(distance, lessThan(8));
    expect(() => haversineKm(91, 0, 0, 0), throwsArgumentError);
  });
}
