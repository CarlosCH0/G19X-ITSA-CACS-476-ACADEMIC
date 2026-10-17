"""Servicio de IA — Azure OpenAI Service (RF-08).

Diseño con degradación elegante: si no hay credenciales configuradas (o el
servicio falla), se genera una explicación determinista local y se marca el
origen. La IA solo recibe contexto autorizado por la aplicación (nunca datos
crudos de la base). La clasificación final siempre es revisada por humanos.
"""
import httpx

from app.core.config import settings

PROMPT_SISTEMA = (
    "Eres un asistente de analítica de personas para la identificación de talento "
    "de alto potencial. Redacta explicaciones breves, profesionales y en español. "
    "Usa EXCLUSIVAMENTE la información del contexto proporcionado; no inventes "
    "datos ni emitas juicios definitivos: recuerda que la decisión final es humana."
)

MAX_TOKENS = 450


def _llamar_azure_openai(mensajes: list[dict[str, str]]) -> str | None:
    """Invoca Azure OpenAI; devuelve None si no está configurado o falla."""
    if not settings.ia_configurada:
        return None
    url = (
        f"{settings.azure_openai_endpoint.rstrip('/')}/openai/deployments/"
        f"{settings.azure_openai_deployment}/chat/completions"
        f"?api-version={settings.azure_openai_api_version}"
    )
    headers = {"api-key": settings.azure_openai_key, "Content-Type": "application/json"}
    cuerpo = {"messages": mensajes, "max_tokens": MAX_TOKENS, "temperature": 0.3}
    try:
        with httpx.Client(timeout=settings.ia_timeout_segundos) as cliente:
            respuesta = cliente.post(url, headers=headers, json=cuerpo)
            respuesta.raise_for_status()
            return respuesta.json()["choices"][0]["message"]["content"].strip()
    except Exception:  # noqa: BLE001 - se usa el modo local si falla el servicio externo
        return None


def explicar_evaluacion(contexto: dict) -> tuple[str, str]:
    """Genera la explicación de un resultado (RF-08, RF-09).

    Devuelve (texto, origen) donde origen es 'azure_openai' o
    'local_determinista'.
    """
    top = contexto.get("factores_top", [])
    factores_txt = ", ".join(
        f"{f['nombre']} ({f['contribucion']:.1f} pts)" for f in top[:5]
    ) or "sin factores disponibles"
    prompt_usuario = (
        f"Contexto autorizado de una evaluación de talento:\n"
        f"- Colaborador: {contexto.get('nombre', 'N/D')} ({contexto.get('area', 'N/D')})\n"
        f"- Periodo: {contexto.get('periodo')}\n"
        f"- Puntuación global: {contexto.get('puntuacion')}\n"
        f"- Clasificación: {contexto.get('clasificacion')}\n"
        f"- Umbral HiPo: {contexto.get('umbral')}\n"
        f"- Cobertura de datos: {contexto.get('cobertura_pct')}\n"
        f"- Factores principales: {factores_txt}\n"
        f"- Versión del modelo: {contexto.get('version_modelo')}\n\n"
        "Redacta un resumen ejecutivo (máx. 150 palabras) que explique por qué "
        "obtuvo esa clasificación, apoyándote en los factores principales."
    )
    texto = _llamar_azure_openai(
        [{"role": "system", "content": PROMPT_SISTEMA}, {"role": "user", "content": prompt_usuario}]
    )
    if texto:
        return texto, "azure_openai"
    return _explicacion_local(contexto, factores_txt), "local_determinista"


def _explicacion_local(contexto: dict, factores_txt: str) -> str:
    clas = str(contexto.get("clasificacion", "N/D")).replace("_", " ").title()
    return (
        f"Resumen de la evaluación de {contexto.get('nombre', 'el colaborador')} "
        f"({contexto.get('area', 'área no indicada')}) para el periodo {contexto.get('periodo')}: "
        f"puntuación global de {contexto.get('puntuacion', 0):.1f}/100 frente a un umbral HiPo de "
        f"{contexto.get('umbral', 0):.0f}, con una cobertura de datos válidos del "
        f"{contexto.get('cobertura_pct', '0%')}. Los factores con mayor contribución fueron: "
        f"{factores_txt}. La clasificación resultante es «{clas}». Este resultado es un insumo "
        f"de apoyo generado con la versión {contexto.get('version_modelo')} del modelo y debe "
        "ser revisado por un usuario autorizado antes de tomar decisiones."
    )


def consulta_asistida(pregunta: str, contexto: str) -> tuple[str, str, str | None]:
    """Consulta asistida (RF-08). Devuelve (respuesta, origen, advertencia)."""
    prompt_usuario = (
        f"Contexto autorizado por la aplicación:\n{contexto}\n\nPregunta del usuario: {pregunta}"
    )
    texto = _llamar_azure_openai(
        [{"role": "system", "content": PROMPT_SISTEMA}, {"role": "user", "content": prompt_usuario}]
    )
    if texto:
        return texto, "azure_openai", None
    advertencia = (
        "Azure OpenAI no está configurado o no respondió; se muestra una respuesta "
        "genérica local. Configura AZURE_OPENAI_ENDPOINT y AZURE_OPENAI_KEY para "
        "habilitar las consultas asistidas."
    )
    local = (
        "No fue posible consultar el servicio de IA en este momento. Con el contexto "
        "autorizado disponible, revisa el perfil del colaborador, sus indicadores del "
        f"periodo y las evaluaciones previas. Tu pregunta fue: «{pregunta}»."
    )
    return local, "local_determinista", advertencia
