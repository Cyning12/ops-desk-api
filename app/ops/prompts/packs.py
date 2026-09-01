"""Prompt Pack 层（Host C2 · comms pack）。

纯函数层：
- render_pack("comms", ...) 装配 comms system 槽位链（kit FRAGMENT 真值注入 +
  task 字段清单 + 对话策略 + 禁令条文）；
- route_intent(text) 规则/关键词意图路由判定器，严格二值 "comms" | "product"。

边界（SPEC 06 §4/§6/§8/§9 + task host-comms-prompt-pack 00 定夺）：
- 不新增 HTTP 路由；不 import app.ops.session / chat 流路径；
- product 侧零影响：不改动 render() / get_template() / TEMPLATES；
- FRAGMENT 运行时读仓内真值文件 docs/harness/prompts/（单一真值源，禁止拷贝漂移），
  文件缺失 → 明确报错，不静默降级为空槽位。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

RouteIntent = Literal["comms", "product"]

# 仓内 FRAGMENT 真值（SoT）。运行时读文件：注入内容即真值文件本身，无拷贝故无漂移。
_FRAGMENT_DIR = Path("docs/harness/prompts")
_FRAGMENT_FILES: tuple[str, ...] = (
    "FRAGMENT_00_delegate_only_v1_zh.md",
    "FRAGMENT_hat_reanchor_v1_zh.md",
)
# app/ops/prompts/packs.py → parents[3] = 仓根
_REPO_ROOT = Path(__file__).resolve().parents[3]

# comms pack 元信息（SPEC 06 §9 session 隔离落到元信息标记；capability 仅声明不调用）
PACK_NAME = "comms"
PACK_VERSION = "v1"
PACK_SESSION_SCOPE = "comms"
PACK_CAPABILITIES: tuple[str, ...] = ("harness.verify", "harness.task_lint")

# 槽位：调用方传入 slots 时必须包含以下键（缺 → 明确报错，见 failure_paths「pack 槽位缺字段」）
REQUIRED_SLOTS: tuple[str, ...] = ("task_slug", "hat_id")

# task 模板字段清单（comms 起草 task 时必须收集/产出的字段）
_TASK_FIELD_CHECKLIST = """## task 字段清单（起草 task 时必须覆盖）

- task_slug / git_branch / implement_repo
- 范围（scope）与非范围（out of scope）
- 验收标准（可机械判定的勾选条）
- failure_paths（触发 / 行为 / 可重试 / 用户可见）
- 人工闸表（human_gate_id / status / blocks_hats）
- test_strategy 与 test_strategy_note
- graph_delta / wiki_delta / review_hat
"""

# 对话策略（澄清 → 起草 → 提示人闸）
_DIALOG_POLICY = """## 对话策略

1. 澄清：先确认立项意图、范围与非范围；信息不足时追问，不臆造。
2. 起草：按 task 字段清单产出 task 草稿与 invoke 草稿（写盘边界见禁令）。
3. 提示人闸：草稿完成后列出缺失闸清单与「待人签」提示，交人确认。
"""

# 禁令条文（SPEC 06 §3 禁令 B / §5 写盘边界 / §8 Skills≠verify）
_PROHIBITIONS = """## 禁令（不可逾越）

- **永不签发 human_gate**：不得输出「已签收 / approved / 已代签」字样；
  闸状态真值在 task 表，仅可输出「待人签」提示与缺失闸清单。
- **写盘仅 docs/tasks/（active/draft）+ invoke 草稿（docs/harness/invokes/by-task/）**；
  禁写 app/、tests/、图谱 yaml、SPEC 正文。
- **Skills ≠ verify**：Skill 是提示层纪律，不是机械闸；
  不得以「已加载 Skill」宣称 verify 已完成，闸状态以 CLI verify + task 表为准。
