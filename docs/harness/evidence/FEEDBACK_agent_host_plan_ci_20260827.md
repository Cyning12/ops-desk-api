# FEEDBACK · agent-host-plan CI 踩坑 · from ops-desk-api

> **日期**：2026-08-27  
> **业务仓**：`ops-desk-api`（FastAPI · `dsh-coding-kit@1.8.0`（K1–K7 已核对）· CI `lint-wiki-delta` + `pytest tests`）  
> **场景**：Agent Host 规划轨 H1–H5 连续 PR（#70–#74）+ 收官文档 #75  
> **统筹**：00 单窗签收 SPEC → 拆 task → 派 30 → 阶段 PR + auto merge  
> **真值对照**：`docs/harness/prompts/30-execute-code.md` · `40-self-check.md` · `ci/samples/lint-wiki-delta.yml.example` · `.github/workflows/{pytest,lint-wiki-delta}.yml`  
> **关联规划**：`docs/spec/agent-infra/02_agent_host_plan_v0.md`（H1–H5 全轨 CLOSE）

---

## 1. 结论（归因摘要）

| 失败类型 | 出现 PR | 主因归属 | kit 是否应改 |
|---|---|---|---|
| pytest · 行为变更未回归全仓 | #70 · #71 | **本仓执行 + task 验收项** | 次要（verify/40 与 CI 对齐） |
| lint-wiki-delta · 兄弟 active task 缺字段 | #70 | **00 批量拆 task 未早检** | **是**（10-task / 00 playbook） |
| lint-wiki-delta · done task 节名错误仍报 missing | #72（fix commit 仍红） | **kit 误报 + 手归档 bypass close** | **是**（lint 诊断 + close 输出） |
| lint 仍红即 merge | #72 | **统筹执行**（非 kit 设计） | 否（文档纪律即可） |
| 一次绿 | #73 · #74 · #75 | 执行改善 | — |

**判定**：pytest 类失败 **不是 kit 规则错误**，是域内语义变更 + PR 前未跑 CI 同款全量。  
**wiki_delta 类失败** 暴露 kit **起草→verify→close→CI 链路缝隙**（早检不足、误报、手写出 done），值得产品侧迭代。

---

## 2. CI 失败实录（按 PR）

### PR #70 · H1 · supervisor Capability 目录

| job | commit | 现象 | 根因 |
|---|---|---|---|
| **pytest** | `e499679` | `test_lg_rag_multi.py::test_unknown_tool_recorded_and_continues` · `assert len(results) == 2` → 1 | H1 新语义：plan 含非法 tool id → **整 plan fallback 单 rag**；旧测假设 invoke 层逐条报错继续 |
| **lint-wiki-delta** | `e499679` | missing ×4 | 同分支上 H2–H5 **active task** 缺 `wiki_delta`（00 SPEC 签收批量拆 task 时未预填） |

**修复 commit** `a8e52c8`：对齐 `test_lg_rag_multi`；4 个 active task 补 `| **wiki_delta** | n/a |`。

### PR #71 · H2 · Policy 门

| job | commit | 现象 | 根因 |
|---|---|---|---|
| **pytest** | `5d7c061` | `test_capability_gateway.py::test_p2_probes_register_and_invoke_mock` · `sandbox.ok is False` · `policy_blocked: sandbox_disabled` | H2 invoke 前 Policy 门；sandbox/cli 默认 env 关；旧测未传 `ctx._host_policy` |

**修复 commit** `4cb9e14`：探针 invoke 显式 `allow_sandbox` / `allow_cli`。

### PR #72 · H3 · Session 连续性

| job | commit | 现象 | 根因 |
|---|---|---|---|
| **lint-wiki-delta** | `1adac32` | `task_chat_session_continuity.md` · wiki_delta_missing | 手写出 `docs/tasks/done/`，**未走** `task close --yes`；done task 无字段 |
| **lint-wiki-delta** | `dfc3abf` | 同上（fix 后仍红） | 写了 `## Harness` + `wiki_delta` 行，但 lint 只认 **`## Harness 元信息`** → **误报为 missing** |

**备注**：#72 merge 时 lint 仍红；master 后续才改为正确节名。H4/H5 因格式对齐 + 走规范归档，**首次 CI 即绿**。

### PR #73 · #74 · #75

无失败记录（H4/H5 实现 commit 即绿；#75 纯文档补全）。

---

## 3. 产品改进建议（dsh-coding-kit / harness）

| ID | 现象 | severity | 建议 | **1.8.0 状态** |
|---|---|---|---|---|
| **K1** | `lint-wiki-delta`：字段存在于 `## Harness` 等非标准节名下，仍报 `wiki_delta_missing` | **P1** | 新增 issue code `wiki_delta_wrong_section`；summary 写「须在 `## Harness 元信息` 表格内」 | **已修 · 1.8.0** |
| **K2** | `task lint --file`（10-task）起草时不拦 `wiki_delta` 缺失；直到 CI `scope: all` 才 red | **P1** | `task lint` 增 E8：缺 `wiki_delta` 行 → FAIL（与 close 对齐） | **已修 · 1.8.0** |
| **K3** | `verify --task` 不跑 `lint-wiki-delta`；30 GATE_VERIFY 与 PR CI 双轨 | **P2** | `verify --with-wiki-lint`（opt-in；preset 默认未开） | **已修 · 1.8.0（旗标）** |
| **K4** | 00 一次拆 N 个 active task 后，第一棒 PR 被「兄弟 task」连带打红 | **P2** | 00 playbook bulk-split 后必跑 lint-wiki-delta；10-task 预填义务 | **已修 · 1.8.0（条文）** |
| **K5** | Agent 手写出 done task 绕过 `task close` 机械校验 | **P2** | `task close` 打印 `done_snapshot`（`## Harness 元信息`） | **已修 · 1.8.0** |
| **K6** | `40-self-check` 与 CI 全量命令不对齐 | **P2** | TASK_TEMPLATE / 40 默认全量 CI + lint-wiki-delta | **已修 · 1.8.0（条文）** |
| **K7** | 行为变更类 task 无「旧测 grep」提醒 | **P3** | 20-task-audit checklist（非机械闸） | **已修 · 1.8.0（checklist）** |

