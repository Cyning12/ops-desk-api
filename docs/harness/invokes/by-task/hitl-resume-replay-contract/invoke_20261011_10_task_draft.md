# invoke：10-task 起草（hitl_resume_replay_contract · 2026-10-11）

> **帽位**：10-task（任务需求分析 · 只起草文档 · 零实现码改动）
> **task**：`docs/tasks/active/task_hitl_resume_replay_contract.md`（本帽产出 · draft）
> **worktree/分支**：`/tmp/ops-desk-api-fobs` · `task/hitl-resume-obs-drafts`（base master `92a8526` · 主仓 checkout 在途（uv.lock 脏）未动）

## 立项令

ops-desk-web 联调链 00 委派（T-W2 FP-1 报回 · web PR #61）：联调实证暴露两后端观察项，按 FP-1 纪律报回 api 仓另立 task——F-OBS-1 resume 终帧 `done{status:'resumed'}` 缺 `latency_ms`/`model`（S3 replay seq18 实证）；F-OBS-2 run 在飞时 `POST /lg-rag/replay` 瞬返 500（S2 run `640d68970a564fbb8459d8d40cb1c5f6` 实证），建议语义化 409/Retry-After。

## 输入真读清单（本帽亲读 · 非凭记忆）

| 文档/码面 | 读取要点 |
|---|---|
| 00 委派令（联调链 T-W2 FP-1 报回） | 两观察项实证锚（S3 seq18 / S2 run id）· 闸表口径（HG-TASK-DRAFT=approved / HG-AUDIT-R1=pending）· 禁区（不改 app/ · 不动主 checkout · 不合并 PR） |
| docs/tasks/active/task_hitl_n1_locked_branch_inject.md | task 文件范式（元信息表 · 闸表四列 · 锚点表 · 思考轮控制表五列 · early_stop） |
| docs/tasks/done/task_lg_rag_sse_subtask_message.md 等 freeze 先例 | `lg-rag-sse-v1` 不新 freeze · payload 增可选键先例（survey 全仓 freeze_id 用法） |
| app/ops/hitl/resume.py:112-159 | `ResumeEventSink.close()` :124-134 终帧仅 `{run_id, thread_id, status, events_persisted}`——F-OBS-1 缺口核真（确无 latency_ms/model） |
| app/ops/lg_rag/sse_stream.py:455-491 | live 流 done 对照面：:471/:488 含 `latency_ms`；waiting_approval 终帧 :465-474 含 status |
| app/ops/chat/streaming.py:280-297 | chat 流 done :290-297 含 `latency_ms`+`model`——前端徽标字段期望的形态来源 |
| app/ops/lg_rag/router.py:332-373 | replay 端点：:350-356 try/except **仅捕** `LgRagRunNotFoundError`→404 · 其余异常逃逸即 500（F-OBS-2 机理面） |
| app/ops/lg_rag/event_store.py:128-169 | `assert_run_owned`/`load_events_after` 读取面（在飞态异常类型未实证 · 留 30） |
| docs/harness/invokes/by-task/b2_nit3_admin_items_array/invoke_20261011_10_task_draft.md | 10 invoke 留档范式（立项令 · 真读清单 · 裁定 · 门禁实证 · 遗留） |

## 关键裁定（留痕）

1. **两观察项合并为一 task**（委派令授权「可合为一 task 或两枚」）：同源（web 联调 T-W2 同批报回）· 同面（lg-rag/hitl SSE/HTTP 契约）· 各自面极小（单帧增键 / 单端点错误语义）——拆两枚徒增 orchestration 面，合并 F1/F2 双范围项。
2. **model 键不锁死**：resume 路径是否持有 run_model 未实证（FP-1 裁定面）；latency_ms 必补（对照面口径现成），model 可得则补、不可得钉案照登，**禁伪造值**。
3. **在飞 500 根因不锁死**：router.py:350-356 单异常捕获为机理面实证，在飞态具体异常类型留 30 亲测钉案；建议语义 409+Retry-After，等价语义化 4xx 开放。
4. **闸表**：HG-TASK-DRAFT=approved（00 委派令代录 · 委派令显式口径）· HG-AUDIT-R1=pending / HG-GRAPH-MODULES=pending（待 20 R1 + 维护者签 · 不代签）。

## 产出

- task 文件：`docs/tasks/active/task_hitl_resume_replay_contract.md`（背景双实证锚 · 范围 F1–F4 · 非范围六条 · failure_paths 六行四列表 · TC1–TC5 · 思考轮 R0–R5 early_stop at R5）
- 人工闸表三闸：HG-TASK-DRAFT **approved**（00 委派令代录）· HG-AUDIT-R1 / HG-GRAPH-MODULES **pending（未代签）**
- graph_change_layer 预判 `G-L1`（hitl/resume.py 终帧组装 + lg_rag/router.py 错误语义 · 行为表述面 · 30 按实判回写义务钉死）
- freeze_id `lg-rag-sse-v1`（不新 freeze · 不新 event_type · payload 增可选键承先例）
- review_hat `20` · required_invoke_hats `10,20,30,40` · invoke_retention_profile `default`

## 门禁实证（重定向取真码）

- `npx --yes spec-wave@3.3.0 task lint --file docs/tasks/active/task_hitl_resume_replay_contract.md > /tmp/lint_hrrc.log 2>&1; echo EXIT=$?` → **EXIT=0 · LINT: PASS**
- `npx --yes spec-wave@3.3.0 verify --target . --task docs/tasks/active/task_hitl_resume_replay_contract.md > /tmp/verify_hrrc.log 2>&1; echo EXIT=$?` → **EXIT=2 · VERIFY: BLOCKED**——HG-AUDIT-R1 / HG-GRAPH-MODULES pending 属**正确语义**（未代签 · 待 20 R1 + 维护者签）；HG-TASK-DRAFT approved 解析正常（00 委派令代录口径）
- verify 后 `git status --short`：仅本 task 两件新档（task 文件 + 本 invoke）· **零再生噪音**

## 遗留

- HG-AUDIT-R1 前需 20-task-audit R1 落盘；三闸全 approved 前 30 拒开工。
- 在飞态异常类型枚举、model 键可得性、「在飞」机断判定面——刻意开放留 30 实证钉案。
- 本 PR 纯 docs（task 文件 + 本 invoke）；不改 app/ · 不动主 checkout · 不合并 PR（委派令禁区）。
