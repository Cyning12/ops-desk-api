# PROMPT_00：spec 战役交接（2026-10-11 · 第一/二梯队+web 联调 SPEC）

> 本档承接 PROMPT_00_hitl-consumption-loop-handoff_20261009.md 先例——消费回路战役已全链收官（见 §0），本档面向**新的 00**交代当前盘面与下一棒任务。

## 0. 前战役收官态（hitl-consumption-loop · 全 CLOSED）

| 线 | 交付 | PR |
|---|---|---|
| D1 compose 透传 | OPS_HITL_PERSISTENCE 空默认透传 | #207/#208 |
| D2 testing 写 capability | testing.v1.yaml+OPS_CAPABILITY_EXTRA_MANIFESTS/ALLOW_WRITE_TAGS | #209/#210 |
| T3 strategy env 口 | OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS | #213 |
| T1 消费回路 | decide 消费+unlock 回填 | #216/#217 |
| T2 auto_resume | 自动续跑+SKIP LOCKED+补偿扫描 | #218/#219 |
| env 补登 | .env.example 五键 | #220 |
| 保号+persist guard | replan 保号+建单前检查 | #221/#222 |
| 验收 | 20261010 checklist 8/8 PASS | #223 |
| D1 auto_resume 认领竞态 | _interrupt_metadata_visible 只读就绪校验 | #224/#225 |
| SPEC v1 §9 三钉案 | 遗留排序入 SPEC | #226 |

## 1. 本战役收官态（第一/二梯队 · goal-5183d236）

| 线 | 状态 | PR |
|---|---|---|
| 序2 repo-logging-init | CLOSED（import 期 basicConfig · OPS_LOG_LEVEL fail-closed） | #227/#229 |
| 序3 specwave-verify-baseline | CLOSED（legacy-gate-exempt.yaml 93 档豁免+双址规约档） | #228/#230 |
| A面 B1 capability-mine + B2 manifest_errors | CLOSED（维护者 checklist 三项待验 · close 档第七节） | #231/#234 |
| 序1 hitl-approved-replan-quality | CLOSED（维护者 checklist 在 close 档第九节） | #233/#235 |
| web-integration SPEC | v0 signed 入 master（F1-F10/S1-S7/T-W1~W4/Q1-Q4） | #232 |
| B面 dialogue-full-view SPEC | v0 signed（worktree t-dialogue-full-view 保留 · Q1-Q5 待维护者） | 未 PR |

## 2. 下一棒任务队列（按优先级）

### 2.1 维护者决策点（阻塞下列线 · 须维护者答）

| 决策点 | 所属 | 影响 |
|---|---|---|
| web SPEC Q1-Q4 | docs/spec/web-integration/SPEC-web-integration_v0.md | 解锁 T-W1~W4 拆 task |
| B面 SPEC Q1-Q5 | docs/spec/dialogue-full-view/SPEC-dialogue-full-view_v0.md（worktree t-dialogue-full-view 保留） | 解锁 B-E1/B-E2/B-F1 拆 task |
| A面/B面 维护者验收 checklist | close_tool_catalog_page_b1b2_20261011.md §7 · close_hitl_approved_replan_quality §7 | 令③ m01606 回归 review 组织 |
| 终局 §5 SPEC-C | DESIGN_agent_contribution_endgame_v0_zh.md §3.1/3.2/3.3 | 闸级裁定 · 挂起等维护者信号 |

### 2.2 可立即立项（无外部阻塞 · 按序）

1. **序1 N1 注入缺口**：nodes.py:1172 locked 空分支 preserved_block 不注入（LLM 仍盲 · write 护栏兜底在 · 40 N1 建议另立 task · SPEC §9 序1 后续项）。
2. **序2 N-40-1**：app/main.py:9-12 import 链先于 :38 _init_logging() 窗口（WARNING+ 走 lastResort 裸格式 / INFO 被吞 · nit 级）。
3. **verify 上游根治**：spec-wave findLatestReview 支持址B docs/audits/task-review/（双址规约档 CONVENTION_review_gate_dual_address_v1_zh.md 已钉过渡方案 · 上游 issue/PR）。
4. **B2 NIT-3 / admin items 全字段数组**（close 档后续建议四条照录）。

### 2.3 维护者答 Q 后启动

- **T-W1~W4**（web 联调四 task · SPEC-web-integration §拆 task 规划 · 双仓：api 侧契约微调+web 侧实现 · web 仓 active task specwave_upgrade_3_0_0/tenant_context_chat 注意不撞）。
- **B-E1/B-E2/B-F1**（B面三 task · SPEC-dialogue-full-view §拆 task 规划 · B-F1 前端专项 SPEC 另立 ops-desk-web 仓 docs/spec/）。

## 3. 环境坑全集（本战役沉淀 · 复跑必读）

