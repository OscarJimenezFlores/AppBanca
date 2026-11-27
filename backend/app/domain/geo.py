from __future__ import annotations

import math


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    for value in (lat1, lon1, lat2, lon2):
        if not math.isfinite(value):
            raise ValueError("coordenada no finita")
    if not -90 <= lat1 <= 90 or not -90 <= lat2 <= 90:
        raise ValueError("latitud fuera de rango")
    if not -180 <= lon1 <= 180 or not -180 <= lon2 <= 180:
        raise ValueError("longitud fuera de rango")
    radius = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(a))
