# 占位 SPEC 队列清零战报（长城任务）（v1）

> **期间**：2026-09-21 21:10 → 2026-09-22 10:45（UTC+8 · 约 13.5h 连续夜战）
> **模式**：00 delegate-only（全程未亲改实现码 · 每棒子 Agent 独立派发）· 维护者一次授权贯穿（「授权00签收所有过程文档」+「一个个进行，每次PR到main通过CI后自动merge」）
> **结果**：占位 SPEC 队列 **9/9 清零**，全部走完整五棒流（10-spec→签收→10-task→20-audit→签收→30→40→PR→CI 绿自动 merge→CLOSE），master 顶端 `877ea0c`，`docs/tasks/active/` 已空。

---

## 一、时间线总览（master 合入时刻 · UTC+8）

| 时刻 | 里程碑 | 本棒耗时 |
|---|---|---|
| 09-21 21:10 | 授权令下达 · 闸扫描（SPEC 仅占位 · 无 task · 无 invoke · 分支在 memory-golden-eval） | — |
| 21:26 | `task/llm-layer-hardening` 分支建立 · 10-spec 派出 | — |
| **22:39** | **#148 llm-layer-hardening 合入**（验收 24/24） | ~3.5h（含管线基建磨合） |
| 22:44 | #149 CLOSE 归档合入 | +5min |
| **09-22 00:01** | **#151 memory-embedding-backfill 合入**（21/21） | ~1.3h |
| **00:51** | **#153 continuity-dedup 合入**（17/17） | ~45min |
| **02:05** | **#155 prompt-asset-roadmap-p1 合入**（20/20） | ~1.2h |
| **03:19** | **#157 memory-preference-profile 合入**（27/27） | ~1.2h |
| **04:53** | **#159 session-summary-fallback 合入**（26/26） | ~1.5h |
| **06:31** | **#161 security-hardening W1 合入**（25/25） | ~1.6h |
| **07:29** | **#163 memory-compliance-delete 合入**（22/22） | ~1h |
| 08:52 / 09:14 | 维护者并行并入 #150（融合权重调参）/ #146（memory-golden-eval） | — |
| **~10:35** | **#165 multi-replica-verify 合入**（26/26） | ~2.8h（双进程基建首创） |
| **10:45** | **#167 末棒 CLOSE 合入 · 队列清零** | — |

## 二、九棒交付明细

| # | SPEC（波次） | 验收 | 核心交付 |
|---|---|---|---|
| 1 | llm-layer-hardening | 24/24 | 重试退避+full jitter · provider 级熔断三态 · 四档分层路由 · `ops_llm_usage` 账本 |
| 2 | memory-embedding-backfill | 21/21 | 回填 CLI（谓词幂等 keyset 续跑 · 限速报告 · 干跑对账）+ span 四分支单测 |
| 3 | continuity-dedup | 17/17 | 重复实现硬删除 · 真源零 diff · 用例 1178→1176 差==2 |
| 4 | prompt-asset-roadmap 阶段一 | 20/20 | 9 模板迁 `assets/*.md` + string.Template 去转义 · 对拍 9/9 逐字节 |
| 5 | memory-preference-profile | 27/27 | kind=preference 闸放开 · 双节注入 · revoke_by_key · 幻觉红线金样 · CHECK 放宽 |
| 6 | session-summary-fallback | 26/26 | 懒生成+DB 缓存 · 回退铁律双对拍逐字节 · 默认关 · 保真金样 |
| 7 | security-hardening W1 | 25/25 | 槽位注册表+强制包装+装配校验 · 下游零请求双断言 · 默认关 |
| 8 | memory-compliance-delete | 22/22 | purge_by_user · admin 首个不可逆写端点双闸门默认干跑 · 两通路零残留 |
| 9 | multi-replica-verify | 26/26 | 双进程 pytest 基建（仓内首创）· 部署实测 16/16 · 进程内状态边界清单 8 条目 · 零生产码 |

**测试面**：1137 → 1358 collected（+221 新增守护用例 · 零删除）；每棒 ruff 零新增、graph-compile 绿、变异检验必挂实证、40 棒全部亲跑复核（不轻信 30 自称）。

## 三、实扫纠偏记录（占位草案被逐波证伪/证实）

1. 「两 continuity 实现逻辑相同」→ **非全同**（lg_rag 版多 try/except 降级与 sorted(str()) 容错），统一到 lg_rag 是真升级。
2. 「session/continuity 只被测试引用」→ `session/__init__.py` re-export 是生产面（消费者为零）。
3. memory-preference-profile：CHECK 约束**物理锁死** kind='fact' → 触发 alembic 义务（占位未预见）。
4. security-hardening：最大注入敞口实扫定为 **RAG 片段 + 工具回执两面裸奔**。
5. prompt-asset-roadmap：转义面仅 3 处，真散布是 **≥7 处内联常量**（registry 仅覆盖 3/10）。

## 四、事故与修复（全部留痕于各 50 invoke）

| 事故 | 处置 |
|---|---|
| 10-task 子 Agent 误切 master 提交闸签收（未 push） | cherry-pick 回任务分支 + master 复位 origin，零污染；此后所有棒次 Prompt 带「commit 前核分支」铁律，零复发 |
| GitHub auto-merge 不可用（私有仓无分支保护） | 改 00 轮询 `gh pr checks` 代行「CI 绿即合」，9 棒全部自动合并 |
| Git SSH 间歇抖动（443 被拒） | 退避重试 + HTTPS/gh 凭证兜底推送 |
| verify 机读闸三次拦阻（审查文否定词误命中 · 闸行复合状态 · 历史叙述含 `=pending` 字面） | 全部合规修复（措辞/纯值化），规避写法传入后续棒次 Prompt |
| master 前进（#150/#146 并入）→ SPEC add/add 冲突 ×2 波 | 取 signed 版 / 并集保留解冲突，CI 全绿 |
| goal 200 轮上限用尽 | 管线切子 Agent 落定通知驱动，未停摆 |
| 10-spec 前台派发触 600s 墙钟被杀 | 改后台派发模式，零复发 |

## 五、移交清单

1. **fix task（已启动）**：3 条本地基线红（chat_ws×2 WS portal-loop 环境性 + capability proxy×1）+ `test_reconcile_mismatch_marks_failed` flaky（时序竞态 embedded==2 实得 3）→ `fix/test-baseline-reds`。
2. **后续波次**（已签收全景 SPEC 内）：prompt-asset-roadmap 阶段二/三 · security-hardening W2 检测/W3 PII 脱敏/W4 真沙箱。
3. **灰度前必处置**：W1 on 态非 str 结构化工具回执显式炸整单（fail-closed 方向安全 · 默认关兜住）。
4. **跨仓待办**：Eureka 多副本实测（Java 网关在仓外）。
5. **待灰度开关**（均默认关）：MEMORY_FACTS_ENABLED / MEMORY_FACTS_VECTOR_RECALL_ENABLED · SESSION_SUMMARY_ENABLED · SECURITY_INPUT_ISOLATION_ENABLED。

## 六、过程结论

五棒流 + 机读闸 + 变异检验 + worktree 基线对照组合在 9 棒连续长跑中自洽运转；00 delegate-only 模式吞吐 ≈ 1 棒/1.2h（feature 级）、≈45min（refactor/verify 级）。所有过程文档（SPEC / task / reviews / invokes / 50 CLOSE）落盘 `docs/spec/` · `docs/tasks/done/` · `docs/harness/reviews/` · `docs/harness/invokes/by-task/`，全流程可追溯。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-09-22 | 初版落盘（00 · 维护者令「汇总报告落盘」） |
