"""Host C3 · 受控 task 写盘服务（task writer · 纯服务层）。

SPEC：docs/spec/agent-infra/06_host_comms_boundary_spec_v0.md（signed）§5/§6/§7；
Task：docs/tasks/active/task_host_comms_task_writer.md（00 定夺钉死）；
R1 审查：docs/harness/reviews/task_host_comms_task_writer_audit_R1_20260901.md
（非阻塞 5 条逐项处置见下）。

钉死项：

- **纯服务层 · 不是 Gateway Capability**：不进 registry/manifest · 无 HTTP 路由 ·
  不触发 SPEC §7 白名单变更；调用方仅限仓内代码（接线留 C4/Host）。
- API 形态：plan_task_write(slug, content, *, kind, repo_root, overwrite) ->
  WritePlan（路径解析 + allowlist 校验 + dry-run diff 预览）；
  apply_task_write(plan, *, confirmed=False) -> WriteResult
  （confirmed=False → 不落盘返回 dry-run 结果；confirmed=True 即人确认后落盘，
  SPEC §6 C3 前置「落盘前必须人确认」的服务层等价物）。
- allowlist **仅**三处（realpath 前缀判定 · R1 非阻塞③防 symlink/.. 逃逸）：
  docs/tasks/active/ · docs/tasks/draft/（不存在可创建）·
  docs/harness/invokes/by-task/<slug>/。其余一律 path_not_allowed
  （app/ 永久 · tests/ · 图谱 yaml · SPEC 正文 · 任意逃逸）。
- 文件名约束：task 文件 task_<slug>.md（slug kebab-case 校验）；
  invoke 文件 invoke_<slug>.md（invoke_* glob）；kind 推导目录唯一，
  plan 携带的 kind 与目标路径推导不一致 → path_not_allowed 归并校验错误
  （R1 非阻塞④ · 与 failure_paths 同形态）。
- 禁代签机械挡（宁严勿宽 · R1 非阻塞①）：content 人工闸节内任何含 HG- 且
  含 approved 词的行一律拒绝（invalid_content）；占位例外不开放——00 代签走
  人工授权流程直接改 task 表，**不经** comms 写盘，严挡不误伤合法流程。
- 结构自检：task 类须含 Harness 元信息表 / 人工闸节 / 验收标准节；
  invoke 类须含 hat_id/task_slug 字段表标记；缺节 → invalid_structure
  指出缺节。**不真跑 npx lint**（CI 不断网）。
- overwrite：默认不覆盖已存在文件（exists 拒绝）；须显式 overwrite=True
  且仍走 confirmed；dry-run diff 含新旧差异。
- 原子写：临时文件（同目录 mkstemp）+ os.replace rename；IO 失败清理临时
  文件后上抛 io_failed，不留半截文件。
- WritePlan 防伪造（R1 非阻塞② · 双保险）：apply 复跑全部校验（allowlist /
  结构 / 禁代签 / exists）且 WritePlan 携带 sha256 校验摘要，手工构造或篡改
  plan → plan_tampered 拒绝。
- 无删文件/移动文件能力；不写 docs/tasks/done/（归档走 00 CLOSE 流程）。
"""

from __future__ import annotations

import contextlib
import difflib
import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# kind 三形态（00 定夺 allowlist 三目录的一一映射；目录由 kind+slug 唯一推导）
WriteKind = Literal["task_active", "task_draft", "invoke"]

KIND_TASK_ACTIVE: WriteKind = "task_active"
KIND_TASK_DRAFT: WriteKind = "task_draft"
KIND_INVOKE: WriteKind = "invoke"
_KINDS: tuple[str, ...] = (KIND_TASK_ACTIVE, KIND_TASK_DRAFT, KIND_INVOKE)

# task 类 allowlist 目录（相对仓根 · 字面量钉死）
_TASK_DIRS: dict[str, str] = {
    KIND_TASK_ACTIVE: "docs/tasks/active",
    KIND_TASK_DRAFT: "docs/tasks/draft",
}
_INVOKE_BASE = "docs/harness/invokes/by-task"

# slug kebab-case（小写字母/数字 + 连字符；天然排除 /、..、反斜杠、绝对路径）
_SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

# 结构自检（task 类必备三节；re.M 行首锚定）
_TASK_REQUIRED_SECTIONS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^## Harness 元信息", re.M), "Harness 元信息表（## Harness 元信息）"),
    (re.compile(r"^#{2,3} 人工闸", re.M), "人工闸节（##/### 人工闸）"),
    (re.compile(r"^## 验收标准", re.M), "验收节（## 验收标准）"),
)
# 结构自检（invoke 类最小字段表标记；30 定，对齐既有 invoke 文件形态）
_INVOKE_REQUIRED_MARKERS: tuple[str, ...] = ("| hat_id |", "| task_slug |")

