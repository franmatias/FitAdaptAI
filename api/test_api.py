import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from api.index import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_pydantic_validation_tiempo_fuera_de_rango():
    """Verifica que tiempos inferiores a 20 o superiores a 75 sean rechazados con 422."""
    payload = {
        "objetivo": "hipertrofia",
        "tiempo_minutos": 10,
        "equipamiento": ["mancuernas"],
        "nivel": "intermedio"
    }
    response = client.post("/api/generate-routine", json=payload)
    assert response.status_code == 422

def test_pydantic_validation_equipamiento_vacio():
    """Verifica que una lista de equipamiento vacía sea rechazada con 422."""
    payload = {
        "objetivo": "fuerza",
        "tiempo_minutos": 45,
        "equipamiento": [],
        "nivel": "avanzado"
    }
    response = client.post("/api/generate-routine", json=payload)
    assert response.status_code == 422

@patch("api.index.get_openai_client")
def test_generate_routine_mock_success(mock_get_client, monkeypatch):
    monkeypatch.setenv('FITADAPT_MODE', 'ia')
    """Comprueba el flujo de generación exitoso aislando el servicio de IA mediante un mock."""
    mock_payload = {
        "calentamiento": "Movilidad escapular y 5 minutos de cinta suave.",
        "ejercicios": [
            {
                "nombre": "Press militar con mancuernas sentado",
                "series": 3,
                "repeticiones": "8-10",
                "descanso_segundos": 90,
                "rpe_sugerido": "RPE 8",
                "consejo_tecnico": "Mantén el core firme y no arquees excesivamente la zona lumbar."
            }
        ],
        "alternativa_rapida": "Press de hombros en máquina si las mancuernas no están disponibles.",
        "tiempo_total_estimado": 45
    }

    mock_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps(mock_payload)
    mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
    mock_get_client.return_value = mock_client

    request_data = {
        "objetivo": "hipertrofia",
        "tiempo_minutos": 45,
        "equipamiento": ["mancuernas"],
        "nivel": "intermedio"
    }

    response = client.post("/api/generate-routine", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["tiempo_total_estimado"] == 45
    assert len(data["ejercicios"]) == 1
    assert data["ejercicios"][0]["nombre"] == "Press militar con mancuernas sentado"