"""

# 意图路由关键词表（SPEC 06 §4 例示作种子：立项 / 开 task / 写 SPEC / 拆波次 / 走 harness 流程）
# 原则：默认 product；词表外的业务措辞一律回退 product（宁可漏进 comms）。
_COMMS_KEYWORDS: tuple[str, ...] = (
    "立项",
    "开task",
    "开 task",
    "开个task",
    "开个 task",
    "起草task",
    "起草 task",
    "写spec",
    "写 spec",
    "写个spec",
    "写个 spec",
    "起草spec",
    "起草 spec",
    "拆波次",
    "走harness",
    "走 harness",
    "harness流程",
    "harness 流程",
)


class PromptPackError(RuntimeError):
    """pack 装配失败（真值文件缺失 / 槽位缺字段等），不静默降级。"""


class PromptPackNotFoundError(KeyError):
    """未知 pack 名。"""


@dataclass(frozen=True)
class PromptPack:
    """渲染完成的 Prompt Pack（system + 元信息）。"""

    name: str
    version: str
    session_scope: str
    capabilities: tuple[str, ...]
    system_prompt: str


def _repo_root(base_dir: Path | None) -> Path:
    return Path(base_dir) if base_dir is not None else _REPO_ROOT


def _read_fragment(root: Path, filename: str) -> str:
    path = root / _FRAGMENT_DIR / filename
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PromptPackError(f"FRAGMENT 真值文件缺失或不可读: {path}") from exc
    if not content.strip():
        raise PromptPackError(f"FRAGMENT 真值文件为空: {path}")
    return content.strip()


def _render_comms_system(root: Path, slots: dict[str, str] | None) -> str:
    fragments = [_read_fragment(root, name) for name in _FRAGMENT_FILES]
    parts = [
        "你是 Ops Desk Host 的沟通轨 Agent（comms pack）。"
        "职责：立项沟通与 task/SPEC 草稿协助；以下为纪律片段与边界条文，须全部遵守。",
        *fragments,
        _TASK_FIELD_CHECKLIST.strip(),
        _DIALOG_POLICY.strip(),
        _PROHIBITIONS.strip(),
    ]
    text = "\n\n".join(parts)
    if slots is not None:
        missing = [key for key in REQUIRED_SLOTS if key not in slots]
        if missing:
            raise PromptPackError(f"comms pack 缺少槽位: {', '.join(missing)}")
        for name, content in slots.items():
            block = (content or "").strip()
            if block:
                text = f"{text}\n\n<!-- slot:{name} -->\n{block}"
    return text


def render_pack(
    pack_name: str,
    *,
    slots: dict[str, str] | None = None,
    base_dir: Path | str | None = None,
) -> PromptPack:
    """装配指定 pack；当前仅 "comms"。

    - FRAGMENT 内容运行时读仓内真值文件，缺失/为空 → PromptPackError；
    - 传入 slots 时必须含 REQUIRED_SLOTS 全部键，缺 → 报错并点名缺哪个槽位；
    - 未知 pack 名 → PromptPackNotFoundError。
    """
    if pack_name != PACK_NAME:
        raise PromptPackNotFoundError(pack_name)
    root = _repo_root(Path(base_dir) if base_dir is not None else None)
    return PromptPack(
        name=PACK_NAME,
        version=PACK_VERSION,
        session_scope=PACK_SESSION_SCOPE,
        capabilities=PACK_CAPABILITIES,
        system_prompt=_render_comms_system(root, slots),
    )


def route_intent(text: object) -> RouteIntent:
    """意图路由判定器（规则/关键词纯函数）。

    严格二值：显式立项意图 → "comms"；其余（默认 / 空 / None / 非字符串 / 模糊 /
    任何异常）→ "product"（宁可漏进 comms，不可把业务答误入立项流程）。
    """
    try:
        if not isinstance(text, str):
            return "product"
        normalized = text.strip().lower()
        if not normalized:
            return "product"
        if any(keyword in normalized for keyword in _COMMS_KEYWORDS):
            return "comms"
    except Exception:  # 判定器永不外抛，异常一律回退 product
        return "product"
    return "product"