# 人工闸节截取：节头（##/### 人工闸）到下一个二级标题（或文末）
_GATE_HEAD_RE = re.compile(r"^#{2,3} 人工闸.*$", re.M)
_NEXT_H2_RE = re.compile(r"^## ", re.M)
# 禁代签词（宁严：人工闸节内含 HG- 的行再含本词即拒；大小写不敏感）
_APPROVED_RE = re.compile(r"\bapproved\b", re.IGNORECASE)


class TaskWriterError(RuntimeError):
    """受控错误；message 采用 <family>: <detail> 前缀族。

    前缀族：invalid_args: / path_not_allowed: / invalid_content: /
    invalid_structure: / exists: / plan_tampered: / io_failed:
    （与 harness_cli 的 invalid_args: / cli_failed: 同族风格）。
    """


@dataclass(frozen=True)
class WritePlan:
    """plan_task_write 产出的写盘计划（dry-run 预览载体 · 校验摘要防伪造）。

    checksum = sha256(kind/slug/repo_root/rel_path/abs_path/content/overwrite)，
    apply_task_write 复算比对；任何字段被篡改或 plan 被手工构造 → plan_tampered。
    """

    kind: str
    slug: str
    repo_root: str
    rel_path: str
    abs_path: str
    content: str
    overwrite: bool
    existed: bool
    diff: str
    checksum: str


@dataclass(frozen=True)
class WriteResult:
    """apply_task_write 结果。written=False 即 dry-run（未落盘）。"""

    plan: WritePlan
    confirmed: bool
    written: bool


