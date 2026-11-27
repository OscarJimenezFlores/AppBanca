import 'dart:math';

double haversineKm(double lat1, double lon1, double lat2, double lon2) {
  for (final value in [lat1, lon1, lat2, lon2]) {
    if (value.isNaN || value.isInfinite) {
      throw ArgumentError('coordenada no finita');
    }
  }
  if (lat1.abs() > 90 || lat2.abs() > 90) {
    throw ArgumentError('latitud fuera de rango');
  }
  if (lon1.abs() > 180 || lon2.abs() > 180) {
    throw ArgumentError('longitud fuera de rango');
  }
  const radius = 6371.0;
  final p1 = lat1 * pi / 180;
  final p2 = lat2 * pi / 180;
  final dPhi = (lat2 - lat1) * pi / 180;
  final dLambda = (lon2 - lon1) * pi / 180;
  final a = pow(sin(dPhi / 2), 2) + cos(p1) * cos(p2) * pow(sin(dLambda / 2), 2);
  return 2 * radius * asin(sqrt(a));
}
