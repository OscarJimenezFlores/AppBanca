String? dniError(String value) {
  if (!RegExp(r'^\d{8}$').hasMatch(value)) {
    return 'El DNI debe tener 8 dígitos.';
  }
  if (value == '00000000') {
    return 'El DNI no es válido.';
  }
  return null;
}

String? phoneError(String value) {
  if (!RegExp(r'^9\d{8}$').hasMatch(value)) {
    return 'El celular debe tener 9 dígitos y empezar con 9.';
  }
  return null;
}

String? emailError(String value) {
  final text = value.trim().toLowerCase();
  if (text.length > 160 || !RegExp(r'^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$').hasMatch(text)) {
    return 'El correo no tiene un formato utilizable.';
  }
  return null;
}

String? nameError(String value, String label) {
  final text = value.trim().replaceAll(RegExp(r'\s+'), ' ');
  if (value.contains(RegExp(r'[\n\r\t]'))) {
    return '$label contiene caracteres no permitidos.';
  }
  if (text.length < 2 || text.length > 80 || !RegExp(r"^[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+(?:[ '\-][A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+)*$").hasMatch(text)) {
    return '$label debe tener entre 2 y 80 letras.';
  }
  return null;
}

List<String> passwordErrors(String password) {
  final errors = <String>[];
  if (password.length < 8) {
    errors.add('La clave debe tener al menos 8 caracteres.');
  }
  if (password.length > 64) {
    errors.add('La clave no debe superar 64 caracteres.');
  }
  if (!RegExp(r'[A-Z]').hasMatch(password)) {
    errors.add('La clave debe incluir una mayúscula.');
  }
  if (!RegExp(r'[a-z]').hasMatch(password)) {
    errors.add('La clave debe incluir una minúscula.');
  }
  if (!RegExp(r'\d').hasMatch(password)) {
    errors.add('La clave debe incluir un dígito.');
  }
  if (!RegExp(r'[^A-Za-z0-9]').hasMatch(password)) {
    errors.add('La clave debe incluir un símbolo.');
  }
  if (password.toLowerCase() == 'andes.2026' || password.toLowerCase().contains('andesbank')) {
    errors.add('La clave es demasiado predecible.');
  }
  return errors;
}

String? otpError(String value) {
  if (!RegExp(r'^\d{6}$').hasMatch(value)) {
    return 'El código debe tener 6 dígitos.';
  }
  return null;
}

String? accountNumberError(String value) {
  if (!RegExp(r'^\d{14}$').hasMatch(value)) {
    return 'El número de cuenta debe tener 14 dígitos.';
  }
  return null;
}

String? cciError(String value) {
  if (!RegExp(r'^\d{20}$').hasMatch(value)) {
    return 'El CCI debe tener 20 dígitos.';
  }
  return null;
}

String? amountError(String value, {required String ceiling}) {
  final money = value.trim();
  if (sanitizePreview(money) == null) {
    return 'El monto debe escribirse con punto decimal y sin separador de miles.';
  }
  final cents = _cents(money);
  if (cents < 100) {
    return 'El mínimo es S/ 1.00.';
  }
  if (cents > _cents(ceiling)) {
    return 'El máximo por operación es S/ $ceiling.';
  }
  return null;
}

int _cents(String value) {
  final parts = value.split('.');
  final whole = int.parse(parts[0]);
  final fraction = parts.length == 1 ? 0 : int.parse(parts[1].padRight(2, '0'));
  return whole * 100 + fraction;
}

String? sanitizePreview(String value) {
  if (!RegExp(r'^(?:0|[1-9]\d*)(?:\.\d{1,2})?$').hasMatch(value)) {
    return null;
  }
  return value;
}
