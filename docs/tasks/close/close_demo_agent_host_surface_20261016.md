# CLOSE：demo-agent-host-surface（三方演示 · 展示面收敛 · 对外只讲 Agent Host）

> **日期**：2026-10-16
> **Task**：`docs/tasks/done/task_demo_agent_host_surface.md`（本 CLOSE 由 active/ 移位归档）
> **SPEC**：`docs/spec/arch-browser/SPEC-arch-browser_v0.md`（D3：§1 纪律 3 显式修订 + §7 修订记录行）
> **属性**：演示展示面 · 名实分离（只藏不改约）· 双仓（api + web）

## 一、任务信息

- **背景**：维护者 2026-10-16 演示指令（00 窗 prompt）——三方演示对外只讲 Agent Host 能力；内部实现名（lg-rag / LG RAG / LC Evidence / legacy Chat）不出现在演示面；产品语义与端点名不变（freeze 纪律）。
- **范围**：A1 展示名替换（lg-rag→Agent 工作台，D1 已锁）· A2 arch-browser 演示视图收敛（ENG_DEMO_HIDDEN_FLOWS 过滤 + host_modules display 政策）· A3 SPEC 修订（D3）· A4 web 仓菜单/文案 · A5 验收钉 · A6 归档。
- **非范围**：app/ 业务代码、端点改名、_tech_graph 真值、crosswalk、eng-graph-mermaid 在飞改动（留树）。

## 二、交付（三 PR 齐）

| 仓 | PR | squash | 内容 |
|---|---|---|---|
| ops-desk-web | **#70** | `44a77db` | web 面菜单/文案展示名替换（TC-5） |
| ops-desk-web | **#71**（D4 修正） | `46c8c54` | 裁定：Agent 工作台=/chat 直接对话页；/lg-rag 退菜单 meta 恢复 |
| ops-desk-api | **#255** | `370cee4` | api 面 A1-A5：catalog×2 展示文案 + build_site.py display 政策管线 + app.js 演示视图过滤/display 消费 + SPEC §1 纪律 3 修订 + §7 修订行 + dist 重建 + task 档/invokes |

api 侧 CI 四绿（check / import-linter / lint-wiki-delta / pytest）。

## 三、核验结论（api 面 · PR #255 验收实录）

- **TC-1/2（展示名零泄漏）**：dist/site-data.json 演示面载体（home_narrative/entry/waves/concept_mermaid/host_modules[*].display.*）+ dist/index.html grep 零命中 lg-rag · LG RAG · LC Evidence · lc_evidence_chain · legacy Chat；display 中残留命中经核验全部为 chip href 真值 id（TC-1 例外清单①），剔 href 后全 PASS；app.js 新增行旧名仅 4 处过滤代码键名（例外②）。
- **TC-3（build 管线）**：`python3 docs/arch-browser/scripts/build_site.py` EXIT=0，dist 全新生成（host_modules=34 · graphs=9 · freeze 沿用 OPS_DESK_API_TECH_GRAPH_FREEZE_20261014_V1）；surface-only 构建无 eng_l0_mermaid 键——属预期（eng task 未并），grep 断言按实际载体执行并在 PR 正文说明。
- **TC-4（SPEC 修订）**：§1 纪律 3 修订行 + §7 修订记录行均在。
- **TC-6/7（名实分离守护）**：app/ 零 diff · docs/_tech_graph 零 diff（本 CLOSE 链未跑 graph-compile.sh，无 freeze 副作用需回滚）。
- **TC-8（CLOSE 清单）**：三链接齐（web #70 / web #71 / api #255），已回填 task 档。
- **pytest 未跑**（task test_strategy_note 口径：纯 docs/arch-browser 面；CI pytest 绿）。
- **质量钉（本 CLOSE 段）**：`npx spec-wave task lint` PASS（W5 思考轮槽位 warn-only 过渡口径不挡）· 裸 `verify --target .` EXIT=0 PASS（仓级 reviews 扫描 · 豁免命中本 task）· `--task` verify 因「20 R1 审查结论并入 30 invoke」无独立审查文报 missing review → 按扩列纪律 `docs/harness/legacy-gate-exempt.yaml` 新增一枚（四字段齐 · 本 PR 即人审面 · 承 specwave-330 先例 · 豁免≠审查通过）。

## 四、偏差登记

- **web 残留决策点（另裁）**：登录流程两处落地仍指 `/overview`（router 守卫被 `tests/router-guard.spec.ts:45-50` 断言卡住 · LoginView.vue:30 fallback 超 diff 白名单）——若要求登录后默认落地=Agent 工作台，需另裁并最小同步该条断言。
- **eng-graph-mermaid 脏树留树**：主工作树未提交 eng 改动原样保留，归其自身 task；本 task 切分采用新 worktree 自 master 摘 hunk，主树零触碰（FP-7 基线风险消解）。
- **切分归类存疑 hunk**（判定依据已入 PR #255 正文）：build_site.py `_ENG_L0_DEMO_*` 演示政策虽含「demo」字样但只服务 eng_l0 管线→判 eng；app.js 「工程 G-L0→工程图谱」改名随 mermaid 面板重写→判 eng；web/index.html cache-bust `?v=20261015-mz3`→判 eng；style.css 全部 mermaid 交互样式→判 eng；README 全为 eng 视图说明→判 eng。

## 五、签录（闸态）

| 闸 | 状态 | 签录 |
|---|---|---|
| HG-TASK-DRAFT | approved | 00 代录（维护者授权 2026-10-16） |
| HG-AUDIT-R1 | approved | 00 代录（维护者授权 2026-10-16） |

## 六、资源清理

- 本 CLOSE：task 档 `git mv` active/ → done/ · active/README 登记表顶部补归档行 · done/README 修订记录补登（含近两次漏登的 hitl-resume-async #252）· 本 CLOSE 档落盘 · `docs/harness/legacy-gate-exempt.yaml` 扩列一枚（reviews 缺口豁免 · 四字段齐）。
- **不删任何东西**：worktree `demo-agent-host-surface` 与分支 `task/demo-agent-host-surface`、`close/demo-agent-host-surface` 移交 00 统一清理。
- 主工作树（eng-graph-mermaid 脏树）全程零触碰，开工/收尾 git status 快照逐行一致。

## 七、维护者验收 checklist

- [ ] PR（本 CLOSE 归档 PR）diff 仅五类：task 档移位+回填 · active/README 一行 · done/README 两行 · 本 CLOSE 档 · legacy-gate-exempt.yaml 扩列一枚——**零码零配置**。
- [ ] task 档状态行含 api PR #255（squash `370cee4`）· TC-8 三链接齐 · 自检结论 50-CLOSE 段 · 经验总结 worktree 隔离条。
- [ ] active/README 新归档行体例与既有行一致（含三 PR 号 + eng 脏树留树声明）。
- [ ] 核后由维护者 merge（本棒不 merge）。

## 八、修订记录

| 日期 | 摘要 |
|---|---|
| 2026-10-16 | 初版（50-CLOSE 归档段 · 30 子 Agent 代笔 · 00 口径） |

## 九、附录

- 切分方法钉案：混合脏树切分用 worktree 隔离——主树零触碰、新 worktree 自 master 摘本 task hunk（整文件直复制 + 混合文件人工归类拆 hunk + 存疑 hunk 列依据入 PR 正文）、dist 靠重建不靠手切、漂移/垃圾文件（uv.lock marker 漂移 · .pnpm-store/ · pnpm-lock.yaml）甄别排除。
- 过程 invoke：`docs/harness/invokes/by-task/demo_agent_host_surface/`（30-implement · 50-close 代录）。
