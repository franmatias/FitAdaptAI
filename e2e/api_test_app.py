"""ASGI entrypoint for browser tests with an isolated auth dependency override."""
from api.index import app, require_authenticated_user

app.dependency_overrides[require_authenticated_user] = lambda: 'e2e-user'
