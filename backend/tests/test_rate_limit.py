"""Integration tests for the global per-IP rate limiter.

The test environment disables the limiter by default (see conftest.py) so
existing tests can hammer endpoints freely. This file re-enables it with a
tiny bucket so we can assert the 429 behaviour without making 300+ calls.

The fixture composes on top of the existing ``client`` fixture so it
inherits the test DB session and authentication overrides — we only mutate
the limiter on the same app instance and restore it on teardown.
"""

from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient
from slowapi.util import get_remote_address
from slowapi.wrappers import LimitGroup

from src.main import STATIC_DIR, app


@pytest.fixture
async def rate_limited_client(client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """Re-enable the limiter at 3/minute on the shared app and yield the test client.

    Depends on the conftest ``client`` fixture so DB and auth overrides are in
    place. We restore the limiter's original ``enabled`` flag and
    ``_default_limits`` on teardown to avoid cross-test pollution.
    """
    limiter = app.state.limiter

    original_enabled = limiter.enabled
    original_defaults = list(limiter._default_limits)

    # slowapi stores defaults as LimitGroup objects (NOT Limit objects).
    # _check_request_limit does ``itertools.chain(*self._default_limits)`` and
    # iterating a LimitGroup yields parsed Limit instances, so we must hand it
    # a LimitGroup here — Limit alone would explode at iteration time.
    limiter.enabled = True
    limiter._default_limits = [
        LimitGroup(
            "3/minute",
            get_remote_address,
            None,
            False,
            None,
            None,
            None,
            1,
            False,
        )
    ]
    limiter.reset()

    yield client

    limiter.enabled = original_enabled
    limiter._default_limits = original_defaults
    limiter.reset()


async def test_default_limit_triggers_429_on_unprotected_route(
    rate_limited_client: AsyncClient,
) -> None:
    """The 4th request from the same IP to a route with no per-route limit is 429."""
    # /api/v1/ has no per-route decorator, so it falls through to the default bucket.
    for _ in range(3):
        response = await rate_limited_client.get("/api/v1/")
        assert response.status_code == 200, response.text

    response = await rate_limited_client.get("/api/v1/")
    assert response.status_code == 429
    body = response.json()
    assert body["error"] == "rate_limit_exceeded"


async def test_spa_catch_all_is_subject_to_default_limit(
    rate_limited_client: AsyncClient,
) -> None:
    """The SPA catch-all (serve_spa) is the main scanner-amplification surface.

    Note: this test only runs meaningfully when the static directory exists
    (i.e. the frontend has been built into ``backend/static``). When it
    doesn't exist the catch-all isn't registered at all — skip in that case.
    """
    if not STATIC_DIR.exists():
        pytest.skip("static dir not present — SPA catch-all not registered")

    for _ in range(3):
        response = await rate_limited_client.get("/some-arbitrary-spa-path")
        assert response.status_code == 200

    response = await rate_limited_client.get("/another-spa-path")
    assert response.status_code == 429


async def test_health_endpoint_is_exempt(
    rate_limited_client: AsyncClient,
) -> None:
    """/health is exempt — health probes must never get 429."""
    for _ in range(10):  # well above the 3/minute default
        response = await rate_limited_client.get("/health")
        assert response.status_code == 200


async def test_per_route_limit_overrides_default(
    rate_limited_client: AsyncClient,
) -> None:
    """/api/v1/auth/login has @limiter.limit('5/minute') — its own bucket, not the default 3/minute.

    We exhaust the login bucket (5 attempts -> 6th is 429). This proves that the
    per-route decorator on auth.login uses the same Limiter instance as the
    default; otherwise the default's 3/minute bucket would have triggered first
    on the 4th attempt.
    """
    # Each request returns 401 (bad creds) but still counts against the bucket.
    for i in range(5):
        response = await rate_limited_client.post(
            "/api/v1/auth/login",
            data={"username": "no-such-user@test.com", "password": "wrong"},
        )
        assert response.status_code == 401, f"attempt {i + 1}: {response.text}"

    response = await rate_limited_client.post(
        "/api/v1/auth/login",
        data={"username": "no-such-user@test.com", "password": "wrong"},
    )
    assert response.status_code == 429
