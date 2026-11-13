"""P0' T1 negative regression: unauthenticated demo WebSocket endpoint removed.

Guards that /api/ops/chat/ws stays absent (issue #23 R4 ruling P5/A3-1).
If anyone re-registers this endpoint, this test must fail.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

_WS_PATH = "/api/ops/chat/ws"


def test_chat_ws_route_absent_from_route_table() -> None:
    paths = [getattr(r, "path", "") for r in app.routes]
    assert _WS_PATH not in paths, f"{_WS_PATH} must not be registered (P0' T1 removed)"


def test_chat_ws_connect_rejected() -> None:
    with TestClient(app) as tc, pytest.raises(Exception), tc.websocket_connect(_WS_PATH):  # noqa: B017
        pass  # pragma: no cover - connecting successfully means failure
