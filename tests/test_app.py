from datetime import datetime, timezone

from app import (
    app,
    _circuit_breaker_failures,
    _circuit_breaker_last_failure,
    CIRCUIT_BREAKER_COOLDOWN,
    CIRCUIT_BREAKER_THRESHOLD,
    verify_alpr_checksums,
)


def test_app_creation():
    assert app is not None
    assert app.name == "app"


def test_root_route(client):
    response = client.get("/")
    assert response.status_code == 200


def test_root_route_content_type(client):
    response = client.get("/")
    assert "text/html" in response.content_type


def test_health_route(client):
    response = client.get("/health")
    assert response.status_code == 200


def test_health_route_content_type(client):
    response = client.get("/health")
    assert "application/json" in response.content_type


def test_health_route_status(client):
    response = client.get("/health")
    data = response.get_json()
    assert data["status"] == "ok"


def test_api_data_checksum_verified_flag(client):
    response = client.get("/api/data")
    assert response.status_code == 200
    data = response.get_json()
    assert "checksum_verified" in data


def test_api_providers_checksum_verified_flag(client):
    response = client.get("/api/providers")
    assert response.status_code == 200
    data = response.get_json()
    assert "checksum_verified" in data


def test_api_regions_checksum_verified_flag(client):
    response = client.get("/api/regions")
    assert response.status_code == 200
    data = response.get_json()
    assert "checksum_verified" in data


def test_api_stats_checksum_verified_flag(client):
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.get_json()
    assert "checksum_verified" in data


def test_verify_alpr_checksums():
    results = verify_alpr_checksums()
    assert isinstance(results, dict)
    for i in range(1, 6):
        key = f"alpr_batch{i}.json"
        assert key in results
        assert results[key] is True


def test_circuit_breaker_opens_after_threshold_failures():
    _circuit_breaker_failures.clear()
    _circuit_breaker_last_failure.clear()
    url = "https://example.com/test"
    now = datetime.now(timezone.utc).timestamp()
    for _ in range(CIRCUIT_BREAKER_THRESHOLD):
        _circuit_breaker_failures[url] = _circuit_breaker_failures.get(url, 0) + 1
        _circuit_breaker_last_failure[url] = now
    from app import _is_circuit_open
    assert _is_circuit_open(url) is True


def test_circuit_breaker_closed_below_threshold():
    _circuit_breaker_failures.clear()
    _circuit_breaker_last_failure.clear()
    url = "https://example.com/test2"
    for _ in range(CIRCUIT_BREAKER_THRESHOLD - 1):
        _circuit_breaker_failures[url] = _circuit_breaker_failures.get(url, 0) + 1
        _circuit_breaker_last_failure[url] = 0.0
    from app import _is_circuit_open
    assert _is_circuit_open(url) is False


def test_circuit_breaker_resets_on_success():
    _circuit_breaker_failures.clear()
    _circuit_breaker_last_failure.clear()
    url = "https://example.com/test3"
    _circuit_breaker_failures[url] = CIRCUIT_BREAKER_THRESHOLD
    _circuit_breaker_last_failure[url] = 0.0
    from app import _reset_circuit
    _reset_circuit(url)
    from app import _is_circuit_open
    assert _is_circuit_open(url) is False
    assert url not in _circuit_breaker_failures
    assert url not in _circuit_breaker_last_failure
