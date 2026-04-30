from unittest.mock import MagicMock, patch

import requests

from services import http_client


def _mock_response(*, status: int, json_body=None, headers=None, text="") -> MagicMock:
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status
    resp.headers = headers or {}
    resp.text = text
    resp.json = MagicMock(return_value=json_body if json_body is not None else {})
    return resp


def test_get_json_success():
    with patch("services.http_client.requests.request") as req:
        req.return_value = _mock_response(status=200, json_body={"hello": "world"})
        body, status = http_client.get_json("https://example.com")
    assert body == {"hello": "world"}
    assert status == "success"


def test_get_json_404_classified_not_found():
    with patch("services.http_client.requests.request") as req:
        req.return_value = _mock_response(status=404)
        body, status = http_client.get_json("https://example.com")
    assert body is None
    assert status == "not_found"


def test_get_json_429_retries_with_retry_after():
    rate_limited = _mock_response(status=429, headers={"Retry-After": "0"})
    success = _mock_response(status=200, json_body={"ok": True})
    with patch("services.http_client.requests.request", side_effect=[rate_limited, success]):
        with patch("services.http_client.time.sleep") as sleep_mock:
            body, status = http_client.get_json("https://example.com", max_retries=2)
    assert status == "success"
    assert body == {"ok": True}
    sleep_mock.assert_called()


def test_get_json_timeout_returns_timeout_status():
    with patch("services.http_client.requests.request", side_effect=requests.Timeout()):
        with patch("services.http_client.time.sleep"):
            body, status = http_client.get_json("https://example.com", max_retries=2)
    assert body is None
    assert status == "timeout"


def test_github_403_with_zero_remaining_classified_rate_limited():
    resp = _mock_response(
        status=403,
        headers={"X-RateLimit-Remaining": "0"},
        text="API rate limit exceeded",
    )
    assert http_client._classify_response(resp) == "rate_limited"


def test_unauth_403_classified_unauthorized():
    resp = _mock_response(status=403, headers={"X-RateLimit-Remaining": "5"}, text="forbidden")
    assert http_client._classify_response(resp) == "unauthorized"