| 坑 | 真值 |
|---|---|
| 代理 | macOS 全局代理时 NO_PROXY 含 `[::1]` 炸 httpx（InvalidURL ':1]'）→ NO_PROXY 加 127.0.0.1,localhost 去方括号 |
| .env 作用域 | app/config.py:11 load_dotenv 钉仓根 .env → worktree 缺 .env 时 SILICONFLOW_API_KEY=dummy-probe 口径 · 401 invite token 排查=PYTHONPATH=$PWD+OPS_DESK_SECRET 两侧对齐（scripts/create_initial_user.py sys.path[0] 坑） |
| capability 门禁 | scripts/acceptance/capability_acceptance.sh 需 worktree .venv → 软链主仓 .venv 先例 |
| 本地红归因 | 4-7 红（capability_lookups×3/lg_rag_multi/memory_vector 等）=master 基线对拍判环境性 · 勿当回归修 |
| compose 端口 | worktree compose 端口被主仓占用 → 复用主仓栈或改端口 |
| curl 三坑 | 全 URL（无 :8050 简写）· POST 必带 Content-Type: application/json · jq 路径 .visible_ids（catalog 返回对象非数组） |
| uvicorn 裸起 | app 侧零 logging 初始化（序2 已修）· 验收期坑位：须自带 basicConfig 的 /tmp/serve.py（序2 merge 后免） |
| SSE 端点 | /api/ops/chat/stream 已 410 Gone → /api/ops/lg-rag/stream |
| web 仓 | Vite proxy /api→VITE_API_PROXY\|\|127.0.0.1:8000 · macOS localhost IPv6 坑 · cookie withCredentials · X-Ops-Tenant-Id 头 |

## 4. 机读纪律坑全集（spec-wave / harness 契约 · 本战役沉淀）

1. **task lint 契约**（TASK_TEMPLATE.md）：节名无编号（## 验收标准）· ## 失败路径四列表 · ### 自检结论（执行者）· 元信息 wiki_delta/wiki_delta_note 必填 · 闸表 4 列 human_gate_id|status|blocks_hats|说明（3 列触发空解析告警）· status 单元格纯 approved（粗体+括注解析失败误报 BLOCKED → 注解移说明列）。
2. **verify 真码**：管道吞码坑——`npx spec-wave verify 2>&1 | tail` 报 EXIT=0 假象 → 重定向文件再 echo $?。
3. **审查档口径墙**：findLatestReview 只扫 docs/harness/reviews/（址A）+命名 task_<slug>_audit_R<N>_*.md · 新址 docs/audits/task-review/（址B）不入扫描面 → 双址复制纪律（序3 CONVENTION_review_gate_dual_address_v1_zh.md）· **CLOSE 流程「审查文落址A」为硬步骤**（序2 漏 → master verify EXIT=2 救援先例）。
4. **上游钉版**：graph-compile.sh 钉 spec-wave@3.0.1（3.2.0 implementedBy object schema 收紧断 CI · package.json:6/lint-wiki-delta.yml:35 同钉先例）· 仓级 verify 用 3.2.0 豁免机制（legacy-gate-exempt.yaml）不受 CI 钉版影响。
5. **invoke 目录**：by-task/<slug>/ 不存在时 heredoc cat 静默失败 → write 工具代 heredoc。
6. **多棒共享态**：主仓 index 多棒共享——跨棒 checkout 分支会把暂存态带走（a42ac37 事故先例）· 同 worktree 并行棒须文件隔离清单。
7. **棒卡滞判据**：零工作区痕迹≠卡滞（亲读阶段合理）· interrupt 前先等回执一拍 · 骨架先行纪律对长文档棒有效。

## 5. 新 00 启动 Prompt（复制即用 · 自包含）

\`\`\`
你是 ops-desk-api 仓的 00 编排棒（delegate-only：闸扫描→派子 Agent→短报→CLOSE · 禁亲改实现码 · 例外须维护者明文授权留痕）。
先读三档进入状态：
1. docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md（本交接档 · 队列/坑/纪律全集）
2. docs/harness/CONVENTION_review_gate_dual_address_v1_zh.md（审查档双址规约）
3. docs/spec/ 目录四 SPEC 状态行（tool-catalog-page v0 signed · dialogue-full-view v0 signed 在 worktree · web-integration v0 signed · hitl-approval-consumption v1 signed）
当前盘面：master 已含第一/二梯队全部交付（#207-#235）· active/ 零在途 task · worktree 仅剩 t-dialogue-full-view（B面冻结等 Q1-Q5）。
你的第一棒任务：等维护者答 §2.1 决策点 → 按 §2.2/§2.3 队列立项。
纪律集（本战役沉淀 · §3/§4 全集必读）：
- 棒预算 15-60 分钟 · 骨架先行 · 红测先行 · 零痕迹≠卡滞（interrupt 前等回执一拍）
- verify 重定向取真码 · 审查文落址A 是 CLOSE 硬步骤 · 闸表 4 列 status 纯 approved
- graph-compile 再生噪音一律 checkout 还原 · SSH 抖动用 gh api/HTTPS 回退
- 主仓 index 多棒共享 · 同 worktree 并行须文件隔离清单 · worktree .venv 软链主仓
- CLOSE 前维护者验收 checklist（令③）· 需人签收档 00 可代录（授权 m00059/m00255/m01606 先例）
\`\`\`
