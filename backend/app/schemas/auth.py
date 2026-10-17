# -*- coding: utf-8 -*-
"""Esquemas de autenticación y usuarios (RF-01, RF-02)."""
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    correo: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    usuario: "UsuarioMe"


class UsuarioMe(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: EmailStr
    rol: str = ""
    permisos: list[str] = []


class PermisoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo: str
    descripcion: str


class RolOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    descripcion: str
    permisos: list[PermisoOut] = []


class UsuarioCreate(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    correo: EmailStr
    password: str = Field(min_length=8, max_length=128)
    rol_id: int


class UsuarioUpdate(BaseModel):
    nombre: str | None = Field(default=None, min_length=2, max_length=120)
    password: str | None = Field(default=None, min_length=8, max_length=128)
    rol_id: int | None = None
    estado: bool | None = None


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    correo: EmailStr
    rol_id: int
    estado: bool


class PaginaUsuarios(BaseModel):
    total: int
    pagina: int
    tamanio: int
    items: list[UsuarioOut]


TokenResponse.model_rebuild()
