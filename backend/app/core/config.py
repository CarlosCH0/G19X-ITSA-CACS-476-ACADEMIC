# -*- coding: utf-8 -*-
"""Configuración centralizada (RNF-05).

Toda la configuración se lee de variables de entorno (o de un .env local que
NUNCA se sube al repo). Los secretos —SECRET_KEY, llaves de Azure— no van
hardcodeados en el código.
"""
from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore", case_sensitive=False
    )

    # Datos generales de la aplicacion.
    app_name: str = "Sistema de Identificación de Talento de Alto Potencial"
    api_prefix: str = "/api"
    entorno: str = "desarrollo"  # desarrollo | produccion

    # PostgreSQL se usa en Docker y SQLite para desarrollo local.
    database_url: str = "sqlite:///./talento.db"

    # --- Seguridad ---
    secret_key: str = "cambiar-esta-clave-en-produccion-mediante-variable-de-entorno"
    algoritmo_token: str = "HS256"
    access_token_expire_minutes: int = 480  # 8 horas: una jornada de trabajo

    # --- Datos de arranque (solo desarrollo) ---
    seed_demo_data: bool = True
    admin_email: str = "admin@develop.com.mx"
    admin_password: str = "Admin123!"

    # Version del modelo analitico.
    modelo_version: str = "reglas-v1"

    # --- Azure OpenAI (RF-08) ---
    # Si no hay credenciales, la IA usa el modo local y el sistema sigue activo.
    azure_openai_endpoint: str = ""
    azure_openai_key: str = ""
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_openai_api_version: str = "2024-08-01-preview"
    ia_timeout_segundos: int = 20

    @model_validator(mode="after")
    def validar_produccion(self):
        if self.entorno.casefold() in {"produccion", "production"}:
            if len(self.secret_key) < 32 or any(
                marca in self.secret_key.casefold()
                for marca in ("cambiar", "reemplazar", "example")
            ) or len(set(self.secret_key)) < 8:
                raise ValueError("SECRET_KEY debe tener al menos 32 caracteres aleatorios en producción.")
            if self.seed_demo_data:
                raise ValueError("SEED_DEMO_DATA debe ser false en producción.")
            if len(self.admin_password) < 12 or "reemplazar" in self.admin_password.casefold():
                raise ValueError("ADMIN_PASSWORD debe tener al menos 12 caracteres en producción.")
            if self.admin_email.casefold().endswith(".example"):
                raise ValueError("ADMIN_EMAIL debe ser una cuenta real del cliente en producción.")
            if not self.database_url.startswith(("postgresql://", "postgresql+")):
                raise ValueError("Producción requiere una base de datos PostgreSQL.")
            if len(make_url(self.database_url).password or "") < 24:
                raise ValueError("La contraseña PostgreSQL debe tener al menos 24 caracteres en producción.")
        return self

    @property
    def cors_origins_list(self) -> list[str]:
        # En desarrollo se usa Vite; en produccion, Nginx funciona como proxy.
        raw = "http://localhost:5173,http://127.0.0.1:5173"
        return [o.strip() for o in raw.split(",") if o.strip()]

    @property
    def ia_configurada(self) -> bool:
        # se considera "configurada" solo si hay endpoint Y llave
        return bool(self.azure_openai_endpoint and self.azure_openai_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
