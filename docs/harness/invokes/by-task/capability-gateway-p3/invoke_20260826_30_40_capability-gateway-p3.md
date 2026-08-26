# Invoke：30（含 40）· capability-gateway-p3

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40） |
| task_slug | `capability-gateway-p3` |
| freeze_id | 无 |
| task_paths | `docs/tasks/active/task_capability_gateway_p3.md` |
| related_review_or_none | `docs/harness/reviews/task_capability_gateway_p3_audit_R1_20260826.md` |
| git_branch | `task/capability-gateway` |
| worktree_root | `.`（主仓 `ops-desk-api`） |
| created_utc_or_local | 2026-08-26 |
| notes | 仅 P3；**未** commit / **未** push / **未** PR；交 00 验收 |

---

## 人工闸扫描（GATE_VERIFY · 首输出）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---------------|--------------|-----------------|--------|-----------|------------|
| HG-TASK-DRAFT | approved | approved（PROMPT） | Y | N（22-R1） | Y |
| HG-AUDIT-R1 | approved | approved（PROMPT） | Y | Y | Y |
| HG-GRAPH-MODULES | approved | approved（PROMPT · 不增一级） | Y | Y | Y |

reviews：`task_capability_gateway_p3_audit_R1_20260826.md` 存在且 R1 通过？ **是**

pre-30 invoke：`required ∩ {10,20,00}` 齐全？ **是**（有 00 + 10；`required_invoke_hats=10,30` · `default`）

`npx dsh-coding-kit verify --target . --task docs/tasks/active/task_capability_gateway_p3.md` → **VERIFY: PASS**

结论：**可进入读码/改码**

---

## 可复制 Prompt 快照

见同目录 `PROMPT_30_execute.md`（本轮按该复制区执行）。

---

## 交付范围（30）

1. `kind=skill` 预留：`SkillStubAdapter.provide()` 注入 stub 上下文 vs `invoke()` → `NotImplementedError`（非完整引擎）
2. Gateway 表面新增 `provide()`；与 `invoke` 分派共用 `_dispatch`
3. `register_skill_stub(*, enabled=False)`：默认**不**进 defaults；`skill_ref` 仅元数据指向 `docs/skills/s-l0-project-map`
4. 边界文档：`docs/guides/GUIDE_capability-gateway-p3-skill-boundary_v0.md`
5. SPEC §3.2 补 `provide`；§8 修订记录追加 **P0–P3 落地状态**
6. 最小 stub 单测；**未**改 `chat/graph.py`；无 Agently；无真外网；**未**实现完整 Skill 引擎

---

## 验证摘要（30/40）

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS（三闸 approved） |
| harness verify | `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_capability_gateway_p3.md` → **PASS** |
| ruff（触及路径） | `ruff check app/ops/capability tests/test_capability_gateway.py` → exit **0** |
| pytest | `.venv/bin/pytest tests/test_capability_gateway.py tests/test_lg_rag_multi.py -q` → exit **0** · **28 passed**（capability 19 + multi 9） |
| `git diff` · `app/ops/chat/graph.py` | **0**（零改动） |
| Agently / 真外网 / 完整 Skill 引擎 | **未**引入 / **未**连 / **未**实现 |
| commit / push / PR | **未执行** |

**变更路径（本 task）**

- `app/ops/capability/adapters/skill.py`（新建）
- `app/ops/capability/skill_stub.py`（新建 · 注册辅助）
- `app/ops/capability/gateway.py`（`provide` + `_dispatch`）
- `app/ops/capability/adapters/__init__.py` / `__init__.py`（导出）
- `tests/test_capability_gateway.py`（P3 单测 ×4）
- `docs/guides/GUIDE_capability-gateway-p3-skill-boundary_v0.md`
- `docs/guides/GUIDE_capability-gateway-p2-probes_v0.md`（非范围行交叉指针）
- `docs/spec/agent-infra/SPEC-capability-gateway_v0.md`（§3.2 + §8）
- 本 invoke

**默认关闭钉死**：defaults 仅 `local_fn`；skill stub 须显式 `register_skill_stub`。

---

## 交 00

- 验收标准可勾选（边界文档 · stub 单测 · SPEC 落地状态 · pytest/ruff · graph.py 0）。
- **可否关账**：是（40 绿 · 无完整引擎 · 未 commit/push）。
