import requests

SERVER_URL = "http://server:8080"


def check_health() -> None:
    r = requests.get(f"{SERVER_URL}/health", timeout=5)
    print(f"[client] status={r.status_code} body={r.json()}")


if __name__ == "__main__":
    check_health()
