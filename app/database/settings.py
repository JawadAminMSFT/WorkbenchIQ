from dataclasses import dataclass
import os
from typing import Optional

@dataclass
class DatabaseSettings:
    backend: str = "json"  # 'json' or 'postgresql'
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    user: Optional[str] = None
    password: Optional[str] = None
    ssl_mode: Optional[str] = None
    schema: Optional[str] = None

    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        return cls(
            backend=os.getenv("DATABASE_BACKEND", "json"),
            host=os.getenv("POSTGRESQL_HOST"),
            port=int(os.getenv("POSTGRESQL_PORT", 5432)) if os.getenv("POSTGRESQL_PORT") else None,
            database=os.getenv("POSTGRESQL_DATABASE"),
            user=os.getenv("POSTGRESQL_USER"),
            password=os.getenv("POSTGRESQL_PASSWORD"),
            ssl_mode=os.getenv("POSTGRESQL_SSL_MODE"),
            schema=os.getenv("POSTGRESQL_SCHEMA"),
        )
