# Invoke：ruff-baseline-cleanup · 20 task audit R1（2026-10-18）

> **帽位**：20-task-audit（R1 书面审查 · 受 00 委派 · 维护者授权口径「按授权取舍」已含本次）
> **产出**：`docs/harness/reviews/task_ruff_baseline_cleanup_audit_R1_20261018.md`（签收 · 零阻塞 · nit×1）
> **纪律**：零 git 操作 · 零码改 · 三闸未代签（HG-TASK-DRAFT/HG-AUDIT-R1 pending · HG-GRAPH-MODULES n/a 照登）

## 一 · 结论

**签收（无需退回）**。内容面零阻塞；流程闸 pending 如实写明，签闸权属维护者。nit N1：F4/FP-7「uv.lock 同源」与既有 CI 安装面（pytest.yml:44 `uv pip install "ruff>=0.5,<1"` 非 lock 钉版）措辞张力，建议 10-task 顺手钉死 `ruff==0.15.21` 或维护者签闸明裁——不阻签收（FP-7 有修正兜底）。

## 二 · 20 独立亲核实录（非转述 10 自报）

| 项 | 命令 / 动作 | 结果 |
|----|-------------|------|
| ruff 版本 | `uv run --extra dev ruff --version` + 亲读 `uv.lock:1831-1835` / `pyproject.toml:47,64-73` | 0.15.21 · 行号全命中 ✅ |
| check 总量/分布 | `ruff check app tests` + `--statistics` | 52 errors · 28 fixable · 8 hidden · 13 类分布逐项一致（28 可修 + 24 人工加总闭合）✅ |
| F811 九对 | `--select F811 --output-format concise` | redlines 572→777/617→822/640→845/703→908/743→948 · manifest 468→523/476→531/554→597/581→624，对名全对 ✅ |
| E402/C408/C401/N814/N818 | 分 select 实跑 | 坐标全数命中（http_generic.py:65-66 · token_stream:32,33,39 · C408 七处 · nodes.py:1922 · observability:214 · circuit.py:76）✅ |
| E402 互证 / N818 上下文 | 亲读 http_generic.py:55-72 · circuit.py:68-81 | :63-64 注释 + :66 `# noqa: F401` 互证成立 · CircuitOpen 为 app 公开异常 ✅ |
| format 漂移 | `ruff format --check`（全量/app/tests 三遍） | 223/103 · app 115/74 · tests 108/29 ✅ |
| CI 实况 | 亲读 pytest.yml 全文 + ls workflows + grep ruff | :52-53 Ruff 段注释 ✅ · 六件 workflow 仅 pytest.yml 含 ruff ✅ · 副产发现：pytest.yml:44 安装面为 `uv pip install "ruff>=0.5,<1"`（→ nit N1） |
| pytest 基线 | `.venv/bin/python -m pytest tests -q --tb=no` 独立复跑 | **19 failed, 1828 passed, 1 skipped（66.33s）** · FAILED 清单与 10 invoke §四 对拍一致 ✅ |

## 三 · 门禁实录（20 亲跑）

- `npx spec-wave verify --target . --task docs/tasks/active/task_ruff_baseline_cleanup.md` → **EXIT=2** · 尾行 `VERIFY: BLOCKED · HG-AUDIT-R1 pending · task_ruff_baseline_cleanup.md`（三闸 pending/n-a 期预期 fail-closed；闸表扫描 HG-TASK-DRAFT pending blocks 20,30 · HG-AUDIT-R1 pending blocks 30 · HG-GRAPH-MODULES n/a）
- `npx spec-wave task lint --file docs/tasks/active/task_ruff_baseline_cleanup.md` → **EXIT=0 · LINT: PASS**

## 四 · 交接

- 维护者：读审查文 → 签 HG-TASK-DRAFT / HG-AUDIT-R1（签注可确认 F3/F4 默认形态 · 可参考 nit N1）→ 再下发 30。
- 10-task（顺手修可选）：nit N1 措辞钉死 CI ruff 安装为 `ruff==0.15.21`。
- 30（签闸后）：以 task 表 + 审查文 nit 清单为准；F811 九对亲读两版再裁定，禁信转述。
