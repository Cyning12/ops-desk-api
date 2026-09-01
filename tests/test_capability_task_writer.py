"""Host C3 · 受控 task 写盘服务测试（tmp_path 沙箱 · 纯函数/纯文件语义）。

不真跑 npx、不触网。覆盖（对照 task 验收标准）：
- allowlist 参数化命中/拒绝（三目录可写 · slug 注入形态全拒 · symlink 逃逸拒）；
- dry-run 默认不落盘（且零目录副作用）；confirmed=True 落盘且内容一致；
- 禁代签机械挡（宁严：人工闸节内 approved 一律拒 · overwrite 注入 approved 侧路）；
- 结构自检缺节拒绝；文件名/kind 错配归并校验错误；overwrite 默认拒 + diff 含差异；
- 原子写（mock os.replace 失败不留半截 · 临时文件同目录）；plan 伪造/篡改拒绝；
- 不进 Gateway registry/manifest（AST + grep + 活注册表断言）。
"""

from __future__ import annotations

import ast
import dataclasses
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.ops.capability.task_writer import (
    KIND_INVOKE,
    KIND_TASK_ACTIVE,
    KIND_TASK_DRAFT,
    TaskWriterError,
    WritePlan,
    _plan_checksum,
    apply_task_write,
    plan_task_write,
)

_SLUG = "my-task"

_VALID_TASK = """# Task：x

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `x` |

### 人工闸

| human_gate_id | status |
|---|---|
| HG-TASK-DRAFT | pending |
| HG-AUDIT-R1 | pending |

## 验收标准

- [ ] a
"""

_VALID_INVOKE = """# Invoke：30 · x

| 字段 | 值 |
|---|---|
| hat_id | 30 |
| task_slug | x |
"""


@pytest.fixture()
def repo_root(tmp_path: Path) -> Path:
    """最小仓面：仅 docs/tasks/active 存在（draft/invokes 由服务创建）。"""
    (tmp_path / "docs/tasks/active").mkdir(parents=True)
    return tmp_path


# ---------------------------------------------------------------- allowlist


class TestAllowlist:
    @pytest.mark.parametrize(
        ("kind", "rel"),
        [
            (KIND_TASK_ACTIVE, "docs/tasks/active/task_my-task.md"),
            (KIND_TASK_DRAFT, "docs/tasks/draft/task_my-task.md"),
            (KIND_INVOKE, "docs/harness/invokes/by-task/my-task/invoke_my-task.md"),
        ],
    )
    def test_hit(self, repo_root: Path, kind: str, rel: str) -> None:
        content = _VALID_INVOKE if kind == KIND_INVOKE else _VALID_TASK
        plan = plan_task_write(_SLUG, content, kind=kind, repo_root=repo_root)
        assert plan.rel_path == rel
        assert plan.existed is False

    @pytest.mark.parametrize(
        "slug",
        [
            "../app",  # .. 逃逸
            "..",  # 裸 ..
            "a/b",  # 路径分隔符（注入子目录）
            "/etc/passwd",  # 绝对路径
            r"a\b",  # 反斜杠
            "Foo_Bar",  # 大写 + 下划线（非 kebab）
            "a..b",  # 内嵌 ..
            "",  # 空
            "-lead",  # 连字符开头
            "trail-",  # 连字符结尾
            "a--b",  # 连续连字符
        ],
    )
    def test_reject_bad_slug(self, repo_root: Path, slug: str) -> None:
        with pytest.raises(TaskWriterError, match="invalid_args"):
            plan_task_write(slug, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)

    def test_reject_unknown_kind(self, repo_root: Path) -> None:
        with pytest.raises(TaskWriterError, match="invalid_args"):
            plan_task_write(_SLUG, _VALID_TASK, kind="task_done", repo_root=repo_root)  # type: ignore[arg-type]

    def test_reject_non_str_content(self, repo_root: Path) -> None:
        with pytest.raises(TaskWriterError, match="invalid_args"):
            plan_task_write(_SLUG, None, kind=KIND_TASK_ACTIVE, repo_root=repo_root)  # type: ignore[arg-type]

    def test_symlink_escape_rejected(self, repo_root: Path, tmp_path: Path) -> None:
        """allowlist 目录被 symlink 替换指向仓外 → realpath 前缀判定拒绝。"""
        evil = tmp_path / "evil"
        evil.mkdir()
        (repo_root / "docs/tasks/active").rmdir()  # 替换为 symlink
        os.symlink(evil, repo_root / "docs/tasks/active")
        with pytest.raises(TaskWriterError, match="path_not_allowed"):
            plan_task_write("escape", _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        assert not (evil / "task_escape.md").exists()

    def test_non_allowlist_dir_never_created(self, repo_root: Path) -> None:
        """被拒的写盘零副作用：非 allowlist 目录一律不创建。"""
        with pytest.raises(TaskWriterError):
            plan_task_write("../done", _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        assert not (repo_root / "docs/tasks/done").exists()
        assert not (repo_root / "docs/tasks/draft").exists()


# ------------------------------------------------------------- dry-run/落盘


class TestDryRunAndConfirm:
    def test_dry_run_default_no_write(self, repo_root: Path) -> None:
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        result = apply_task_write(plan)  # confirmed 默认 False
        assert result.written is False
        assert result.confirmed is False
        assert not (repo_root / plan.rel_path).exists()
        assert plan.diff  # diff 预览存在
        assert "+" in plan.diff

    def test_dry_run_no_dir_side_effect(self, repo_root: Path) -> None:
        """dry-run 连 allowlist 目录都不创建（draft/invokes 保持不存在）。"""
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_DRAFT, repo_root=repo_root)
        apply_task_write(plan, confirmed=False)
        assert not (repo_root / "docs/tasks/draft").exists()

    def test_confirmed_writes_content(self, repo_root: Path) -> None:
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        result = apply_task_write(plan, confirmed=True)
        assert result.written is True
        assert (repo_root / plan.rel_path).read_text(encoding="utf-8") == _VALID_TASK

    def test_draft_dir_created_on_confirm(self, repo_root: Path) -> None:
        """allowlist 目录可创建：docs/tasks/draft/ 不存在时 mkdir parents 创建。"""
        plan = plan_task_write("draft-one", _VALID_TASK, kind=KIND_TASK_DRAFT, repo_root=repo_root)
        apply_task_write(plan, confirmed=True)
        assert (repo_root / "docs/tasks/draft/task_draft-one.md").is_file()

    def test_invoke_nested_dir_created_on_confirm(self, repo_root: Path) -> None:
        plan = plan_task_write(_SLUG, _VALID_INVOKE, kind=KIND_INVOKE, repo_root=repo_root)
        apply_task_write(plan, confirmed=True)
        target = repo_root / "docs/harness/invokes/by-task/my-task/invoke_my-task.md"
        assert target.read_text(encoding="utf-8") == _VALID_INVOKE

    def test_plan_has_no_write_side_effect(self, repo_root: Path) -> None:
        plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_DRAFT, repo_root=repo_root)
        assert not (repo_root / "docs/tasks/draft").exists()


