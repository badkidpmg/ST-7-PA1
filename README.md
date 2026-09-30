# ST-7-PA1 (SecBank)

## Project structure
- `secbank/server`: FastAPI backend
- `secbank/client`: client container image
- `secbank/docker-compose.yml`: local orchestration for `server` and `client`

## Basic setup
1. Go to the compose directory:
   ```bash
   cd /home/runner/work/ST-7-PA1/ST-7-PA1/secbank
   ```
2. Build and start the stack:
   ```bash
   docker compose up --build -d
   ```
3. Check API health:
   ```bash
   curl http://localhost:8080/health
   ```

## Run tests from the client container
From `/home/runner/work/ST-7-PA1/ST-7-PA1/secbank`, run:

```bash
docker compose run --rm --no-deps \
  -v ./server:/workspace/server \
  client sh -lc "pip install --no-cache-dir -r /workspace/server/requirements.txt pytest httpx && PYTHONPATH=/workspace/server python -m pytest -q /workspace/server/tests"
```

## How to know tests passed
Tests went well when all of the following are true:
- the command exits with code `0`
- pytest output ends with `N passed`
- there are no `FAILED` lines in the summary

## Stop the environment
```bash
cd /home/runner/work/ST-7-PA1/ST-7-PA1/secbank
docker compose down
```
