import sys
import time
import requests
import getpass

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


def registrar_usuario() -> bool:
    """Registra un nuevo usuario en el servidor."""
    print("\n=== REGISTRO DE USUARIO ===")
    
    try:
        username = input("Nombre de usuario (3-50 caracteres): ").strip()
        
        if len(username) < 3 or len(username) > 50:
            print("[Error] El nombre de usuario debe tener entre 3 y 50 caracteres.")
            return False
        
        password = getpass.getpass("Contraseña (8-128 caracteres): ")
        confirm_password = getpass.getpass("Confirmar contraseña: ")
        
        if password != confirm_password:
            print("[Error] Las contraseñas no coinciden.")
            return False
        
        if len(password) < 8 or len(password) > 128:
            print("[Error] La contraseña debe tener entre 8 y 128 caracteres.")
            return False
        
        data = {
            "username": username,
            "password": password,
        }
        
        response = requests.post(
            f"{SERVER_URL}/api/v1/register",
            json=data,
            timeout=5
        )
        
        if response.status_code == 201:
            result = response.json()
            print(f"\n✓ {result.get('message', 'Usuario registrado')}")
            print(f"  ID de usuario: {result.get('id')}")
            print(f"  Nombre de usuario: {result.get('username')}")
            return True
        elif response.status_code == 409:
            print("[Error] El nombre de usuario ya existe.")
            return False
        else:
            error = response.json().get('detail', 'Error desconocido')
            print(f"[Error] {error}")
            return False
            
    except requests.exceptions.Timeout:
        print("[Error] Tiempo de espera agotado.")
        return False
    except Exception as e:
        print(f"[Error] {e}")
        return False


def iniciar_sesion() -> str | None:
    """Inicia sesión y retorna el token de acceso si es exitoso."""
    print("\n=== INICIAR SESIÓN ===")
    
    try:
        username = input("Nombre de usuario: ").strip()
        password = getpass.getpass("Contraseña: ")
        
        data = {
            "username": username,
            "password": password,
        }
        
        response = requests.post(
            f"{SERVER_URL}/api/v1/login",
            json=data,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            token = result.get('access_token')
            expires_in = result.get('expires_in', 0)
            minutes = expires_in // 60
            
            print(f"\n✓ Sesión iniciada correctamente")
            print(f"  Token de acceso obtenido")
            print(f"  Tiempo de expiración: {minutes} minutos")
            return token
            
        elif response.status_code == 429:
            print("[Error] Demasiados intentos fallidos. Intenta más tarde.")
            return None
        elif response.status_code == 401:
            print("[Error] Usuario o contraseña incorrectos.")
            return None
        else:
            error = response.json().get('detail', 'Error desconocido')
            print(f"[Error] {error}")
            return None
            
    except requests.exceptions.Timeout:
        print("[Error] Tiempo de espera agotado.")
        return None
    except Exception as e:
        print(f"[Error] {e}")
        return None


def obtener_usuario_actual(token: str) -> bool:
    """Obtiene información del usuario autenticado."""
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.get(
            f"{SERVER_URL}/api/v1/me",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            user = response.json()
            print(f"\n✓ Usuario autenticado:")
            print(f"  ID: {user.get('id')}")
            print(f"  Usuario: {user.get('username')}")
            return True
        elif response.status_code == 401:
            print("[Error] Sesión no válida o caducada.")
            return False
        else:
            error = response.json().get('detail', 'Error desconocido')
            print(f"[Error] {error}")
            return False
            
    except requests.exceptions.Timeout:
        print("[Error] Tiempo de espera agotado.")
        return False
    except Exception as e:
        print(f"[Error] {e}")
        return False


def cerrar_sesion(token: str) -> bool:
    """Cierra la sesión actual."""
    try:
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        response = requests.post(
            f"{SERVER_URL}/api/v1/logout",
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            print(f"\n✓ Sesión cerrada correctamente")
            return True
        elif response.status_code == 401:
            print("[Error] Sesión no válida o caducada.")
            return False
        else:
            error = response.json().get('detail', 'Error desconocido')
            print(f"[Error] {error}")
            return False
            
    except requests.exceptions.Timeout:
        print("[Error] Tiempo de espera agotado.")
        return False
    except Exception as e:
        print(f"[Error] {e}")
        return False


def menu_autenticado(token: str) -> bool:
    """Menú para usuario autenticado. Retorna False para cerrar sesión."""
    while True:
        print("\n=== MENÚ SECBANK (AUTENTICADO) ===")
        print("1. Ver mi perfil")
        print("2. Comprobar salud del servidor")
        print("3. Cerrar sesión")
        print("4. Salir")
        
        try:
            opcion = input("\nSelecciona una opción: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCerrando cliente...")
            sys.exit(0)
        
        if opcion == "1":
            obtener_usuario_actual(token)
        elif opcion == "2":
            try:
                r = requests.get(f"{SERVER_URL}/health", timeout=3)
                print(f"\n[Servidor]: {r.json()}")
            except Exception as e:
                print(f"[Error]: {e}")
        elif opcion == "3":
            if cerrar_sesion(token):
                return False  # Volver al menú principal
        elif opcion == "4":
            print("Saliendo de la aplicación...")
            sys.exit(0)
        else:
            print("Opción no válida. Inténtalo de nuevo.")


def menu_principal() -> None:
    """Menú principal sin autenticar."""
    while True:
        print("\n=== MENÚ SECBANK ===")
        print("1. Registrar nuevo usuario")
        print("2. Iniciar sesión")
        print("3. Comprobar salud del servidor")
        print("4. Salir")

        try:
            opcion = input("\nSelecciona una opción: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCerrando cliente...")
            sys.exit(0)

        if opcion == "1":
            registrar_usuario()
        elif opcion == "2":
            token = iniciar_sesion()
            if token:
                menu_autenticado(token)
        elif opcion == "3":
            try:
                r = requests.get(f"{SERVER_URL}/health", timeout=3)
                print(f"\n[Servidor]: {r.json()}")
            except Exception as e:
                print(f"[Error]: {e}")
        elif opcion == "4":
            print("Saliendo de la aplicación...")
            break
        else:
            print("Opción no válida. Inténtalo de nuevo.")


if __name__ == "__main__":
    if esperar_y_conectar():
        menu_principal()
