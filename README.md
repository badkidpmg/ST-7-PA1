# ST-7-PA1 (SecBank)

## Basic setup

1. Go to the project root:
   ```bash
   cd /home/runner/work/ST-7-PA1/ST-7-PA1/secbank
   ```
2. Start containers:
   ```bash
   docker compose up --build
   ```
3. The API is available at:
   - `http://localhost:8080/health`

## Run tests

From repository root:

```bash
cd /home/runner/work/ST-7-PA1/ST-7-PA1
PYTHONPATH=/home/runner/work/ST-7-PA1/ST-7-PA1/secbank/server python -m pytest -q secbank/server/tests
```

## How to know tests went well

Tests passed when:
- the command exits with code `0`
- pytest summary shows all tests passing (for example, output ending with `X passed` and no `FAILED` lines)
