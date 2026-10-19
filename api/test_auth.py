from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from clerk_backend_api.security.types import TokenVerificationErrorReason

BASE = {
    'objetivo': 'hipertrofia',
    'tiempo_minutos': 35,
    'equipamiento': ['mancuernas'],
    'nivel': 'principiante',
}


def test_generate_routine_requires_a_clerk_session(unauthenticated_client):
    response = unauthenticated_client.post('/api/generate-routine', json=BASE)

    assert response.status_code == 401
    assert response.headers['www-authenticate'] == 'Bearer'


def test_generate_routine_fails_closed_if_clerk_is_not_configured(
    unauthenticated_client, monkeypatch
):
    monkeypatch.setenv('CLERK_SECRET_KEY', '')

    response = unauthenticated_client.post(
        '/api/generate-routine',
        json=BASE,
        headers={'Authorization': 'Bearer example-session-token'},
    )

    assert response.status_code == 503


@pytest.mark.parametrize('is_signed_in,expected_status', [(True, 200), (False, 401)])
def test_generate_routine_verifies_clerk_session(
    unauthenticated_client, monkeypatch, is_signed_in, expected_status
):
    monkeypatch.setenv('CLERK_SECRET_KEY', 'unit-test-secret')
    monkeypatch.setenv('CLERK_AUTHORIZED_PARTIES', 'https://fitadaptai.example')
    clerk = MagicMock()
    clerk.authenticate_request.return_value = SimpleNamespace(
        is_signed_in=is_signed_in,
        payload={'sub': 'user_test'} if is_signed_in else None,
        reason=None,
    )
    monkeypatch.setattr('api.index.Clerk', lambda **kwargs: clerk)

    response = unauthenticated_client.post(
        '/api/generate-routine',
        json=BASE,
        headers={
            'Authorization': 'Bearer example-session-token',
            'Origin': 'https://fitadaptai.example',
        },
    )

    assert response.status_code == expected_status
    clerk.authenticate_request.assert_called_once()
    request, options = clerk.authenticate_request.call_args.args
    assert isinstance(request, httpx.Request)
    assert options.authorized_parties == ['https://fitadaptai.example']
    assert options.accepts_token == ['session_token']


def test_generate_routine_reports_clerk_verification_outage(
    unauthenticated_client, monkeypatch
):
    monkeypatch.setenv('CLERK_SECRET_KEY', 'unit-test-secret')
    clerk = MagicMock()
    clerk.authenticate_request.return_value = SimpleNamespace(
        is_signed_in=False,
        payload=None,
        reason=TokenVerificationErrorReason.SERVER_ERROR,
    )
    monkeypatch.setattr('api.index.Clerk', lambda **kwargs: clerk)

    response = unauthenticated_client.post(
        '/api/generate-routine',
        json=BASE,
        headers={'Authorization': 'Bearer example-session-token'},
    )

    assert response.status_code == 503
