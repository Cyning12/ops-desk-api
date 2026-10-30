# invoke · 40 · 独立验收 · api-prompts-sync-3-5-0

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-30 |
| **帽** | 40（独立验收 · 不信 30 自报 · 逐项亲跑） |
| **task** | `docs/tasks/active/task_api_prompts_sync_3_5_0.md`（v0.5） |
| **对象** | 30 交付：实现 commit c6bb1c3 + docs commit ec1f774（HEAD）· 基线 2b6d2c0 |
| **retention** | minimal（承 task `invoke_retention_profile`） |
| **纪律** | 单 worktree 串行 · 只验收不改实现 · 本地 commit 仅验收留痕 · push/PR 禁 · 维护者脏文件 `docs/arch-browser/dist/site-data.json` 全程未动 |

## 逐项实证（亲跑）

### ① diff 面与量（git diff 2b6d2c0..HEAD 全量亲读）

- 合计 11 文件 +140/-4：c6bb1c3 = 9 文件 **+50/-2**（docs/harness/prompts/ 8 枚 + docs/harness/templates/TASK_TEMPLATE.md 1 枚 · 均在 sync 白名单面内）· ec1f774 = task 文 + 30 invoke（docs 留痕）
- **零 app/ · 零其他面**；非范围件（FRAGMENT_30_invoke_block / DAG / README / AGENTS / CLAUDE）零触碰

### ② conflict 8 台账抽核（实抽全 8 枚 · 超 ≥3 要求）

- 对拍源：`node_modules/spec-wave/`（package.json version = **3.5.0**）assets/harness/{prompts,templates}
- **7 枚合并件与上游逐一 diff = 全部 ZERO-DIFF**（00-orchestrator / 10-task-requirements / 10-spec-requirements / 20-task-audit / 20-spec-audit / FRAGMENT_00_delegate_only / templates/TASK_TEMPLATE）
- **30-execute-code 亲读**：与包内恰 1 行差异——本地 `_tech_graph/` 读序项存续 + 上游条件条款并存于同一行（`读 task 必读列表 + AGENTS.md + _tech_graph/ + L2（涉码）；若仓 profile 声明 …`）· 残留 conflict 系有意保留，与台账一致

### ③ V1–V7 复跑

| 项 | 亲跑结果 |
|----|----------|
| dry-run 复跑 | `npx spec-wave@3.5.0 sync prompts --target .` → **skip 12 / add 0 / conflict 1（30-execute-code）· EXIT=0** · 与 30 复跑收敛证据逐字一致 |
| FRAGMENT sha256 | 包内与仓内两侧均 `3739570a6a40b2f41110a061e1dfdb0864bd596db3371c67569584da29f3f565`（与 V3 照登值一致） |
| V4 白名单外 | 全量 name-status 亲核：面 = 白名单 9 + task/invoke 2 · 白名单外零写入 |
| V5 graph-compile | `./scripts/graph-compile.sh` → **EXIT=0**（9 md check 全 OK · 禁管道截断取真码）· `git status docs/_tech_graph/` 零 diff |
| V6 task lint | `task lint --file …` → **LINT: PASS · EXIT=0** |
| V7 存量 verify 对照 | worktree 基线法：`git worktree add /tmp/ops-api-baseline-2b6d2c0 2b6d2c0` 跑 `verify --task task_lg_rag_gate_produces_unfulfilled.md` vs 当前 HEAD 同命令 → 输出**逐字一致**（双侧均 `VERIFY: BLOCKED · HG-AUDIT-R1 pending` · EXIT=2）· worktree 已清理 |
| 本 task verify | `verify --task docs/tasks/active/task_api_prompts_sync_3_5_0.md` → **VERIFY: PASS · EXIT=0**（INFO：图谱锚点检查未生效 · graph_path_unreachable · graph_modules_path=l1/01_modules · 与 S5 照登一致） |

### ④ 上游新增条款质量抽核

- FRAGMENT_graph_first_read_v1_zh.md 生效条件（profile `graph_modules_path` 非空且可达目录）与 00/10×2/20×2/30 各帽并入条款的「条件触发」措辞语义连贯；各帽义务与片段「各帽义务」节一一对应（00 派发前确认 / 10 必读+锚点 / 20 锚点核对退回 10 / 30 开工必读）
- 相对链接 `./FRAGMENT_graph_first_read_v1_zh.md` 目标存在（同目录 · 已物化）；FRAGMENT_00_delegate_only 内嵌「图谱先读」整节与片段 00 义务一致 · 零虚构图谱指引

### ⑤ 30 落账检查

- 30 invoke（minimal）在盘：闸扫描表（真值=task 闸表）+ 执行记录 8 条 + 物化≠接入结论 ✓
- 自检回填 S1–S5 / V1–V7 与本帽亲跑结果逐项吻合，无拔高措辞 ✓
- v0.5 修订记录与实际交付一致 ✓
- 遗留四条照登合理性：(1) 残留 conflict 1（30-execute-code `_tech_graph/`）——实证为有意保留 ✓；(2) 物化≠接入（生效前提 = profile 可达目录 · 属 task_api_graph_anchor_profile_fix 地盘）——本帽 verify 实测同一 INFO skipped ✓；(3) web e70a2b0 conflict 9 全保留 vs 本仓 8 全合并之差异根因（本仓零本地定制块）照登 ✓；(4) §7 跨分支引用悬空（两关联 task 在 sibling 分支 · 本分支 `ls docs/tasks/active/` 实证不存在）照登 ✓

## 结论

**PASS** —— S1–S5 / V1–V7 独立复跑全绿；conflict 8 处置台账全枚亲核属实；零 --force 由 30-execute-code 本地项存续 + 7 枚对齐上游零 diff 内容级佐证；diff 面零越界；维护者脏文件未动。建议维护者关账裁决。
