"""N-40-1 logging 初始化窗口验收（task n40-1-log-init-window · TC1–TC3 · 裸 python 子进程探针）。

窗口：app/main.py 的 app 包 import 链先于模块级 _init_logging() —— 修复前窗口内
WARNING+ 走 logging.lastResort 裸格式（无 asctime/name/level）、INFO 整行被吞；
修复后首个 app 包 import 之前 root handler 已就位，窗口发射以钉死格式落 stderr。

探针纪律（承 repo-logging-init CLOSE 偏差 4）：PYTHONPATH=仓根 + 显式 env，不赌时机。
env 口径：OPS_CAPABILITY_PERSISTENCE="" 显式空串 ≡ 未设（persistence.py:39
or MODE_NULL 同一路径），且 load_dotenv 不覆盖既有 env —— 防仓根 .env 渗入致假绿/假红。
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# 钉死格式（app/main.py:14 逐字 · 台账 grep 口径零 diff）
ASCTIME_RE = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}"
PERSISTENCE_LOGGER = "app.ops.capability.persistence"

_SNIPPET = """\
import logging

import app.main  # noqa: F401  # import 期副作用即仓级 logging 初始化

print("ROOT_LEVEL=%s" % logging.getLevelName(logging.getLogger().level))
"""


def _run_bare_import(env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """裸 python 子进程 import app.main（PYTHONPATH=仓根 · env 受控 · 默认剔 OPS_LOG_LEVEL）。"""
    env = dict(os.environ)
    env.pop("OPS_LOG_LEVEL", None)
    env["PYTHONPATH"] = str(REPO_ROOT)
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
    return proc


def _formatted_line_re(level: str, logger: str, msg_substr: str) -> re.Pattern[str]:
    """钉死格式行：<asctime> <logger> <LEVEL> …msg_substr…"""
    return re.compile(
        rf"^{ASCTIME_RE} {re.escape(logger)} {level} .*{re.escape(msg_substr)}",
        re.MULTILINE,
    )


def _assert_no_bare_line(stderr: str, msg_substr: str) -> None:
    """含 msg_substr 的行若存在必须是钉死格式（不得以 lastResort 裸格式出现）。"""
    for line in stderr.splitlines():
        if msg_substr in line:
            assert re.match(rf"^{ASCTIME_RE} ", line), f"裸格式行存续：{line!r}"


# ---------------------------------------------------------------- TC1 窗口格式反转（核心）


def test_tc1_window_warning_uses_pinned_format() -> None:
    """TC1：默认 env（显式清 OPS_CAPABILITY_PERSISTENCE）窗口 WARNING 以钉死格式落 stderr。

    修复前：lastResort 裸格式（红）；修复后：<asctime> app.ops.capability.persistence WARNING …（绿）。
    """
    proc = _run_bare_import({"OPS_CAPABILITY_PERSISTENCE": ""})
    assert _formatted_line_re("WARNING", PERSISTENCE_LOGGER, "能力层持久化未配置").search(
        proc.stderr
    ), f"缺钉死格式 WARNING 行：\n{proc.stderr}"
    _assert_no_bare_line(proc.stderr, "能力层持久化未配置")


def test_tc1_window_invalid_persistence_error_formatted() -> None:
    """TC1 补组（R1 N-1 回填 · 发射点四处计全）：非法 OPS_CAPABILITY_PERSISTENCE 值时
    persistence.py:60-64 ERROR 与 :65-68 WARNING 两行同窗发射，均须钉死格式。"""
    proc = _run_bare_import({"OPS_CAPABILITY_PERSISTENCE": "bogus"})
    assert _formatted_line_re("ERROR", PERSISTENCE_LOGGER, "无法识别（仅 db / memory）").search(
        proc.stderr
    ), f"缺钉死格式 ERROR 行：\n{proc.stderr}"
    assert _formatted_line_re("WARNING", PERSISTENCE_LOGGER, "能力层持久化未配置").search(
        proc.stderr
    ), f"缺钉死格式 WARNING 行：\n{proc.stderr}"
    _assert_no_bare_line(proc.stderr, "无法识别（仅 db / memory）")
    _assert_no_bare_line(proc.stderr, "能力层持久化未配置")


# ---------------------------------------------------------------- TC2 窗口 INFO 可见性


def test_tc2_window_info_visible_db_mode() -> None:
    """TC2：OPS_CAPABILITY_PERSISTENCE=db 时 persistence.py:48 INFO 行钉死格式可见。

    修复前：lastResort 门槛 WARNING，INFO 整行被吞（红）；修复后可见（绿）。
    """
    proc = _run_bare_import({"OPS_CAPABILITY_PERSISTENCE": "db"})
    assert _formatted_line_re(
        "INFO", PERSISTENCE_LOGGER, "能力层持久化：db（跨实例防重 + 回执落库）"
    ).search(proc.stderr), f"窗口 INFO 行不可见或非钉死格式：\n{proc.stderr}"


def test_tc2_window_warning_formatted_memory_mode() -> None:
    """TC2 memory 子组（R1 N-4 口径）：断言对象为 persistence.py:54 WARNING 格式化行（非 INFO）。"""
    proc = _run_bare_import({"OPS_CAPABILITY_PERSISTENCE": "memory"})
    assert _formatted_line_re(
        "WARNING", PERSISTENCE_LOGGER, "能力层持久化：memory（进程内）"
    ).search(proc.stderr), f"缺钉死格式 memory WARNING 行：\n{proc.stderr}"
    _assert_no_bare_line(proc.stderr, "能力层持久化：memory（进程内）")


# ---------------------------------------------------------------- TC3 OPS_LOG_LEVEL 回归组


def test_tc3_invalid_log_level_falls_back_info_with_alert() -> None:
    """TC3 非法值组：OPS_LOG_LEVEL=BOGUS → INFO fail-closed + 格式化 ERROR 告警行存续
    （app/main.py:31-35 口径逐字不动），且窗口 WARNING 亦钉死格式。"""
    proc = _run_bare_import({"OPS_LOG_LEVEL": "BOGUS", "OPS_CAPABILITY_PERSISTENCE": ""})
    assert "ROOT_LEVEL=INFO" in proc.stdout, proc.stdout
    assert _formatted_line_re("ERROR", "app.main", "OPS_LOG_LEVEL='BOGUS' 无法识别").search(
        proc.stderr
    ), f"格式化 ERROR 告警行未存续：\n{proc.stderr}"
    assert _formatted_line_re("WARNING", PERSISTENCE_LOGGER, "能力层持久化未配置").search(
        proc.stderr
    ), f"窗口 WARNING 非钉死格式：\n{proc.stderr}"


def test_tc3_debug_effective() -> None:
    """TC3 DEBUG 组：OPS_LOG_LEVEL=DEBUG 生效。"""
    proc = _run_bare_import({"OPS_LOG_LEVEL": "DEBUG", "OPS_CAPABILITY_PERSISTENCE": ""})
    assert "ROOT_LEVEL=DEBUG" in proc.stdout, proc.stdout


def test_tc3_default_info() -> None:
    """TC3 缺省组：OPS_LOG_LEVEL 缺省 → INFO。"""
    proc = _run_bare_import({"OPS_CAPABILITY_PERSISTENCE": ""})
    assert "ROOT_LEVEL=INFO" in proc.stdout, proc.stdout
