import json
from itertools import combinations, product
from types import SimpleNamespace
from unittest.mock import MagicMock
import httpx
import pytest
from openai import APIConnectionError, APIStatusError, APITimeoutError
from api.index import get_openai_client, WorkoutRequest, RutinaResponse
from api.demo import CATALOG, generate_demo

ENDPOINT = '/api/generate-routine'


@pytest.mark.parametrize('field', ['objetivo', 'tiempo_minutos', 'equipamiento', 'nivel'])
@pytest.mark.parametrize('operation', ['missing', 'null'])
def test_required_fields(client, payload, provider, field, operation):
    if operation == 'missing':
        del payload[field]
    else:
        payload[field] = None
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code == 422
    assert any(error['loc'][-1] == field for error in response.json()['detail'])
    provider.chat.completions.create.assert_not_called()


@pytest.mark.parametrize('body', ['{broken', 'null', '[]', '"text"'])
def test_invalid_json_body(client, provider, body):
    assert client.post(ENDPOINT, content=body, headers={'Content-Type': 'application/json'}).status_code == 422
    provider.chat.completions.create.assert_not_called()


def test_http_contract(client):
    assert client.get(ENDPOINT).status_code == 405
    assert client.post('/api/health').status_code == 405
    assert client.get('/api/missing').status_code == 404
    assert client.get('/api/health').json() == {'status': 'ok', 'service': 'FitAdaptAI', 'modo': 'demo'}


@pytest.mark.parametrize('mode,expected', [(' IA ', 'ia'), (' DEMO ', 'demo'), ('', None), ('invalid', None)])
def test_mode_normalization(client, monkeypatch, mode, expected):
    monkeypatch.setenv('FITADAPT_MODE', mode)
    response = client.get('/api/health')
    assert response.status_code == (200 if expected else 500)
    if expected:
        assert response.json()['modo'] == expected


def test_provider_receives_user_constraints(client, payload, provider, monkeypatch, routine):
    monkeypatch.setenv('AI_MODEL', 'test-model')
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code == 200
    assert response.json() == routine | {'modo': 'ia'}
    provider.chat.completions.create.assert_called_once()
    args = provider.chat.completions.create.call_args.kwargs
    assert args['model'] == 'test-model'
    assert args['response_format'] == {'type': 'json_object'}
    assert [m['role'] for m in args['messages']] == ['system', 'user']
    for value in ['fuerza', '35', 'peso_corporal', 'principiante']:
        assert value in args['messages'][1]['content']


@pytest.mark.parametrize('fence', ['', '```json\n{}\n```', '```\n{}\n```'])
def test_json_and_markdown_supported(client, payload, provider, routine, fence):
    routine['modo'] = 'demo'  # El proveedor no puede falsear el origen del resultado.
    raw = json.dumps(routine)
    provider.chat.completions.create.return_value.choices[0].message.content = fence.format(raw) if fence else '  '+raw+'  '
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code == 200
    assert response.json()['modo'] == 'ia'


@pytest.mark.parametrize('field,value', [
    ('series', 0), ('series', 9), ('series', True), ('series', '3'),
    ('descanso_segundos', 14), ('descanso_segundos', 301),
    ('rpe_sugerido', 'RPE 11'), ('rpe_sugerido', 'RPE 7.2'),
    ('nombre', '  '), ('repeticiones', ''), ('consejo_tecnico', ''), ('extra', 'unexpected'),
])
def test_reject_invalid_exercise(client, payload, provider, routine, field, value):
    routine['ejercicios'][0][field] = value
    provider.chat.completions.create.return_value.choices[0].message.content = json.dumps(routine)
    assert client.post(ENDPOINT, json=payload).status_code == 502


@pytest.mark.parametrize('content', ['null', '[]', '42', '"text"', '{"secret":"must-not-leak"}'])
def test_non_object_and_incomplete_results(client, payload, provider, content):
    provider.chat.completions.create.return_value.choices[0].message.content = content
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code == 502
    assert 'must-not-leak' not in response.text


def test_empty_choices(client, payload, provider):
    provider.chat.completions.create.return_value = SimpleNamespace(choices=[])
    assert client.post(ENDPOINT, json=payload).status_code == 502


@pytest.mark.parametrize('kind,expected', [('timeout', 504), ('connection', 502), ('rate_limit', 502), ('auth', 502)])
def test_provider_failure_is_safe_and_retryable(client, payload, provider, kind, expected):
    request = httpx.Request('POST', 'https://provider.invalid')
    if kind == 'timeout':
        failure = APITimeoutError(request=request)
    elif kind == 'connection':
        failure = APIConnectionError(message='secret-must-not-leak', request=request)
    else:
        failure = APIStatusError('secret-must-not-leak', response=httpx.Response(
            429 if kind == 'rate_limit' else 401, request=request), body=None)
    success = provider.chat.completions.create.return_value
    provider.chat.completions.create.side_effect = [failure, success]
    response = client.post(ENDPOINT, json=payload)
    assert response.status_code == expected
    assert 'secret-must-not-leak' not in response.text
    assert client.post(ENDPOINT, json=payload).status_code == 200


@pytest.mark.parametrize('custom', [False, True])
def test_client_configuration(monkeypatch, custom):
    monkeypatch.setenv('OPENAI_API_KEY', 'fake-test-key')
    if custom:
        monkeypatch.setenv('OPENAI_BASE_URL', 'https://provider.invalid/v1')
    constructor = MagicMock()
    monkeypatch.setattr('api.index.OpenAI', constructor)
    assert get_openai_client() is constructor.return_value
    constructor.assert_called_once_with(api_key='fake-test-key',
        base_url='https://provider.invalid/v1' if custom else None, timeout=40.0, max_retries=0)


EQUIPMENT_SETS = [list(group) for size in range(1, 6) for group in combinations(CATALOG, size)]


@pytest.mark.parametrize('equipment', EQUIPMENT_SETS, ids=lambda e: '+'.join(e))
def test_demo_all_equipment_subsets(equipment):
    allowed = {name for key in equipment for name, _ in CATALOG[key]}
    for goal, level, minutes in product(['hipertrofia', 'fuerza', 'perdida_grasa', 'resistencia'],
                                       ['principiante', 'intermedio', 'avanzado'], range(20, 76, 5)):
        request = WorkoutRequest(objetivo=goal, nivel=level, tiempo_minutos=minutes, equipamiento=equipment)
        routine = RutinaResponse(**generate_demo(request))
        assert routine.tiempo_total_estimado <= minutes
        assert len(routine.ejercicios) == 4
        assert {exercise.nombre for exercise in routine.ejercicios} <= allowed
        assert all(1 <= exercise.series <= {'principiante': 3, 'intermedio': 4, 'avanzado': 5}[level]
                   for exercise in routine.ejercicios)
        if level == 'principiante':
            assert all(float(exercise.rpe_sugerido.split()[1]) <= 7 for exercise in routine.ejercicios)
