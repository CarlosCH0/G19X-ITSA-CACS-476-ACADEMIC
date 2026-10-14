# -*- coding: utf-8 -*-
"""Configuración centralizada por variables de entorno (RNF-05).

Los secretos (SECRET_KEY, llaves de Azure) nunca van en el código fuente:
se cargan desde variables de entorno o un archivo .env no versionado.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # --- Aplicación ---
    app_name: str = "Sistema de Identificación de Talento de Alto Potencial"
    api_prefix: str = "/api"
    entorno: str = "desarrollo"  # desarrollo | produccion

    # --- Base de datos (PostgreSQL en la implementación; SQLite local) ---
    database_url: str = "sqlite:///./talento.db"

    # --- Seguridad ---
    secret_key: str = "cambiar-esta-clave-en-produccion-mediante-variable-de-entorno"
    algoritmo_token: str = "HS256"
    access_token_expire_minutes: int = 480

    # --- Datos de arranque (solo desarrollo) ---
    seed_demo_data: bool = True
    admin_email: str = "admin@develop.com.mx"
    admin_password: str = "Admin123!"

    # --- Modelo analítico ---
    modelo_version: str = "reglas-v1"

    @property
    def cors_origins_list(self) -> list[str]:
        raw = "http://localhost:5173,http://127.0.0.1:5173"
        return [o.strip() for o in raw.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
