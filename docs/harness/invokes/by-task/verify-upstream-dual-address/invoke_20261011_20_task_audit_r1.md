# invoke：20-task-audit R1 审查 verify-upstream-dual-address（2026-10-11）

> **hat**：20-task-audit · **task_slug**：`verify_upstream_dual_address` · **轮次**：R1
> **worktree**：`../ops-desk-api-worktrees/t-verify-upstream-dual-address` · **分支**：`task/verify-upstream-dual-address`
> **性质**：书面审查 · 零 task 实质改动 · 不代签 human_gate
> **审查文**：`docs/harness/reviews/task_verify-upstream-dual-address_audit_R1_20261011.md`（址A 硬步骤 · 命名机读口径合规 · 结论节模拟机读 PASS）

## 1. 任务来源

- 00 派单：20-task-audit R1 书面审查 `docs/tasks/active/task_verify-upstream-dual-address.md`（10 落稿 commit d2e19cb）。
- 对照真值：CONVENTION 双址规约 v1 · 交接档 PROMPT_00 §2.2-3/§4-3/§4-4 · 上游 Cyning12/SpecWave @ `fad4694` 源码亲读。

## 2. 实证清单

| 对象 | 结果 |
|------|------|
| 上游源码 `src/checks/review-gates.ts` @ `fad4694` | 亲读复核：:96 双址写死（址B 不在内）· :99 命名 RE · :117-119 findReview 同源 · :46 spec 面同构。当前 checkout HEAD `fe454f0` 与 `fad4694` 对该文件零 diff，锚点精确成立 |
| 址B 命名不同构 | 抽样 `docs/audits/task-review/` 9/9 档全为 `YYYYMMDD_<slug>_r<n>.md` · 不同构属实 |
| 钉版三处 | `scripts/graph-compile.sh:28` · `package.json:6` · `.github/workflows/lint-wiki-delta.yml:35` 均 spec-wave@3.0.1 · 逐处核真 |
| 镜像行（task:55） | 主仓 `node_modules/spec-wave`（v3.0.1）`lib/checks/review-gates.js:89-114` 函数体在 · 路径写法 `spec-wave@3.0.1` 与 npm 布局不符 → N1 |
| task lint 机检 | `npx --yes spec-wave@3.0.1 task lint --file ...` EXIT=0 PASS（闸表 4 列 · status 纯 pending · 节名/必填齐） |
| graph_change_layer=none 先例 | done/ 70 处先例 · 按实判成立 |
| 结论节机读口径 | 以 review-gates.ts:143-162 常量本地模拟：chunks=1 · NEG 无命中 · PASS 命中 · substance 514≥20 · SUBJ/OBJ∨GATE 齐 → 可机读 |

## 3. 结论

**PASS-WITH-NITS · 零内容阻塞** · NIT 三条（N1 镜像路径写法 · N2 lint-wiki-delta 验收命令未钉版 vs CI 钉 3.0.1 · N3 worktree 无 node_modules 镜像弱化旁证）。
三闸（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES）均 pending → 审查文附维护者签闸清单 · 未附 30 Prompt（守 20-task-audit 纪律）。

## 4. 纪律自查

- 未改 task 实质内容 · 未代签 human_gate · 审查文落址A（未双落址B · 过渡期口径允许单落址A）
- 未切换/新建分支（全程 task/verify-upstream-dual-address）
