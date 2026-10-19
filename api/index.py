import os
import json
from pathlib import Path
from enum import Enum
from typing import List
import httpx
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions, TokenVerificationErrorReason
from fastapi import Depends, FastAPI, HTTPException, Request, status
from pydantic import BaseModel, Field, ConfigDict, ValidationError, field_validator
from openai import OpenAI, APIError, APITimeoutError
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[1] / '.env')

app = FastAPI(
    title="FitAdapt AI Engine",
    description="Backend serverless para la generación estructurada de rutinas de gimnasio",
    version="1.0.0"
)

def generation_mode():
    mode = os.getenv('FITADAPT_MODE', 'demo').strip().lower()
    if mode not in {'demo', 'ia'}:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La variable FITADAPT_MODE debe ser 'demo' o 'ia'."
        )
    return mode

# 1. Esquemas de validación de entrada
class ObjetivoEnum(str, Enum):
    hipertrofia = "hipertrofia"
    fuerza = "fuerza"
    perdida_grasa = "perdida_grasa"
    resistencia = "resistencia"

class NivelEnum(str, Enum):
    principiante = "principiante"
    intermedio = "intermedio"
    avanzado = "avanzado"

class EquipamientoEnum(str, Enum):
    mancuernas = "mancuernas"
    maquinas = "maquinas"
    poleas = "poleas"
    barras_discos = "barras_discos"
    peso_corporal = "peso_corporal"

class WorkoutRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    objetivo: ObjetivoEnum
    tiempo_minutos: int = Field(..., strict=True, ge=20, le=75, multiple_of=5)
    equipamiento: List[EquipamientoEnum] = Field(..., min_length=1, max_length=5)
    nivel: NivelEnum

    @field_validator('equipamiento')
    @classmethod
    def unique_equipment(cls, values):
        if len(set(values)) != len(values):
            raise ValueError('El equipamiento no puede repetirse.')
        return values

# 2. Esquemas de respuesta estructurada
class Ejercicio(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    nombre: str = Field(min_length=1, max_length=200)
    series: int = Field(strict=True, ge=1, le=8)
    repeticiones: str = Field(min_length=1, max_length=80)
    descanso_segundos: int = Field(strict=True, ge=15, le=300)
    rpe_sugerido: str = Field(pattern=r'^RPE (?:[1-9](?:\.5)?|10)$')
    consejo_tecnico: str = Field(min_length=1, max_length=1000)

class RutinaResponse(BaseModel):
    model_config = ConfigDict(extra='forbid', str_strip_whitespace=True)
    calentamiento: str = Field(min_length=1, max_length=2000)
    ejercicios: List[Ejercicio] = Field(min_length=1, max_length=12)
    alternativa_rapida: str = Field(min_length=1, max_length=2000)
    tiempo_total_estimado: int = Field(strict=True, ge=1, le=75)
    modo: str = 'ia'

def get_openai_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="La variable de entorno OPENAI_API_KEY no está configurada."
        )
    base_url = os.getenv("OPENAI_BASE_URL", None)
    return OpenAI(api_key=api_key, base_url=base_url, timeout=40.0, max_retries=0)

def require_authenticated_user(request: Request) -> str:
    authorization = request.headers.get('authorization', '')
    if not authorization.lower().startswith('bearer '):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Inicia sesión para utilizar este servicio.',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    secret_key = os.getenv('CLERK_SECRET_KEY')
    if not secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='La autenticación no está configurada en el servidor.',
        )

    allowed_parties = [
        origin.strip()
        for origin in os.getenv(
            'CLERK_AUTHORIZED_PARTIES',
            'http://127.0.0.1:5173,http://localhost:5173',
        ).split(',')
        if origin.strip()
    ]
    clerk = Clerk(bearer_auth=secret_key)
    clerk_request = httpx.Request(
        request.method,
        str(request.url),
        headers=request.headers,
    )
    try:
        request_state = clerk.authenticate_request(
            clerk_request,
            AuthenticateRequestOptions(
                authorized_parties=allowed_parties,
                accepts_token=['session_token'],
            ),
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='No se pudo verificar la sesión con Clerk.',
        ) from exc

    if request_state.reason in {
        TokenVerificationErrorReason.SERVER_ERROR,
        TokenVerificationErrorReason.JWK_FAILED_TO_LOAD,
        TokenVerificationErrorReason.JWK_REMOTE_INVALID,
    }:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='No se pudo verificar la sesión con Clerk.',
        )

    if not request_state.is_signed_in:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='La sesión no es válida o ha caducado.',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    user_id = (request_state.payload or {}).get('sub')
    if not isinstance(user_id, str) or not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='La sesión no contiene una identidad válida.',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    return user_id

