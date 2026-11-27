from __future__ import annotations

from app.domain.catalog import BRANCHES
from app.domain.errors import DomainError
from app.domain.geo import haversine_km
from app.types.entities import Branch


def list_branches(latitude: float | None, longitude: float | None) -> list[dict[str, object]]:
    if (latitude is None) != (longitude is None):
        raise DomainError("VALIDATION", "Envíe latitud y longitud juntas, o ninguna.")
    rows: list[dict[str, object]] = []
    for branch in BRANCHES:
        rows.append(_row(branch, latitude, longitude))
    if latitude is not None and longitude is not None:
        rows.sort(key=lambda item: float(item["distance_km"]))  # type: ignore[arg-type]
    return rows


def _row(branch: Branch, latitude: float | None, longitude: float | None) -> dict[str, object]:
    distance: float | None = None
    if latitude is not None and longitude is not None:
        try:
            distance = round(haversine_km(latitude, longitude, branch.latitude, branch.longitude), 2)
        except ValueError as exc:
            raise DomainError("VALIDATION", "La coordenada está fuera de rango.") from exc
    return {
        "id": branch.id,
        "name": branch.name,
        "kind": branch.kind,
        "address": branch.address,
        "district": branch.district,
        "city": branch.city,
        "latitude": branch.latitude,
        "longitude": branch.longitude,
        "hours": branch.hours,
        "phone": branch.phone,
        "distance_km": distance,
    }
