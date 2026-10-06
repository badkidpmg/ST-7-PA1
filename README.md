# ST-7-PA1 (SecBank)

## Project structure
- `secbank/server`: FastAPI backend
- `secbank/server/app`: aplicación principal (API, seguridad, base de datos, cliente)
- `secbank/server/tests`: tests de seguridad, base de datos y API
- `secbank/server/scripts`: scripts auxiliares (seed de usuarios demo)
- `secbank/docker-compose.yml`: local orchestration for `server` and `client`

## Setup Básico
1. Ir al directorio del compose:
   ```bash
   cd secbank
   ```
2. Construir e iniciar el stack:
   ```bash
   docker compose up --build -d
   ```
3. Verificar la salud de la API:
   ```bash
   curl http://localhost:8080/health
   ```
## Crear usuarios de demostración
El proyecto incluye un script que crea dos usuarios demo en la base de datos:

```bash
docker compose exec server sh -c "PYTHONPATH=/app python /app/scripts/seed_users.py"
```

Usuarios creados:
- `alice_demo` / `DemoAlice123!`
- `bob_demo` / `DemoBob123!`

Si los usuarios ya existen, informa que ya están creados.


## Ejecutar el cliente interactivo
Para abrir el cliente de línea de comandos:

```bash
docker compose exec server python -m app.client
```

Desde el cliente puedes:
- Registrarte (`register`)
- Iniciar sesión (`login`)
- Consultar saldo (`balance`)
- Transferir dinero (`transfer`)
- Cerrar sesión (`logout`)


## Ejecutar los tests
Desde el directorio `secbank`:

```bash
docker compose run --rm --no-deps server sh -c "python -m pip install -r requirements-test.txt && python -m pytest -q"
```

Debe mostrar `14 passed` sin fallos.

### Qué verifican los tests
- **Seguridad**: hash Argon2id con sal aleatoria, hashes distintos para contraseñas iguales con sal distinta, verificación correcta.
- **Base de datos**: tablas creadas, usuarios con hash distinto, rollback en transacciones fallidas, nonce único.
- **API**: registro/login/logout, nonce único por sesión, saldo inicial 0, transferencia válida, rollback por saldo insuficiente, nonce rechazado tras logout.

## Requisitos de seguridad implementados
- **Argon2id** con sal aleatoria y parámetros adecuados (memory, time, parallelism).
- **Transaccionalidad** en transferencias: rollback automático si el saldo es insuficiente.
- **Nonce único por sesión**: cada comando requiere un nonce válido; se invalida al hacer logout.
- **Usuarios pre-registrados**: script `seed_users.py` para crear usuarios demo.


## Stop the environment
```bash
cd /home/runner/work/ST-7-PA1/ST-7-PA1/secbank
docker compose down
```

## Limpieza (opcional)
Para eliminar la base de datos y empezar desde cero:

```bash
docker compose exec server sh -c "rm -f /app/data/secbank.db"
docker compose down