@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "FitAdaptAI", "modo": generation_mode()}

@app.post("/api/generate-routine", response_model=RutinaResponse)
def generate_routine(payload: WorkoutRequest, user_id: str = Depends(require_authenticated_user)):
    if generation_mode() == 'demo':
        from api.demo import generate_demo
        return RutinaResponse(**generate_demo(payload))
    client = get_openai_client()

    system_prompt = (
        "Genera una propuesta orientativa de entrenamiento en español. "
        "Utiliza únicamente el equipamiento indicado, también en la alternativa. "
        "Incluye calentamiento y descansos en el tiempo total. No excedas el tiempo disponible. "
        "Para principiantes utiliza movimientos sencillos y RPE entre 5 y 7. "
        "Tu objetivo es diseñar una sesión de entrenamiento adaptada a las restricciones indicadas. "
        "Debes responder EXCLUSIVAMENTE con un JSON válido con la siguiente estructura exacta:\n"
        "{\n"
        '  "calentamiento": "descripción de 2-3 frases de movilidad y activación articular",\n'
        '  "ejercicios": [\n'
        '    {\n'
        '      "nombre": "Nombre del ejercicio",\n'
        '      "series": 3,\n'
        '      "repeticiones": "8-10",\n'
        '      "descanso_segundos": 90,\n'
        '      "rpe_sugerido": "RPE 8",\n'
        '      "consejo_tecnico": "Instrucción biomecánica clave de seguridad y ejecución"\n'
        '    }\n'
        '  ],\n'
        '  "alternativa_rapida": "Sustituto rápido por si el equipamiento principal está ocupado",\n'
        '  "tiempo_total_estimado": 45\n'
        "}\n"
        "No incluyas texto conversacional ni explicaciones fuera del bloque JSON."
    )

    user_prompt = (
        f"Genera una sesión de gimnasio con estos parámetros:\n"
        f"- Objetivo: {payload.objetivo.value}\n"
        f"- Tiempo total disponible: {payload.tiempo_minutos} minutos\n"
        f"- Nivel del practicante: {payload.nivel.value}\n"
        f"- Equipamiento disponible: {', '.join([e.value for e in payload.equipamiento])}\n\n"
        f"Ajusta el volumen para no exceder los {payload.tiempo_minutos} minutos."
    )

    try:
        completion = client.chat.completions.create(
            model=os.getenv("AI_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2200,
            response_format={"type": "json_object"},
        )

        raw_content = (completion.choices[0].message.content or '').strip()

        # Limpieza defensiva en caso de delimitadores markdown
        if raw_content.startswith("```"):
            lines = raw_content.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw_content = "\n".join(lines).strip()

        parsed_data = json.loads(raw_content)
        result = RutinaResponse(**parsed_data)
        if result.tiempo_total_estimado > payload.tiempo_minutos:
            raise ValueError('La rutina excede el tiempo disponible')
        result.modo = 'ia'
        return result

    except (ValueError, ValidationError, TypeError, IndexError):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="La respuesta del modelo de IA no cumplió con el formato JSON requerido."
        )
    except APITimeoutError:
        raise HTTPException(status_code=504, detail="La IA ha tardado demasiado. Vuelve a intentarlo.")
    except APIError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="No se pudo contactar con el proveedor de IA. Revisa la configuración del servidor y vuelve a intentarlo."
        )
