import sys
import time
import requests

SERVER_URL = "http://server:8080"


def esperar_y_conectar(max_retries: int = 10, delay: int = 2) -> bool:
    print("[client] Iniciando comprobación de conexión...")
    for i in range(1, max_retries + 1):
        try:
            r = requests.get(f"{SERVER_URL}/health", timeout=3)
            if r.status_code == 200:
                print(
                    f"[client] ¡Conexión con éxito! Respuesta: {r.json()}\n"
                )
                return True
        except requests.exceptions.ConnectionError:
            print(
                f"[client] Servidor arrancando... reintentando ({i}/{max_retries})"
            )
            time.sleep(delay)

    print("[client] ERROR: No se pudo conectar tras varios intentos.")
    return False


def menu_principal() -> None:
    while True:
        print("\n=== MENÚ SECBANK ===")
        print("1. Comprobar salud del servidor (/health)")
        print("2. Salir")

        try:
            opcion = input("\nSelecciona una opción: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCerrando cliente...")
            sys.exit(0)

        if opcion == "1":
            try:
                r = requests.get(f"{SERVER_URL}/health", timeout=3)
                print(f"[Servidor]: {r.json()}")
            except Exception as e:
                print(f"[Error]: {e}")
        elif opcion == "2":
            print("Saliendo de la aplicación...")
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.")


if __name__ == "__main__":
    if esperar_y_conectar():
        menu_principal()