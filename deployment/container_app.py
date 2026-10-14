"""Punto de entrada Docker: API existente e interfaz bajo un mismo origen."""
from pathlib import Path

from fastapi.staticfiles import StaticFiles

from api.index import app


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; base-uri 'self'; object-src 'none'; "
        "frame-ancestors 'none'; form-action 'self'; script-src 'self'; "
        "style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'"
    )
    return response


# Se monta después de las rutas /api para conservar sus respuestas y validaciones.
app.mount("/", StaticFiles(directory=Path(__file__).resolve().parent / "dist", html=True), name="frontend")
