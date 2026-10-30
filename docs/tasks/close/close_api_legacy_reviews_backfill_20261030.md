# CLOSE 档 · task_api_legacy_reviews_backfill（2026-10-30）

## 一句话

仓级 5 存量 reviews 缺口走补审不走豁免（维护者新原则首单执行）：2×R1 新审 + 3×R2 补轮逐件 PASS 零实质问题，仓规两则落 AGENTS.md 仓内定制块 :159-160，裸 verify 缺口 5→0「VERIFY: PASS（裸 verify · 仓级 reviews 扫描）」EXIT=0；40 独立验收七项逐项亲验全 PASS（commit e191ebd · NIT×2 照登不阻塞）归档；分支 `task/api-legacy-reviews-backfill`（七 commit）未 push，**PR 合码 + CI 绿 + 分支清理待维护者裁决**（close_pr_policy=required 偏差 · 维护者授权 m00085/m00500 全程本地 commit 可 push/PR 禁）。

## 需求锚

维护者新原则（2026-10-30 立 · task §1 背景在案）：「api 仓后续不使用豁免更符合长久发展」——晚于豁免基线（2026-10-11）的归档档走补审不走豁免；升级/流程类 task 一律走 20-R1 审查、禁用 `--allow-no-review`；legacy-gate-exempt 扩列须带截止条件/回填义务。缺口实证：`docs/spec/doc-health/feedback/2026-10-30_3.5.0_ops-desk-api_upgrade.md` §5（5 缺口存量既有非 3.5.0 引入 · master 3.3.0 复跑同集对照）。

## 交付（S1–S3）

- **S1 逐档补审**（docs/harness/reviews/ · 20-task-audit 帽 · 每档独立审查文独立结论）：
  - S1a 新 R1 `task_fix_hitl_observe_node_config_injection_audit_R1_20261030.md` → PASS（PR #296/27fd930 · 验收 4 条 + failure_paths 5 条全落实）
  - S1b 新 R1 `task_fix_no_proxy_bracket_ipv6_sanitize_audit_R1_20261030.md` → PASS（PR #295/1d26aa7 · 验收 4 条 + live 补验 + failure_paths 4 条全落实）
  - S1c 补轮 R2 `task_lg_rag_capability_output_schema_audit_R2_20261030.md` → PASS（R1-B1 经 8cd8584 回填闭环 · PR #294/bfed4cd · 前审沿革独立成节）
  - S1d 补轮 R2 `task_query_coref_rewrite_audit_R2_20261030.md` → PASS（R1 内容面 pass 维持 · PR #284/4b36b3b+fc5d9bd · TC1–TC12 实录 38 例先红后绿）
  - S1e 补轮 R2 `task_supervisor_first_fail_closed_audit_R2_20261030.md` → PASS（R1-B1 经 TC11 补列 40ab986 闭环 · PR #282/35b8f95 · 1851 passed/1 skipped）
- **S2 仓规两则落位** `AGENTS.md` `<!-- cyning-harness-local -->` 块 :159-160（begin/end 标记外零改）：条款一「升级/流程类 task 禁用 `--allow-no-review`，一律走 20-R1 审查文」；条款二「legacy-gate-exempt 扩列须带截止条件或回填义务（截止条件/回填义务写入 reason 字段）· 语义面人审非机断（R1 审查 O2）」。
- **S3 清零实证**：裸 `npx spec-wave verify --target .` → EXIT=0 ·「VERIFY: PASS（裸 verify · 仓级 reviews 扫描）」逐字照登 · reviews 缺口 5→0（豁免命中留痕行不含本 5 枚 slug）· `legacy-gate-exempt.yaml` 零 diff · 5 枚 done 档本体零 diff · 零业务码改动（app/ tests/ 零触碰）。

## 验收链

10 落稿 v0.1 → 00 代录 HG-TASK-DRAFT approved（`001a188` · 授权锚 m00500）→ 20 R1 审查通过零阻塞（`0ae43e9` · 观察 O1–O3 全采纳）→ 00 代录 HG-AUDIT-R1 approved + R1 审查文入库（`c1ec310`）→ 30 交付三件套（`1a9f54b` 五件补审落盘 + `5f00a03` 仓规两则 + 30 invoke + 自检回填 v0.5 · 裸 verify 5→0 · lint/verify --task 双绿零 --allow 旗标）→ **40 独立验收七项逐项亲验全 PASS**（`e191ebd` · v0.6 · NIT×2 登记不阻塞）→ 00 代签 CLOSE（本 commit）。

## 40 验收摘要（逐项亲验 · 不背书 30 自报）

| 验收项 | 结论 | 实证锚 |
|--------|------|--------|
| 1 diff 面 | ✅ | c1ec310..HEAD = 8 档 +283/−1（reviews/+5 · AGENTS.md +2 · invoke · 本 task）· app/ tests/ 零触碰 · exempt yaml/done 档零 diff |
| 2 补审实证锚抽核 | ✅ | 5 件代码锚全抽：nodes.py:2156 · main.py:43/:73 · types.py:122 · builtin.v1.yaml 5 条 output_fields · query_rewrite.py:54-66 · supervisor nodes.py:1260/:1269/:1426-1435 · 10 枚 commit 链 merge-base 实证在 master |
| 3 R2 机读契约 | ✅ | 直引仓装 review-gates.js evalReviewConclusion 跑 5/5 pass=true · R2 三件前审沿革独立成节 · REVIEW_NEG_RE 零命中 |
| 4 裸 verify | ✅ | EXIT=0 · 缺口 5→0 · 豁免留痕 96 行 · 5 枚 slug grep 零出现 |
| 5 仓规两则落位 | ✅ | AGENTS.md :159 条款一 · :160 条款二 · 标记外零改 |
| 6 lint / verify --task | ✅ | 双 PASS EXIT=0 零 --allow 旗标 · R1 审查文 + 30 invoke 在库 |
| 7 30 落账抽核 | ✅ | S1/S2/S3/V1–V7 自报逐项与实测一致 |

**40 总裁定：PASS（NIT×2 登记）**。

## 遗留移交

1. **NIT-1**（40 登记 · 不阻塞）：capability R2 括注 8cd8584「实证在 master」失实——该 commit 经 PR #294 squash 吸收为 bfed4cd · 原 hash 仅任务分支可达 · 实质结论不受影响 · 措辞校正建议 20/10 帽 · **待维护者裁决**。
2. **NIT-2**（40 登记 · 已闭合）：文首状态行陈旧（c1ec310 存量）已被 40 随 v0.6 顺手校正 · 本次 CLOSE 落 done 终态。
3. 仓规两则已生效：后续升级/流程类 task 一律 20-R1 审查文禁 `--allow-no-review`；exempt 扩列须带截止条件/回填义务（语义面人审非机断）。
4. web 仓对应缺口与仓规条款另仓另案（本 task 非范围）。
5. 分支 `task/api-legacy-reviews-backfill` 七 commit 全程本地未 push · PR 合码 + CI 绿 + 分支清理移交维护者终审（维护者授权 m00085/m00500：验收过才 CLOSE · 全程本地 commit 可 push/PR 禁）。
