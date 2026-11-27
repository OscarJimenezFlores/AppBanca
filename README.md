# AndesBank

Banca de laboratorio para **SI-988 · Soluciones Móviles II**, Universidad Privada de Tacna. La aplicación es multiplataforma (Android e iOS) y conversa con un API propio. No es una entidad financiera, no está supervisada y no mueve dinero real.

## Qué hay en el repositorio

| Carpeta | Responsabilidad |
|---|---|
| `mobile/` | App Flutter. Presentación en MVVM, reglas en dominio, HTTP en datos |
| `backend/` | API FastAPI. Dominio, casos de uso, infraestructura PostgreSQL e interfaz HTTP |
| `postman/` | Colección y entorno para repetir las peticiones |
| `.github/workflows/` | Integración continua, imagen, humo por entorno y tarea semanal |

La documentación de clase (arquitectura y Scrum, manual del API, guía de CI/CD) se prepara aparte y no viaja en este repositorio.

## Un comando para el API y PostgreSQL

Hace falta Docker Desktop en marcha. En un disco externo de macOS aparecen archivos `._` que Docker no puede leer; la variable evita generarlos durante el contexto de build.

```bash
COPYFILE_DISABLE=1 docker compose up --build
```

Cuando `/health` responda, el API queda en `http://127.0.0.1:8080`. La documentación interactiva está en `http://127.0.0.1:8080/docs`.

PostgreSQL escucha en el puerto `5432`.

| Variable | Valor local |
|---|---|
| Base | `andesbank` |
| Usuario | `andes` |
| Clave | `andes_local` |

Para bajar los contenedores y conservar los datos: `docker compose down`. Para empezar de cero, con otra semilla: `docker compose down -v`.

## Clientes de demostración

La clave de los cuatro es `Andes.2026`. El alta de un cliente nuevo rechaza esa clave a propósito: es pública.

| Persona | DNI | Correo | Estado |
|---|---|---|---|
| María Elena Quispe Huanca | 45821367 | maria.quispe@correo.pe | Activa, sin doble factor |
| Carlos Alberto Mendoza Ríos | 70129458 | carlos.mendoza@correo.pe | Activa, TOTP ya encendido |
| Lucía Fernanda Choque Mamani | 41290873 | lucia.choque@correo.pe | Activa, saldo bajo |
| Jorge Luis Paredes Salas | 33445566 | jorge.paredes@correo.pe | Bloqueado |

Carlos usa la semilla de demostración del RFC 6238, `GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ`. Sirve para Microsoft Authenticator, Google Authenticator o Authy: seis dígitos, periodo de 30 segundos, SHA-1. El código vigente, dentro del contenedor:

```bash
docker compose exec api python -c "import pyotp; print(pyotp.TOTP('GEZDGNBVGY3TQOJQGEZDGNBVGY3TQOJQ').now())"
```

Cuentas que el laboratorio deja listas:

| Cliente | Producto | Número | Uso en clase |
|---|---|---|---|
| María | Ahorro | 00110000004821 | Origen habitual |
| María | Corriente | 00110000009034 | Pagos |
| María | CTS | 00110000001102 | No admite cargos desde la app |
| Carlos | Ahorro | 00110000007751 | Destino interno |
| Lucía | Ahorro | 00110000003308 | Saldo que no cubre S/ 500.00 |

El CCI de AndesBank empieza por `999`. El de la cuenta de ahorro de María es `9990 0110 0000 0482 1044`. Un CCI que no empieza por `999` se trata como interbancario y cobra S/ 4.50. El ejemplo del directorio es `99800112345678901234`, Banco Demo Sur.

## Probar el API

```bash
COPYFILE_DISABLE=1 docker compose --profile test run --rm tests
```

Ese perfil crea la base `andesbank_test`, separada de la de trabajo, y no la toca si el nombre no termina en `_test`.

Un recorrido corto, con el API ya levantado:

```bash
curl -s http://127.0.0.1:8080/health
curl -s -X POST http://127.0.0.1:8080/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"identifier":"45821367","password":"Andes.2026"}'
```

Postman: importar `postman/AndesBank.postman_collection.json` y `postman/AndesBank.local.postman_environment.json`, elegir el entorno **AndesBank local** y ejecutar primero **Login María por DNI**. La prueba de la petición guarda el token.

## App móvil

Hace falta el SDK estable de Flutter. Esta versión se analizó y se probó con Flutter 3.50.1.

```bash
cd mobile
flutter pub get
flutter analyze
flutter test
```

Android Emulator habla con la máquina anfitriona por `10.0.2.2`. Ese es el valor por defecto.

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8080
```

Simulador de iOS:

```bash
flutter run --dart-define=API_BASE_URL=http://127.0.0.1:8080
```

Un teléfono físico usa la IP de la computadora en la misma red, por ejemplo `http://192.168.1.20:8080`. El API local es HTTP. Android permite ese tráfico claro solo en esta build de laboratorio; un despliegue real tiene que ser HTTPS.

El ojo de la parte superior oculta los saldos en el teléfono. Es una preferencia visual: el API sigue enviando el monto. La pantalla de doble factor lo dice.

Teclados: DNI, celular, cuenta, CCI y el código TOTP abren el teclado numérico. El monto abre el teclado decimal y no acepta más de dos decimales.

## Reglas de negocio que conviene no redescubrir en clase

- Los montos viajan como texto con dos decimales (`"25.50"`), no como número JSON.
- El día operativo es el de Perú, `UTC-5`, sin horario de verano.
- Mínimo por operación: S/ 1.00. Máximo de una transferencia: S/ 10,000.00. Tope diario de transferencias: S/ 20,000.00.
- Desde S/ 500.00, si el cliente activó el doble factor, la transferencia y el pago piden el código.
- Cinco claves o códigos de ingreso fallidos suspenden el acceso 15 minutos.
- La CTS se consulta. No se debita ni se abona desde la app.
- La tarjeta guarda los últimos cuatro dígitos. No hay PAN completo en la base.

## Integración y despliegue

| Flujo | Cuándo corre |
|---|---|
| `.github/workflows/ci.yml` | Cada push y cada pull request a `main` |
| `.github/workflows/cd.yml` | Un tag `vX.Y.Z` o un disparo manual |
| `.github/workflows/smoke-entorno.yml` | Disparo manual contra development, staging o production |
| `.github/workflows/scheduled.yml` | Lunes 11:00 UTC, las 06:00 en Perú |

La imagen se publica solo si el repositorio tiene las variables `REGISTRY` e `IMAGE_NAME` y los secretos `REGISTRY_USER` y `REGISTRY_PASSWORD`. Sin eso, el flujo construye la imagen y se detiene antes del `docker push`. El humo remoto usa el secreto `API_BASE_URL` del entorno de GitHub. En development, si el secreto no existe, el paso avisa y no falla. En staging y production, la ausencia del secreto rompe el flujo.

## Lo que esta versión deja fuera

No hay cajero automático de verdad, no hay compensación interbancaria, no hay verificación de correo y el esquema lo crea el proceso al arrancar. Antes de una base compartida entre versiones hace falta un mecanismo de migraciones. El secreto JWT del `docker-compose.yml` sirve para la laptop. No sirve para ningún otro sitio.
