"""仓级 logging 初始化验收（task repo-logging-init · TC1 · 裸 python 子进程断言）。

N-3 识别口径：pytest 进程 root 自带捕获 handler，「root 有且仅有一个本 task handler」
必须在裸 python 子进程中断言（非 pytest 进程内），否则 pytest 捕获 handler 致计数误判。
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# D3 钉死：对齐验收启动器实证格式（验收文档 :139 逐字）
EXPECTED_FORMAT = "%(asctime)s %(name)s %(levelname)s %(message)s"

_SNIPPET = """\
import logging

import app.main  # noqa: F401  # import 期副作用即仓级 logging 初始化

root = logging.getLogger()
print("HANDLER_COUNT=%d" % len(root.handlers))
print("ROOT_LEVEL=%s" % logging.getLevelName(root.level))
print("FORMATS=%r" % [getattr(h.formatter, "_fmt", None) for h in root.handlers])
"""


def _run_bare_import(env_extra: dict[str, str] | None = None) -> str:
    """裸 python 子进程 import app.main 并返回 stdout（env 受控 · 默认剔除 OPS_LOG_LEVEL）。"""
    env = dict(os.environ)
    env.pop("OPS_LOG_LEVEL", None)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [sys.executable, "-c", _SNIPPET],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, f"子进程 import app.main 失败：\n{proc.stderr}"
    return proc.stdout


def _parse(stdout: str) -> dict[str, str]:
    keys = {"HANDLER_COUNT", "ROOT_LEVEL", "FORMATS"}
    out: dict[str, str] = {}
    for line in stdout.splitlines():
        key, sep, value = line.partition("=")
        if sep and key in keys:
            out[key] = value
    return out


def test_default_root_handler_info() -> None:
    """TC1 默认组：root 恰一个本 task handler · level=INFO · format 钉死。"""
    result = _parse(_run_bare_import())
    assert result["HANDLER_COUNT"] == "1", result
    assert result["ROOT_LEVEL"] == "INFO", result
    assert EXPECTED_FORMAT in result["FORMATS"], result


def test_env_override_debug() -> None:
    """TC1 env 覆盖组：OPS_LOG_LEVEL=DEBUG 生效（D2-A）。"""
    result = _parse(_run_bare_import({"OPS_LOG_LEVEL": "DEBUG"}))
    assert result["HANDLER_COUNT"] == "1", result
    assert result["ROOT_LEVEL"] == "DEBUG", result


def test_invalid_env_falls_back_to_info() -> None:
    """TC1 非法值回退组：OPS_LOG_LEVEL 无法识别 fail-closed 回 INFO（D2-A）。"""
    result = _parse(_run_bare_import({"OPS_LOG_LEVEL": "BOGUS"}))
    assert result["HANDLER_COUNT"] == "1", result
    assert result["ROOT_LEVEL"] == "INFO", result
