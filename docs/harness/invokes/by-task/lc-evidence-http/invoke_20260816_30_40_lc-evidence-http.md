# Invoke：30（含 40）· lc-evidence-http

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `lc-evidence-http` |
| freeze_id | `lc-evidence-http-v1` |
| task_paths | `docs/tasks/active/task_lc_evidence_http.md` |
| git_branch | `task/lc-evidence-http` |
| created_utc_or_local | 2026-08-16 |

## GATE_VERIFY（开工时）

| human_gate_id | task表status | 一致？ | 30可开工？ |
|---|---|---|---|
| HG-TASK-DRAFT | approved | Y | 是 |
| HG-AUDIT-R1 | approved | Y | 是 |
| HG-GRAPH-MODULES | approved | Y | 是 |

`harness verify --task …/task_lc_evidence_http.md` → **PASS**

## 实现摘要

1. `app/ops/lc_evidence_chain/router.py`：专用 `EvidenceOut.snippet` + `{ok,data}` / 500 envelope
2. `app/ops/router.py` include
3. `tests/test_lc_evidence_http.py` mock 链：401 / 422 / 200+snippet / refuse=200 / 500
4. G-L1 `01_modules.md` 备注 HTTP

## 验证

| 命令 | 结果 |
|---|---|
| `uv run ruff check app/ops/lc_evidence_chain/router.py app/ops/router.py tests/test_lc_evidence_http.py` | PASS |
| `uv run pytest tests/test_lc_evidence_http.py -q` | **7 passed** |
| `./scripts/graph-compile.sh` | exit 0 |
| `git diff origin/master -- app/ops/chat/graph.py` | 空 |
| 本机 OpenAPI + POST 无 cookie | 路径存在 · 401 |

## 下一棒

50 → CLOSE → PR
