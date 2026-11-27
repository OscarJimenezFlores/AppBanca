from __future__ import annotations

from decimal import Decimal

from app.domain.money import money
from app.types.entities import Branch, ServiceDefinition

SERVICES: tuple[ServiceDefinition, ...] = (
    ServiceDefinition(
        "LUZ-ANDINA",
        "Luz Andina",
        "Energía",
        "Número de suministro",
        r"^\d{7,12}$",
        money("1.00"),
        money("2000.00"),
    ),
    ServiceDefinition(
        "AGUA-TACNA",
        "Agua Tacna",
        "Agua",
        "Código de suministro",
        r"^\d{6,10}$",
        money("1.00"),
        money("1500.00"),
    ),
    ServiceDefinition(
        "MOVIL-SUR",
        "Móvil Sur",
        "Telefonía",
        "Celular",
        r"^9\d{8}$",
        money("1.00"),
        money("500.00"),
    ),
    ServiceDefinition(
        "UPTSERV",
        "Universidad Privada de Tacna",
        "Educación",
        "Código de alumno",
        r"^\d{8,10}$",
        money("1.00"),
        money("5000.00"),
    ),
    ServiceDefinition(
        "GAS-ALTIPLANO",
        "Gas Altiplano",
        "Gas",
        "Número de contrato",
        r"^\d{8,12}$",
        money("1.00"),
        money("800.00"),
    ),
)

# Coordenadas públicas de referencia, distrito de Tacna.
# No son sucursales de una entidad real.
BRANCHES: tuple[Branch, ...] = (
    Branch(
        "ag-centro",
        "Agencia Centro",
        "agencia",
        "Calle San Martín 214",
        "Tacna",
        "Tacna",
        -18.01397,
        -70.25362,
        "Lun a vie 09:00–18:00 · Sáb 09:00–13:00",
        "052-481200",
    ),
    Branch(
        "ag-mendoza",
        "Agencia Coronel Mendoza",
        "agencia",
        "Avenida Coronel Mendoza 640",
        "Tacna",
        "Tacna",
        -18.00648,
        -70.24627,
        "Lun a vie 09:00–18:00 · Sáb 09:00–13:00",
        "052-481210",
    ),
    Branch(
        "ag-upt",
        "Agencia Ciudad Universitaria",
        "agencia",
        "Campus Universidad Privada de Tacna, avenida Bolognesi",
        "Tacna",
        "Tacna",
        -18.00340,
        -70.22680,
        "Lun a vie 09:00–16:00",
        "052-481230",
    ),
    Branch(
        "ag-pocollay",
        "Agencia Pocollay",
        "agencia",
        "Avenida Celestino Vargas 1180",
        "Pocollay",
        "Tacna",
        -17.99620,
        -70.21840,
        "Lun a vie 09:00–17:00",
        "052-481240",
    ),
    Branch(
        "cj-albarracin",
        "Cajero Gregorio Albarracín",
        "cajero",
        "Avenida Municipal 520, mercado Modelo",
        "Gregorio Albarracín",
        "Tacna",
        -18.03080,
        -70.25190,
        "24 horas",
        "052-481200",
    ),
    Branch(
        "cj-parque",
        "Cajero Parque de la Locomotora",
        "cajero",
        "Avenida Grau, cuadra 6",
        "Tacna",
        "Tacna",
        -18.01210,
        -70.24980,
        "24 horas",
        "052-481200",
    ),
)


def service_by_code(code: str) -> ServiceDefinition | None:
    for service in SERVICES:
        if service.code == code:
            return service
    return None


def service_amount_ok(service: ServiceDefinition, amount: Decimal) -> str | None:
    if amount < service.min_amount:
        return f"El mínimo para {service.name} es S/ {service.min_amount:.2f}."
    if amount > service.max_amount:
        return f"El máximo para {service.name} es S/ {service.max_amount:.2f}."
    return None
