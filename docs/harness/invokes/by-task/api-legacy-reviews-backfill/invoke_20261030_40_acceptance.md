# 40 invoke · api-legacy-reviews-backfill 独立验收（2026-10-30）

> **帽**：40 独立验收 · **task**：docs/tasks/active/task_api_legacy_reviews_backfill.md（v0.5）
> **核验对象**：30 交付 1a9f54b + 5f00a03（基 c1ec310 · 分支 task/api-legacy-reviews-backfill · 双闸 approved 授权锚 m00500）
> **纪律**：独立亲验不背书 30 自报 · 单 worktree 仅此一棒 · 维护者脏文件 site-data.json 未触碰 · 零 push
> **结论**：**PASS（两枚 NIT 登记 · 见末节）**

## 逐项验收表（对照 v0.5 验收标准 · 全部亲验）

| # | 验收项 | 结论 | 实证 |
|---|--------|------|------|
| 1 | diff 亲读（面外零改动） | **PASS** | `git diff c1ec310..HEAD`：8 档 +283/−1 = reviews/+5（新档）+ AGENTS.md +2 + 30 invoke +29 + task +33/−1；`app/` `tests/` 零触碰；legacy-gate-exempt.yaml 与 docs/tasks/done/ 零 diff（空输出亲跑） |
| 2 | 5 份补审实证锚抽核 | **PASS（NIT-1 登记）** | 亲验 anchors 全中：nodes.py:2156 `observe_node(state, config: Optional[RunnableConfig] = None)  # noqa: UP045`；main.py:43 def / :73 调用 `_sanitize_no_proxy_env()`；types.py:122 `output_fields: tuple[str, ...] = ()`；builtin.v1.yaml 5 条 output_fields（:27/:47/:67/:90/:113）；query_rewrite.py:54-66 开关解析含非法值 warning 回退关；supervisor nodes.py:1260/:1269/:1426-1435 error{stage=supervisor_plan} 映射与 supervisor_plan_failed span；4 钉测档现存。commit 链亲跑 merge-base --is-ancestor：27fd930/1d26aa7/bfed4cd/4b36b3b/fc5d9bd/35b8f95/e364dd5/47e51f6/0c4a1ed/cb80f8f 均在 master。**NIT-1**：capability R2 核对材料括注「回填 8cd8584 · PR #294 squash bfed4cd · 均实证在 master」——8cd8584 实**不**在 master（squash 吸收 · 经本地分支 task/lg-rag-capability-output-schema 可达）；实质结论（B1 闭环）由 done task v1.1 内容与钉测档独立可验，不受影响。supervisor R2 之 40ab986 列于括注链外、无此误述 |
| 3 | R2 三件机读契约 | **PASS** | 直引仓装 spec-wave 3.5.0 `lib/checks/review-gates.js` `evalReviewConclusion` 跑全 5 件：5/5 pass=true「结论/签收节结论可机读通过」；R2 三件均含 `## 前审沿革` 独立节且结论节 REVIEW_NEG_RE 零命中（否定沿革字面隔离在前审沿革节） |
| 4 | 仓级裸 verify | **PASS** | `npx spec-wave verify --target .`（node_modules 钉版 3.5.0 = package.json 钉位）→ EXIT=0 · 字面「VERIFY: PASS（裸 verify · 仓级 reviews 扫描）」；豁免命中留痕 96 行，grep 实证 5 枚 slug 零出现（缺口 5→0） |
| 5 | AGENTS.md 仓规两则 | **PASS** | 条款一落 :159 · 条款二落 :160（cyning-harness-local 块 :153/:161 内）；30 报 :159/:160 与实测一致；diff 仅块内 +2 行，begin/end 标记外零改 |
| 6 | lint / verify --task 复跑 | **PASS** | `task lint --file` → LINT: PASS EXIT=0；`verify --task` → VERIFY: PASS EXIT=0（闸表 HG-TASK-DRAFT/HG-AUDIT-R1 approved · 零 --allow 旗标）；R1 审查文 task_api_legacy_reviews_backfill_audit_R1_20261030.md 在库（c1ec310 入库）· 30 invoke 在库（本 diff 内） |
| 7 | 30 落账抽核（自报 vs 实测） | **PASS** | 自检结论 S1 表 5×PASS 与审查文一致；S2 条文逐字与 AGENTS.md :159-160 一致；S3 PASS 字面与我复跑逐字一致；V1–V7 矩阵逐项独立复核全绿 |

## 过程留痕

- 2026-10-30 40 单棒验收：master 切 task/api-legacy-reviews-backfill → diff 全读 → anchors/commit 链亲验 → review-gates.js 机读契约直引复判 → 裸 verify/lint/--task 三跑 → 落账 commit → 切回 master。
- verify --task 输出含 INFO 行「图谱锚点引用检查未生效（已跳过 · graph_path_unreachable · graph_modules_path=l1/01_modules）」——属 task_api_graph_anchor_profile_fix 范畴，照登不混入本 task 结论（task §7 关联口径）。

## NIT / 遗留

- **NIT-1**（不阻塞）：capability R2 核对材料括注 8cd8584「实证在 master」失实（squash 吸收 · 任务分支可达）。40 不改被审件以保持独立性；建议 20/10 帽后续校正措辞或维护者裁决留痕。
- **NIT-2**（40 顺手校正）：task 文首状态行陈旧（draft · HG-AUDIT-R1 pending · 拒开工）与闸表 approved 不一致——c1ec310 已存在（非 30 引入 · v0.4 闸代录未同步）；本帽随 v0.6 落账校正并在修订记录照登。
- 维护者脏文件 `docs/arch-browser/dist/site-data.json`（M）全程未触碰。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-30 | 40 独立验收落盘：七项全 PASS · NIT-1/NIT-2 登记 · 裸 verify EXIT=0 缺口 5→0 亲验 |
