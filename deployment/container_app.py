"""Punto de entrada Docker: API existente e interfaz bajo un mismo origen."""
from pathlib import Path

from starlette.exceptions import HTTPException as StarletteHTTPException
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
        "frame-ancestors 'none'; form-action 'self'; "
        "script-src 'self' https://*.clerk.accounts.dev https://*.clerk.com; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https://img.clerk.com https://*.clerk.accounts.dev https://*.clerk.com; "
        "font-src 'self' https://*.clerk.accounts.dev https://*.clerk.com; "
        "connect-src 'self' https://*.clerk.accounts.dev https://*.clerk.com https://api.clerk.com; "
        "frame-src https://*.clerk.accounts.dev https://*.clerk.com"
    )
    return response


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code != 404:
                raise
            return await super().get_response("index.html", scope)


# Se monta después de las rutas /api para conservar sus respuestas y validaciones.
dist_dir = Path(__file__).resolve().parent / "dist"
if not dist_dir.is_dir():
    dist_dir = Path(__file__).resolve().parents[1] / "dist"
app.mount("/", SPAStaticFiles(directory=dist_dir, html=True), name="frontend")