> **核对真值**：[`FEEDBACK_dsh_coding_kit_1_8_0_from_ops_desk_api_20260827.md`](./FEEDBACK_dsh_coding_kit_1_8_0_from_ops_desk_api_20260827.md)（2026-08-27）。

---

## 4. 本仓已采纳 / 待采纳（非产品阻塞）

| # | 动作 | 状态 | 说明 |
|---|---|---|---|
| L1 | 40 / invoke PR 前硬命令：`pytest tests -q` + `npx dsh-coding-kit@1.8.0 task lint-wiki-delta --target .` | **待**（命令已钉 1.8.0） | 写入 `PROMPT_00` 或仓内 `cyning-harness-local` |
| L2 | 归档 **禁止手写 done**；只走 `task close --file … --yes` | **待** | 00/CLOSE invoke 纪律 |
| L3 | SPEC 签收拆多 task 时批量预填 `## Harness 元信息` + `wiki_delta` | **待** | 避免 #70 类连带 red |
| L4 | 行为变更 PR 验收加「全仓 pytest + 关联旧测 grep」 | **待** | 避免 #70/#71 类 |

---

## 5. lint-wiki-delta 失败日志摘录（CI 真值）

**#70 · missing ×4**（`run 33037002560`）：

```text
缺 wiki_delta 字段的 task:
  - docs/tasks/active/task_capability_policy_sandbox.md
  - docs/tasks/active/task_chat_session_continuity.md
  - docs/tasks/active/task_prompt_assembly_p1.md
  - docs/tasks/active/task_skill_registry_p0.md
LINT-WIKI-DELTA: FAIL · issues 4
```

**#72 · 节名错误仍报 missing**（`run 33037752469` · commit `dfc3abf` 文件内已有 `## Harness` + wiki_delta 行）：

```text
  - docs/tasks/done/task_chat_session_continuity.md · wiki_delta_missing
LINT-WIKI-DELTA: FAIL · issues 1
```

**#72 修复后正确格式（本仓 done 真值）**：

```markdown
## Harness 元信息

| **wiki_delta** | `n/a` |
```

---

## 6. pytest 失败日志摘录

**#70** · `test_unknown_tool_recorded_and_continues`：

```text
WARNING lg_rag supervisor plan 含非法 tool id，fallback 单 rag
assert len(results) == 2  →  1
```

**#71** · `test_p2_probes_register_and_invoke_mock`：

```text
AssertionError: assert False is True
error='policy_blocked: sandbox_disabled'
```

---

## 7. severity 汇总

| ID | 主题 | severity | 阻塞关账？ | 建议归属 |
|---|---|---|---|---|
| K1 | lint 误报 wrong section | **P1** | 是（误导 fix） | `task lint-wiki-delta` |
| K2 | 10-task 起草不拦 wiki_delta | **P1** | 否（CI 会拦） | `task lint` + TASK_TEMPLATE |
| K3 | verify 不含 wiki lint | **P2** | 否 | `verify` CLI |
| K4 | bulk-split 00 playbook | **P2** | 否 | prompts / 00-orchestrator |
| K5 | close 成功无模板快照 | **P2** | 否 | `task close` UX |
| K6 | 40 与 CI pytest 范围不一致 | **P2** | 否 | prompts + task 模板 |
| K7 | 行为变更旧测提醒 | **P3** | 否 | 20-task-audit |
| — | pytest 回归（H1/H2） | — | 否 | **本仓执行** + L4 |
| — | #72 merge 时 lint 红 | — | 否 | **本仓统筹纪律** |

---

## 8. 环境与命令实录

| 项 | 值 |
|---|---|
| kit 版本（CI） | `npx --yes dsh-coding-kit@1.8.0` |
| CI workflows | `.github/workflows/pytest.yml` · `.github/workflows/lint-wiki-delta.yml` |
| PR 序列 | #70 H1 · #71 H2 · #72 H3 · #73 H4 · #74 H5 · #75 收官文档 |
| 最终 master | H1–H5 CLOSE · `02_agent_host_plan_v0.md` → completed |

**PR 前推荐命令块（本 FEEDBACK 建议固化）**：

```bash
ruff check app tests   # 触及路径
.venv/bin/pytest tests -q --tb=short
npx --yes dsh-coding-kit@1.6.1 task lint-wiki-delta --target .
# 关账（禁止手写 done）：
npx --yes dsh-coding-kit@1.6.1 task close --file docs/tasks/active/task_<slug>.md --yes
```

---

## 9. 可选 BACKFILL 指针

- §3 **K1–K7** 已于 **1.8.0** 落地；产品侧可关账本 FEEDBACK。  
- 本仓侧 §4 **L1–L4** 可在下一波 00 统筹或 harness upgrade task 中合入（**非** agent-host 轨阻塞项）。

---

## 10. 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-27 | 初稿：agent-host-plan H1–H5 CI 失败复盘 + kit/本仓分层建议 |
| 2026-08-27 | §3 K1–K7 对照 `dsh-coding-kit@1.8.0`：**全部已修**（见同目录 1.8.0 FEEDBACK） |
| 2026-08-27 | Hub 关账：`task_dsh_coding_kit_upgrade_1_8_0` · 命令示例钉 @1.8.0 |
