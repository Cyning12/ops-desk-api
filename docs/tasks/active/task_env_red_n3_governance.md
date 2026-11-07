# Task：env 红基线治理 + 波次审计闸自注册（N3）+ fail-closed 立档（api#337 CLOSE 遗留三挂账）

> **状态**：`active`（2026-11-07 · lead 直接执行 · 维护者当面授权「B 全做」）
> **类型**：fix / 测试基建 + 审计基建（docs+tests 面 · 零 src 改动）
> **上游**：api#337 CLOSE invoke `invoke_20261106_50_close.md` §遗留挂账 1–3（非本链责任·如实移交 → 维护者 2026-11-07 09:15 指令「B 全做」销项）
> **分支**：`agent/env-red-n3-governance`（单棒治理 · 末段=工单名）
> **00 注**：本档即治理裁定档——三挂账逐项处置：①2 枚 env 红另案修（根因=测试自身环境依赖漂移 · 非产品缺陷）②N3 自注册机制立册（registry.yaml + 通用闸 + 程序 README）③fail-closed 语义正式立档（ADR-001·维持不修正）。

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `env-red-n3-governance` |
| **git_branch** | `agent/env-red-n3-governance` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 红测先行双证据：两枚 env 红修复前 `2 failed`（09:17 实测留痕）→ 修复后 `2 passed`（09:21/09:22 实测）；N3 闸三变异探针（banned 在途探针→fail · active committed 面真跑 pass · 缩白名单探针→fail 列出越界件） |
| **code_quality_bar** | `L2_backend`（涉码面=三枚测试文件 + 新增闸测试 · src 零改动红线） |
| **graph_change_layer** | `none`（测试基建 + docs/harness 审计面 · 无路由/表/事件类型/一级模块面） |
| **graph_delta** | `none` |
| **wiki_delta** | `n/a` |
| **review_hat** | `20`（本棒由 lead 自审自验 · 维护者当面授权单棒闭环） |
| **required_invoke_hats** | `30` |
| **kpi_aggregator** | `CLOSE`（治理单棒 · 合并即关账） |
| **orchestration** | 治理单棒：勘察定根因 → 修两红 → 立 N3 三件套 → ADR-001 → 全量回基线 → PR 自验合并 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | 维护者 2026-11-07 09:15 当面指令「B 全做」（挂账原文 = CLOSE invoke §遗留挂账 1–3）· lead 代签 |
| HG-GRAPH-MODULES | approved | 30 | graph_change_layer=none 口径 · 零业务模块改动 · lead 代签 |

---

## 范围

**做**：
1. `tests/test_memory_vector_p1.py::test_embedder_failure_degrades_with_marker`——播种改走 FakeEmbedder（照 ⑦ 变异检验装配口径 `monkeypatch.setattr get_query_embedder`），摘除对 `SILICONFLOW_API_KEY` 真实环境的隐式依赖；
2. `tests/test_multi_replica_dualproc.py::test_hitl_cross_instance_resume` + `tests/dualproc_server.py`——①替身 aggregator 增 `hitl_unlocked_ids`（resume._summarize 可见键·原五键与 summarizer 提取表零重叠的漂移修复）②断言改双契约（同步内联老契约 / hitl-resume-async accepted 新契约·W-fix 2026-11-02）+ replay 轮询等恢复段 done 终帧；
3. N3 三件套：`docs/harness/audit_gates/registry.yaml`（种子=diff-whitelist 闭窗档案）+ `tests/test_wave_gate_registry.py`（通用闸·banned 在途前置 + active committed 闭窗 + 种子回归牙）+ `README.md` 自注册程序；
4. `docs/harness/audit_gates/adr-001-fail-closed-stranded-wave.md`——挂账第 3 项正式立档（accepted·维持不修正·revisit 条件入档）。

**不做（红线）**：
- 零 `src/` 改动（两红根因均在测试自身 · 产品行为零变化）；
- 不放宽 `_touched_in_wave` 保牙语义（ADR-001 裁定）；
- 不动既有 bespoke 闸（TC8 等 = 历史档案见证·保留）。

## 验收标准

- [ ] 两枚 env 红修复后命令级 `2 passed`（修复前 `2 failed` 证据见 invoke）；
- [ ] N3 闸三变异探针全咬（banned 在途 / active 真跑 / 缩白名单）；
- [ ] 全量测试回基线形态：原 2 枚 env 红消失 · 零新增红；
- [ ] ruff + task lint + wiki-delta 三质量门零新增；
- [ ] ADR-001 立档在册。

### 自检结论（执行者）

> **hat 30（治理单棒·实现即验收）** · 三挂账逐项落地 · src 零改动红线零命中。

| 命令 | 退出码 | 摘要 |
|------|--------|------|
| `.venv/bin/python -m pytest tests/test_memory_vector_p1.py::test_embedder_failure_degrades_with_marker tests/test_multi_replica_dualproc.py::test_hitl_cross_instance_resume`（修复前取证） | 1（2 failed） | 基线红证据：embedder 用例播种子缺 SILICONFLOW_API_KEY 裸奔 RuntimeError / hitl 用例 resume 内联 state 恒空 |
| 同上（修复后） | 0（2 passed） | 红转绿双证据（embedder 走 FakeEmbedder 装配 · hitl 双契约 + replay 轮询等 done 终帧） |
| `.venv/bin/python -m pytest tests/test_wave_gate_registry.py` | 0（2 passed） | N3 通用闸常态绿 |
| N3 三变异探针（banned 在途 / active 面真跑 / 缩白名单） | 预期 fail ×2 + pass ×1 | 闸语义实证（探针留痕见 invoke） |
| `ruff check app tests` | 0 | 零新增 |
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_env_red_n3_governance.md` | 0 | LINT: PASS |
| `npx --yes spec-wave@3.5.0 task lint-wiki-delta --target .` | 0 | LINT-WIKI-DELTA: PASS |
| 全量 pytest（回基线形态） | 0 | 原 2 枚 env 红消失 · 零新增红（见 invoke 全量摘要） |

## 失败路径

- 两枚 env 红修复后仍红 → 回滚对应测试改动（根因判定错）· 但 N3/ADR 件不受影响可独立合；
- N3 通用闸在干净树 fail → 闸自身缺陷（banned 定义/面求值错）· 禁靠放宽 allowed 消红；
- 全量出现新增红 → 本棒拒绝合并 · 先销红再谈合并。

## 修订记录

| 日期 | 棒 | 内容 |
|------|----|------|
| 2026-11-07 | 30 | 治理单棒全量落地（两红修复 + N3 三件套 + ADR-001 + 档/invoke） |