def _plan_checksum(
    kind: str,
    slug: str,
    repo_root: str,
    rel_path: str,
    abs_path: str,
    content: str,
    overwrite: bool,
) -> str:
    """WritePlan 校验摘要（字段 canonical JSON 的 sha256）。"""
    payload = json.dumps(
        {
            "kind": kind,
            "slug": slug,
            "repo_root": repo_root,
            "rel_path": rel_path,
            "abs_path": abs_path,
            "content": content,
            "overwrite": overwrite,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _resolve_repo_root(repo_root: Path | str | None) -> Path:
    if repo_root is None:
        # app/ops/capability/task_writer.py → parents[3] = 仓根（同 packs.py 约定）
        return Path(__file__).resolve().parents[3]
    return Path(repo_root).resolve()


def _resolve_target(kind: str, slug: str, repo_root: Path) -> tuple[Path, str]:
    """kind+slug 唯一推导目标路径并做 realpath 前缀判定。

    判定方式（R1 非阻塞③）：目标经 .resolve() 解析符号链接后，须落在
    **字面拼接**的 allowlist 目录之下——allowlist 目录本身被 symlink 替换时，
    resolved 目标与字面根不匹配 → 拒绝。
    """
    if kind not in _KINDS:
        raise TaskWriterError(f"invalid_args: 未知 kind: {kind!r}（允许: {' / '.join(_KINDS)}）")
    if not isinstance(slug, str) or not _SLUG_RE.match(slug):
        raise TaskWriterError(f"invalid_args: slug 须 kebab-case（小写字母/数字/连字符）: {slug!r}")
    if kind == KIND_INVOKE:
        allow_rel = f"{_INVOKE_BASE}/{slug}"
        rel_path = f"{allow_rel}/invoke_{slug}.md"
    else:
        allow_rel = _TASK_DIRS[kind]
        rel_path = f"{allow_rel}/task_{slug}.md"
    # 字面 allowlist 根（不经文件系统解析，防 symlink 替身）
    allow_literal = repo_root / allow_rel
    target = (repo_root / rel_path).resolve()
    if not target.is_relative_to(allow_literal):
        raise TaskWriterError(f"path_not_allowed: 目标越出 allowlist（{allow_rel}/）: {rel_path}")
    return target, rel_path


def _check_structure(kind: str, content: str) -> None:
    """最小结构自检；缺节 → invalid_structure 并点名缺节。"""
    if kind == KIND_INVOKE:
        missing = [m for m in _INVOKE_REQUIRED_MARKERS if m not in content]
        if missing:
            raise TaskWriterError(
                f"invalid_structure: invoke 缺最小字段表标记: {', '.join(missing)}"
            )
        return
    missing = [label for pattern, label in _TASK_REQUIRED_SECTIONS if not pattern.search(content)]
    if missing:
        raise TaskWriterError(f"invalid_structure: 缺必备节: {'；'.join(missing)}")


def _check_no_proxy_signoff(content: str) -> None:
    """禁代签机械挡（宁严勿宽 · SPEC §3 禁令 B / §6）。

    人工闸节内任何含 HG- 且含 approved 词的行一律拒绝（无占位例外）；
    00 代签不经 comms 写盘，严挡不误伤合法流程（R1 非阻塞①）。
    """
    head = _GATE_HEAD_RE.search(content)
    if head is None:
        return  # 无人工闸节：task 类由结构自检拦截；invoke 类不设人工闸节
    tail = content[head.end() :]
    nxt = _NEXT_H2_RE.search(tail)
    section = tail[: nxt.start()] if nxt else tail
    for line in section.splitlines():
        if "HG-" in line and _APPROVED_RE.search(line):
            raise TaskWriterError(
                "invalid_content: 人工闸节内 HG-* 行含 approved 一律拒写"
                f"（宁严 · 禁代签 SPEC §6）: {line.strip()!r}"
            )


def _unified_diff(rel_path: str, old: str, new: str) -> str:
    """dry-run diff 预览（新文件 old 为空串 · 已存在文件含新旧差异）。"""
    lines = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        fromfile=f"a/{rel_path}",
        tofile=f"b/{rel_path}",
        lineterm="",
    )
    return "\n".join(lines)


def plan_task_write(
    slug: str,
    content: str,
    *,
    kind: WriteKind,
    repo_root: Path | str | None = None,
    overwrite: bool = False,
) -> WritePlan:
    """路径解析 + allowlist/结构/禁代签校验 + dry-run diff 预览（不落盘）。

    - kind/slug 非法 → invalid_args；越 allowlist → path_not_allowed；
    - 结构缺节 → invalid_structure；人工闸节含 approved → invalid_content；
    - 目标已存在且未显式 overwrite=True → exists 拒绝；
    - 本函数**零落盘副作用**（不创建目录 · 不写文件）。
    """
    if not isinstance(content, str) or not content.strip():
        raise TaskWriterError("invalid_args: content 必须为非空字符串")
    root = _resolve_repo_root(repo_root)
    target, rel_path = _resolve_target(kind, slug, root)
    _check_structure(kind, content)
    _check_no_proxy_signoff(content)
    existed = target.exists()
    if existed and not overwrite:
        raise TaskWriterError(f"exists: 目标已存在且未显式 overwrite=True: {rel_path}")
    old = target.read_text(encoding="utf-8") if existed else ""
    return WritePlan(
        kind=kind,
        slug=slug,
        repo_root=str(root),
        rel_path=rel_path,
        abs_path=str(target),
        content=content,
        overwrite=overwrite,
        existed=existed,
        diff=_unified_diff(rel_path, old, content),
        checksum=_plan_checksum(kind, slug, str(root), rel_path, str(target), content, overwrite),
    )


def apply_task_write(plan: WritePlan, *, confirmed: bool = False) -> WriteResult:
    """应用写盘计划；confirmed=False → dry-run 不落盘，confirmed=True → 原子落盘。

    不完全信任 plan（R1 非阻塞②）：先比对校验摘要（plan_tampered），再复跑
    全部校验（kind↔路径一致性 / allowlist realpath / 结构 / 禁代签 / exists）。
    confirmed=True 落盘时按 allowlist 目录 mkdir parents 创建（非 allowlist
    目录到此步必已被拒，零越界副作用）；原子写 = 同目录临时文件 + os.replace，
    IO 失败清理临时文件后上抛 io_failed，不留半截文件。
    """
    if not isinstance(plan, WritePlan):
        raise TaskWriterError(
            f"invalid_args: plan 必须为 WritePlan（仅 plan_task_write 产出）: {type(plan)!r}"
        )
    expected = _plan_checksum(
        plan.kind,
        plan.slug,
        plan.repo_root,
        plan.rel_path,
        plan.abs_path,
        plan.content,
        plan.overwrite,
    )
    if plan.checksum != expected:
        raise TaskWriterError(
            "plan_tampered: WritePlan 校验摘要不符（疑似手工构造或篡改；请重新走 plan_task_write）"
        )
    # 复跑校验：kind+slug 推导目标须与 plan 一致（kind/目录错配归并 path_not_allowed）
    root = _resolve_repo_root(plan.repo_root)
    target, rel_path = _resolve_target(plan.kind, plan.slug, root)
    if rel_path != plan.rel_path or str(target) != plan.abs_path:
        raise TaskWriterError(
            f"path_not_allowed: plan 目标与 kind/slug 推导不一致: {plan.rel_path!r}"
        )
    _check_structure(plan.kind, plan.content)
    _check_no_proxy_signoff(plan.content)
    if target.exists() and not plan.overwrite:
        raise TaskWriterError(f"exists: 目标已存在且未显式 overwrite=True: {plan.rel_path}")
    if not confirmed:
        return WriteResult(plan=plan, confirmed=False, written=False)
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(plan.content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, target)
    except OSError as exc:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise TaskWriterError(f"io_failed: 写盘失败（已清理临时文件 · 未落半截）: {exc}") from exc
    return WriteResult(plan=plan, confirmed=True, written=True)
