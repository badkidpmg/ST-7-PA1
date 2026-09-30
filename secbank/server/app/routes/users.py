import sqlite3
import time
from pathlib import Path



from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db_path
from app.models import RegisterRequest, RegisterResponse
from app.security import hash_password

from fastapi import Header

from app.models import LoginRequest, LoginResponse, UserResponse
from app.security import (
    create_session_token,
    hash_session_token,
    verify_password,

)

router = APIRouter(
    prefix="/api/v1",
    tags=["users"],
)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db_path: Path = Depends(get_db_path),
) -> RegisterResponse:
    password_hash = hash_password(data.password)

    try:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                """,
                (data.username, password_hash),
            )
            user_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El nombre de usuario ya existe",
        )

    return RegisterResponse(
        id=user_id,
        username=data.username,
        message="Usuario registrado correctamente",
    )

MAX_FAILED_ATTEMPTS = 5
LOCK_SECONDS = 60
SESSION_SECONDS = 30 * 60


def get_bearer_token(authorization: str | None) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Sesión no válida")

    scheme, separator, token = authorization.partition(" ")

    if (
        separator != " "
        or scheme.lower() != "bearer"
        or not token
        or len(token) > 256
    ):
        raise HTTPException(status_code=401, detail="Sesión no válida")

    return token


def active_user(
    authorization: str | None = Header(default=None),
    db_path: Path = Depends(get_db_path),
) -> tuple[int, str, str]:
    token = get_bearer_token(authorization)
    token_hash = hash_session_token(token)
    now = int(time.time())

    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT u.id, u.username, s.expires_at
            FROM sessions AS s
            JOIN users AS u ON u.id = s.user_id
            WHERE s.token_hash = ?
            """,
            (token_hash,),
        ).fetchone()

        if row is None:
            raise HTTPException(status_code=401, detail="Sesión no válida")

        user_id, username, expires_at = row

        if expires_at <= now:
            connection.execute(
                "DELETE FROM sessions WHERE token_hash = ?",
                (token_hash,),
            )

            connection.commit()
            raise HTTPException(status_code=401, detail="Sesión caducada")

    return user_id, username, token_hash


@router.post("/login", response_model=LoginResponse)
def login(
    data: LoginRequest,
    db_path: Path = Depends(get_db_path),
) -> LoginResponse:
    now = int(time.time())

    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            """
            SELECT id, password_hash, failed_attempts, locked_until
            FROM users
            WHERE username = ?
            """,
            (data.username,),
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=401,
                detail="Usuario o contraseña incorrectos",
            )

        user_id, password_hash, failed_attempts, locked_until = row

        if locked_until > now:
            raise HTTPException(
                status_code=429,
                detail="Demasiados intentos. Prueba más tarde",
            )

        if not verify_password(password_hash, data.password):
            failures = failed_attempts + 1
            next_lock = now + LOCK_SECONDS if failures >= MAX_FAILED_ATTEMPTS else 0

            connection.execute(
                """
                UPDATE users
                SET failed_attempts = ?, locked_until = ?
                WHERE id = ?
                """,
                (0 if next_lock else failures, next_lock, user_id),
            )

            connection.commit()

            if next_lock:
                raise HTTPException(
                    status_code=429,
                    detail="Demasiados intentos. Prueba más tarde",
                )

            raise HTTPException(
                status_code=401,
                detail="Usuario o contraseña incorrectos",
            )

        connection.execute(
            """
            UPDATE users
            SET failed_attempts = 0, locked_until = 0
            WHERE id = ?
            """,
            (user_id,),
        )

        token = create_session_token()
        connection.execute(
            """
            INSERT INTO sessions (token_hash, user_id, expires_at)
            VALUES (?, ?, ?)
            """,
            (hash_session_token(token), user_id, now + SESSION_SECONDS),
        )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        expires_in=SESSION_SECONDS,
    )


@router.get("/me", response_model=UserResponse)
def me(user: tuple[int, str, str] = Depends(active_user)) -> UserResponse:
    user_id, username, _ = user
    return UserResponse(id=user_id, username=username)


@router.post("/logout")
def logout(
    user: tuple[int, str, str] = Depends(active_user),
    db_path: Path = Depends(get_db_path),
) -> dict[str, str]:
    _, _, token_hash = user

    with sqlite3.connect(db_path) as connection:
        connection.execute(
            "DELETE FROM sessions WHERE token_hash = ?",
            (token_hash,),
        )

    return {"message": "Sesión cerrada"}