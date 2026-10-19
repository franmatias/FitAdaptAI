"""Cada prueba empieza sin credenciales y tiene prohibida la salida a red."""
import socket
from unittest.mock import MagicMock
from types import SimpleNamespace
import json
import pytest
from fastapi.testclient import TestClient
from api.index import app, require_authenticated_user


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    previous_overrides = app.dependency_overrides.copy()
    app.dependency_overrides[require_authenticated_user] = lambda: 'test-user'
    for name in ('OPENAI_API_KEY', 'OPENAI_BASE_URL', 'AI_MODEL'):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv('FITADAPT_MODE', 'demo')
    connect = socket.socket.connect
    def guarded_connect(sock, address):
        # asyncio usa un socketpair de loopback para comunicarse en Windows.
        if isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1'):
            return connect(sock, address)
        raise AssertionError('Las pruebas no pueden abrir conexiones externas')
    def forbidden(*args, **kwargs):
        raise AssertionError('Las pruebas no pueden abrir conexiones de red')
    monkeypatch.setattr(socket.socket, 'connect', guarded_connect)
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    monkeypatch.setattr('api.index.OpenAI', forbidden)
    yield
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous_overrides)


@pytest.fixture
def client():
    with TestClient(app) as instance:
        yield instance


@pytest.fixture
def unauthenticated_client():
    previous_override = app.dependency_overrides.pop(require_authenticated_user, None)
    try:
        with TestClient(app) as instance:
            yield instance
    finally:
        if previous_override is not None:
            app.dependency_overrides[require_authenticated_user] = previous_override


@pytest.fixture
def payload():
    return dict(objetivo='fuerza', tiempo_minutos=35,
                equipamiento=['peso_corporal'], nivel='principiante')


@pytest.fixture
def routine():
    return dict(calentamiento='Movilidad suave', ejercicios=[dict(
        nombre='Sentadilla al aire', series=3, repeticiones='8-10',
        descanso_segundos=60, rpe_sugerido='RPE 6', consejo_tecnico='Mantén los talones apoyados.')],
        alternativa_rapida='Puente de glúteos', tiempo_total_estimado=25)


@pytest.fixture
def provider(monkeypatch, routine):
    monkeypatch.setenv('FITADAPT_MODE', 'ia')
    fake = MagicMock()
    fake.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(routine)))])
    monkeypatch.setattr('api.index.get_openai_client', lambda: fake)
    return fake
