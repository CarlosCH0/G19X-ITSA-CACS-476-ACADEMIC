import secrets

import pytest
from pydantic import ValidationError
from pydantic_settings import SettingsConfigDict

from app.core.config import Settings


class _SettingsWithoutEnv(Settings):
    model_config = SettingsConfigDict(env_file=None)


def _credenciales_db():
    return f"postgresql://user:{secrets.token_hex(24)}@localhost/database"


def test_produccion_rechaza_secretos_debilitados():
    with pytest.raises(ValidationError, match="SECRET_KEY"):
        _SettingsWithoutEnv(
            entorno="produccion",
            database_url=_credenciales_db(),
            seed_demo_data=False,
            admin_password="UnaClaveSegura123!",
        )


def test_produccion_rechaza_semilla_de_demostracion():
    with pytest.raises(ValidationError, match="SEED_DEMO_DATA"):
        _SettingsWithoutEnv(
            entorno="produccion",
            database_url=_credenciales_db(),
            secret_key=secrets.token_urlsafe(48),
            seed_demo_data=True,
            admin_password="UnaClaveSegura123!",
        )


def test_produccion_requiere_postgresql_y_password_seguro():
    valores = {
        "entorno": "produccion",
        "secret_key": secrets.token_urlsafe(48),
        "seed_demo_data": False,
        "admin_password": "UnaClaveSegura123!",
    }
    with pytest.raises(ValidationError, match="PostgreSQL"):
        _SettingsWithoutEnv(**valores, database_url="sqlite:///./talento.db")
    with pytest.raises(ValidationError, match="ADMIN_PASSWORD"):
        valores_password_corta = {
            **valores,
            "admin_password": "corta",
        }
        _SettingsWithoutEnv(
            **valores_password_corta,
            database_url=_credenciales_db(),
        )
    with pytest.raises(ValidationError, match="ADMIN_EMAIL"):
        _SettingsWithoutEnv(
            entorno="produccion",
            database_url=_credenciales_db(),
            secret_key=secrets.token_urlsafe(48),
            seed_demo_data=False,
            admin_password="UnaClaveSegura123!",
            admin_email="admin@cliente.example",
        )


def test_produccion_acepta_configuracion_segura():
    config = _SettingsWithoutEnv(
        entorno="production",
        database_url="postgresql+psycopg2://user:"
        f"{secrets.token_hex(24)}@localhost/database",
        secret_key=secrets.token_urlsafe(48),
        seed_demo_data=False,
        admin_password="UnaClaveSegura123!",
        admin_email="admin@cliente.com",
    )
    assert config.entorno == "production"
