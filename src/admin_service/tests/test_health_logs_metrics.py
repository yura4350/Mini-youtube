import logging
from datetime import datetime, timezone

from src.admin_service.main import app, _memory_handler


def test_health_returns_ok():
    """Test GET /health endpoint returns service status."""
    from tests.test_admin import client as test_client

    with test_client() as c:
        resp = c.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "admin"


def test_admin_health_returns_ok():
    """Test GET /admin/health endpoint returns admin service health."""
    from tests.test_admin import client as test_client

    with test_client() as c:
        resp = c.get("/admin/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["service"] == "admin"


def test_logs_returns_formatted_entries(client):
    """Test GET /admin/logs returns log entries with correct format."""
    # Add a test log entry
    logger = logging.getLogger("test.logger")
    logger.info("Test log message")

    resp = client.get("/admin/logs")
    assert resp.status_code == 200
    body = resp.json()
    assert "logs" in body
    assert isinstance(body["logs"], list)

    # If there are logs, validate their structure
    if body["logs"]:
        log = body["logs"][0]
        assert "timestamp" in log
        assert "level" in log
        assert "logger" in log
        assert "message" in log


def test_logs_timestamp_is_iso_format(client):
    """Test that log timestamps are ISO 8601 format."""
    logger = logging.getLogger("test.logger")
    logger.warning("Test warning")

    resp = client.get("/admin/logs")
    assert resp.status_code == 200
    body = resp.json()

    if body["logs"]:
        log = body["logs"][0]
        # Validate ISO 8601 format (should end with +00:00 for UTC)
        assert log["timestamp"].endswith("+00:00")
        datetime.fromisoformat(log["timestamp"])  # Should not raise


def test_metrics_returns_performance_data(client):
    """Test GET /admin/metrics returns all required metrics."""
    resp = client.get("/admin/metrics")
    assert resp.status_code == 200
    body = resp.json()

    # Validate all required fields
    assert "uptime_seconds" in body
    assert "total_requests" in body
    assert "log_entries" in body
    assert "memory_rss_mb" in body

    # Validate data types
    assert isinstance(body["uptime_seconds"], (int, float))
    assert isinstance(body["total_requests"], int)
    assert isinstance(body["log_entries"], int)
    assert isinstance(body["memory_rss_mb"], (int, float))

    # Validate sensible values
    assert body["uptime_seconds"] >= 0
    assert body["total_requests"] >= 0
    assert body["log_entries"] >= 0
    assert body["memory_rss_mb"] >= 0
