"""tracing · Generation I/O 截断与 no-op。"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.ops import tracing


def test_update_generation_io_noop_when_tracing_off(monkeypatch):
    monkeypatch.setattr(tracing, "tracing_enabled", lambda: False)
    with patch("langfuse.get_client") as get_client:
        tracing.update_current_generation_io(input="a", output="b")
        get_client.assert_not_called()


def test_update_generation_io_truncates(monkeypatch):
    monkeypatch.setattr(tracing, "tracing_enabled", lambda: True)
    monkeypatch.setattr(tracing, "generation_io_truncate_chars", lambda: 8)
    client = MagicMock()
    with patch("langfuse.get_client", return_value=client):
        tracing.update_current_generation_io(input="0123456789", output="abcdefghij")
    kwargs = client.update_current_generation.call_args.kwargs
    assert kwargs["input"].endswith("…")
    assert len(kwargs["input"]) == 8
    assert kwargs["output"].endswith("…")
