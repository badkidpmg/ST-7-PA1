import sqlite3

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import configured_db_path, init_db
from app.security import hash_password


TEST_USERS = (
    ("alice_demo", "DemoAlice123!"),
    ("bob_demo", "DemoBob123!"),
)


def main() -> None:
    db_path = configured_db_path()
    init_db(db_path)

    with sqlite3.connect(db_path) as connection:
        for username, password in TEST_USERS:
            try:
                connection.execute(
                    """
                    INSERT INTO users (username, password_hash)
                    VALUES (?, ?)
                    """,
                    (username, hash_password(password)),
                )
                print(f"Creado usuario de prueba: {username}")
            except sqlite3.IntegrityError:
                print(f"Ya existe usuario de prueba: {username}")


if __name__ == "__main__":
    main()