# ---------------------------------------------------------------- 禁代签


class TestNoProxySignoff:
    def test_gate_section_approved_rejected(self, repo_root: Path) -> None:
        bad = _VALID_TASK.replace("HG-AUDIT-R1 | pending", "HG-AUDIT-R1 | approved")
        with pytest.raises(TaskWriterError, match="invalid_content"):
            plan_task_write("t2", bad, kind=KIND_TASK_ACTIVE, repo_root=repo_root)

    def test_case_insensitive_and_note_column(self, repo_root: Path) -> None:
        """宁严：大小写不敏感；approved 出现在 HG 行说明列同样拒。"""
        bad = _VALID_TASK.replace(
            "HG-AUDIT-R1 | pending", "HG-AUDIT-R1 | pending | 已于早前 APPROVED"
        )
        with pytest.raises(TaskWriterError, match="invalid_content"):
            plan_task_write("t2", bad, kind=KIND_TASK_ACTIVE, repo_root=repo_root)

    def test_overwrite_inject_approved_side_channel(self, repo_root: Path) -> None:
        """overwrite 注入 approved 侧路：挡在内容层不在路径层，重写同样被拒。"""
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        apply_task_write(plan, confirmed=True)
        bad = _VALID_TASK.replace("HG-AUDIT-R1 | pending", "HG-AUDIT-R1 | approved")
        with pytest.raises(TaskWriterError, match="invalid_content"):
            plan_task_write(
                _SLUG, bad, kind=KIND_TASK_ACTIVE, repo_root=repo_root, overwrite=True
            )
        # 原文件未被污染
        assert (repo_root / plan.rel_path).read_text(encoding="utf-8") == _VALID_TASK

    def test_approved_outside_gate_section_allowed(self, repo_root: Path) -> None:
        """闸真值 SoT 在 task 表：人工闸节外的 approved 字样（修订记录叙述）不误伤。"""
        ok = _VALID_TASK + "\n## 修订记录\n\n| 日期 | 说明 |\n|---|---|\n| d | HG-AUDIT-R1 后补 |\n"
        plan = plan_task_write("t3", ok, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        assert plan.rel_path.endswith("task_t3.md")

    def test_apply_rechecks_signoff(self, repo_root: Path) -> None:
        """apply 复跑禁代签校验（合法 checksum 的构造 plan 也过不了内容关）。"""
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        bad_content = _VALID_TASK.replace("HG-AUDIT-R1 | pending", "HG-AUDIT-R1 | approved")
        forged = WritePlan(
            kind=plan.kind,
            slug=plan.slug,
            repo_root=plan.repo_root,
            rel_path=plan.rel_path,
            abs_path=plan.abs_path,
            content=bad_content,
            overwrite=plan.overwrite,
            existed=plan.existed,
            diff="",
            checksum=_plan_checksum(
                plan.kind,
                plan.slug,
                plan.repo_root,
                plan.rel_path,
                plan.abs_path,
                bad_content,
                plan.overwrite,
            ),
        )
        with pytest.raises(TaskWriterError, match="invalid_content"):
            apply_task_write(forged, confirmed=True)


# --------------------------------------------------------------- 结构自检


class TestStructure:
    @pytest.mark.parametrize(
        ("section", "label"),
        [
            ("## Harness 元信息", "Harness 元信息"),
            ("### 人工闸", "人工闸"),
            ("## 验收标准", "验收"),
        ],
    )
    def test_missing_section_rejected(self, repo_root: Path, section: str, label: str) -> None:
        broken = _VALID_TASK.replace(section, "## 别的节", 1)
        with pytest.raises(TaskWriterError, match="invalid_structure") as excinfo:
            plan_task_write("t4", broken, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        assert label in str(excinfo.value)

    def test_invoke_missing_marker_rejected(self, repo_root: Path) -> None:
        with pytest.raises(TaskWriterError, match="invalid_structure"):
            plan_task_write(_SLUG, "# Invoke\n\n无字段表", kind=KIND_INVOKE, repo_root=repo_root)

    def test_apply_rechecks_structure(self, repo_root: Path) -> None:
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        bad_content = _VALID_TASK.replace("## 验收标准", "## 别的节", 1)
        forged = dataclasses.replace(
            plan,
            content=bad_content,
            checksum=_plan_checksum(
                plan.kind,
                plan.slug,
                plan.repo_root,
                plan.rel_path,
                plan.abs_path,
                bad_content,
                plan.overwrite,
            ),
        )
        with pytest.raises(TaskWriterError, match="invalid_structure"):
            apply_task_write(forged, confirmed=True)


# ------------------------------------------------------------- 文件名/kind


class TestFilenameKind:
    def test_task_filename_pattern(self, repo_root: Path) -> None:
        plan = plan_task_write("a-b-c", _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        assert Path(plan.rel_path).name == "task_a-b-c.md"

    def test_invoke_filename_pattern(self, repo_root: Path) -> None:
        plan = plan_task_write("a-b", _VALID_INVOKE, kind=KIND_INVOKE, repo_root=repo_root)
        assert Path(plan.rel_path).name.startswith("invoke_")
        assert plan.rel_path.endswith(".md")

    def test_kind_path_mismatch_rejected(self, repo_root: Path) -> None:
        """kind/目录错配归并校验错误：kind=invoke 配 task 路径 → path_not_allowed。"""
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        forged = WritePlan(
            kind=KIND_INVOKE,  # kind 与路径错配
            slug=plan.slug,
            repo_root=plan.repo_root,
            rel_path=plan.rel_path,
            abs_path=plan.abs_path,
            content=plan.content,
            overwrite=plan.overwrite,
            existed=plan.existed,
            diff=plan.diff,
            checksum=_plan_checksum(
                KIND_INVOKE,
                plan.slug,
                plan.repo_root,
                plan.rel_path,
                plan.abs_path,
                plan.content,
                plan.overwrite,
            ),
        )
        with pytest.raises(TaskWriterError, match="path_not_allowed"):
            apply_task_write(forged, confirmed=True)
        assert not (repo_root / plan.rel_path).exists()


# ---------------------------------------------------------------- overwrite


class TestOverwrite:
    def test_existing_rejected_without_overwrite(self, repo_root: Path) -> None:
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        apply_task_write(plan, confirmed=True)
        with pytest.raises(TaskWriterError, match="exists"):
            plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)

    def test_overwrite_diff_contains_changes(self, repo_root: Path) -> None:
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        apply_task_write(plan, confirmed=True)
        new_content = _VALID_TASK.replace("- [ ] a", "- [ ] b")
        plan2 = plan_task_write(
            _SLUG, new_content, kind=KIND_TASK_ACTIVE, repo_root=repo_root, overwrite=True
        )
        assert plan2.existed is True
        assert "-- [ ] a" in plan2.diff  # 旧
        assert "+- [ ] b" in plan2.diff  # 新
        apply_task_write(plan2, confirmed=True)
        assert (repo_root / plan.rel_path).read_text(encoding="utf-8") == new_content

    def test_apply_race_recheck_exists(self, repo_root: Path) -> None:
        """apply 复跑 exists：plan 后文件被他人创建且未 overwrite → 拒绝。"""
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        (repo_root / plan.rel_path).write_text("other", encoding="utf-8")
        with pytest.raises(TaskWriterError, match="exists"):
            apply_task_write(plan, confirmed=True)
        assert (repo_root / plan.rel_path).read_text(encoding="utf-8") == "other"


# ----------------------------------------------------------------- 原子写


class TestAtomicWrite:
    def test_io_failure_leaves_no_partial(self, repo_root: Path) -> None:
        """os.replace 失败：目标不落半截 · 临时文件被清理 · 上抛 io_failed。"""
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        with (
            patch("app.ops.capability.task_writer.os.replace", side_effect=OSError("boom")),
            pytest.raises(TaskWriterError, match="io_failed"),
        ):
            apply_task_write(plan, confirmed=True)
        target_dir = repo_root / "docs/tasks/active"
        assert not (repo_root / plan.rel_path).exists()
        assert list(target_dir.iterdir()) == []  # 无半截目标 · 无残留临时文件

    def test_temp_file_in_same_dir_then_rename(self, repo_root: Path) -> None:
        """原子语义：临时文件同目录 mkstemp，经 os.replace rename 落目标。"""
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        captured: dict[str, object] = {}
        real_replace = os.replace

        def _spy(src: object, dst: object) -> None:
            captured["src"] = src
            captured["dst"] = dst
            real_replace(src, dst)  # type: ignore[arg-type]

        with patch("app.ops.capability.task_writer.os.replace", side_effect=_spy):
            apply_task_write(plan, confirmed=True)
        src = Path(str(captured["src"]))
        assert src.parent == Path(plan.abs_path).parent  # 同目录（rename 原子前提）
        assert src.name.startswith(f".{Path(plan.abs_path).name}.")
        assert src.name.endswith(".tmp")
        assert str(captured["dst"]) == plan.abs_path
        assert (repo_root / plan.rel_path).read_text(encoding="utf-8") == _VALID_TASK


# ------------------------------------------------------------- plan 防伪造


class TestPlanForgery:
    def test_non_plan_rejected(self) -> None:
        with pytest.raises(TaskWriterError, match="invalid_args"):
            apply_task_write({"rel_path": "x"}, confirmed=True)  # type: ignore[arg-type]

    def test_tampered_field_rejected(self, repo_root: Path) -> None:
        plan = plan_task_write(_SLUG, _VALID_TASK, kind=KIND_TASK_ACTIVE, repo_root=repo_root)
        tampered = dataclasses.replace(plan, content=plan.content + "\n注入")
        with pytest.raises(TaskWriterError, match="plan_tampered"):
            apply_task_write(tampered, confirmed=True)
        assert not (repo_root / plan.rel_path).exists()

    def test_hand_built_plan_rejected(self, repo_root: Path) -> None:
        forged = WritePlan(
            kind=KIND_TASK_ACTIVE,
            slug=_SLUG,
            repo_root=str(repo_root),
            rel_path="docs/tasks/active/task_my-task.md",
            abs_path=str(repo_root / "docs/tasks/active/task_my-task.md"),
            content=_VALID_TASK,
            overwrite=False,
            existed=False,
            diff="",
            checksum="0" * 64,  # 手工构造 · 摘要必不符
        )
        with pytest.raises(TaskWriterError, match="plan_tampered"):
            apply_task_write(forged, confirmed=True)


# ----------------------------------------------------- 不进 registry/manifest


class TestNotGatewayCapability:
    def test_ast_no_gateway_import_or_register(self) -> None:
        """AST 断言：task_writer 不 import gateway/registry/manifest · 不调 register。"""
        import app.ops.capability.task_writer as tw

        tree = ast.parse(Path(tw.__file__).read_text(encoding="utf-8"))
        forbidden_modules = {
            "app.ops.capability.gateway",
            "app.ops.capability.registry",
            "app.ops.capability.manifest",
        }
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                assert node.module not in forbidden_modules, node.module
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_modules, alias.name
            elif isinstance(node, ast.Call):
                func = node.func
                name = (
                    func.attr
                    if isinstance(func, ast.Attribute)
                    else (func.id if isinstance(func, ast.Name) else "")
                )
                assert name not in {"register", "unregister"}, name

    def test_grep_registry_surface(self) -> None:
        """grep 断言：registry/defaults/manifest/builtin.yaml 零 task_writer 引用。"""
        import app.ops.capability as cap_pkg

        pkg = Path(cap_pkg.__file__).parent
        for rel in (
            "registry.py",
            "defaults.py",
            "manifest.py",
            "gateway.py",
            "manifests/builtin.v1.yaml",
        ):
            assert "task_writer" not in (pkg / rel).read_text(encoding="utf-8"), rel

    def test_live_registry_has_no_task_writer(self) -> None:
        from app.ops.capability import get_registry

        ids = [spec.capability_id for spec in get_registry().list_specs()]
        assert not any("task_writer" in cid for cid in ids)
