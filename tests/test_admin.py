import logging
from datetime import datetime, timezone

from src.admin_service.main import app, _memory_handler


def test_admin_routes_registered():
    paths = {route.path for route in app.routes}
    assert "/admin/logs" in paths
    assert "/admin/metrics" in paths
    assert "/admin/users/count" in paths
    assert "/admin/content/{video_id}" in paths


def test_memory_handler_capacity():
    assert _memory_handler.capacity == 200


def test_log_entry_format():
    record = logging.LogRecord(
        name="test.logger",
        level=logging.WARNING,
        pathname="",
        lineno=0,
        msg="something happened",
        args=(),
        exc_info=None,
    )
    entry = {
        "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
        "level": record.levelname,
        "logger": record.name,
        "message": record.getMessage(),
    }
    assert entry["level"] == "WARNING"
    assert entry["logger"] == "test.logger"
    assert entry["message"] == "something happened"
    assert entry["timestamp"].endswith("+00:00")
