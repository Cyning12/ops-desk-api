# Invoke：30（含 40）· host-comms-prompt-pack（C2）

| 字段 | 值 |
|---|---|
| hat_id | 30（含 40） |
| task_slug | `host-comms-prompt-pack` |
| task_paths | `docs/tasks/active/task_host_comms_prompt_pack.md` |
| related_review_or_none | `docs/harness/reviews/task_host_comms_prompt_pack_audit_R1_20260901.md` |
| git_branch | `task/host-comms-prompt-pack` |
| created_utc_or_local | 2026-09-01 |
| notes | 00 代签 HG-AUDIT-R1 后派发；**仅 C2 纯函数层**（render_pack + route_intent + pack 元信息）；禁止新 HTTP 路由 · 改 product render/templates 行为 · import session/chat 流路径 · LLM 判定器 · 跨 session 交还（留 C3/C4）· 拷贝 FRAGMENT 漂移 · 真调 harness.* capability · 签 human_gate · 切分支/push/开 PR |

---

## 人工闸扫描（GATE_VERIFY · 30 重填 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 00 代签 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 文 pass | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 不新增一级模块 · 00 代签 · 仅 lg_rag 行备注 | Y | N | Y |

reviews：`task_host_comms_prompt_pack_audit_R1_20260901.md` 存在且内容 pass？ **是**（内容零阻塞 · 非阻塞 4 条 30 知情并逐项处置）

pre-30 invoke：00 + 10 已落盘？ **是**

机械：`npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_host_comms_prompt_pack.md` → **VERIFY: PASS**（exit 0 · 开工前与收尾各跑一次均 PASS）

结论：**可进入读码/改码**（30 首输出已重扫本表）

---

## 可复制 Prompt 快照

hat_id：30（含 40 自检）
task_slug：host-comms-prompt-pack
本帽禁区：新 HTTP 路由；改 `render()`/`get_template()`/`TEMPLATES` 行为；import `app.ops.session`/chat 流路径；LLM 意图判定；跨 session 交还（R1 非阻塞 ③ 留 C3/C4）；拷贝 FRAGMENT 双写漂移；真调 `harness.*` capability / 改 Policy 默认；签发 human_gate；切分支/push/开 PR。

首动作：GATE_VERIFY（FRAGMENT_30_gate_verify）→ 通过再改码。

00 定夺摘要：
- 纯函数层：`render_pack("comms", ...)` + `route_intent(text)` → 严格二值 `"comms"|"product"`；**无新路由**
- 槽位链 = 仓内 kit FRAGMENT 真值（运行时读/内嵌 30 定 · **禁止拷贝漂移** · 测试读真值对比）+ task 字段清单 + 对话策略（澄清→起草→提示人闸）+ 禁令条文（永不签发 human_gate · 写盘仅 docs/tasks+invoke 草稿 · Skills≠verify）
- 意图路由：默认/异常/None/模糊 → product；显式立项意图（SPEC §4 例示作词表种子）→ comms；规则/关键词纯函数
- pack 元信息 `name="comms"`/`session_scope="comms"`/`version`；capability 声明 `harness.verify`/`harness.task_lint`（仅声明不调用）
- product 侧零影响：旧测 `tests/test_prompt_assembly.py` 绿；`router.py` 零 diff

验证：verify · ruff 触及路径 · pytest（CI 等价口径 `DATABASE_URL=postgresql+asyncpg://127.0.0.1:1/invalid` · 旧测零破坏）· graph-compile · lint-wiki-delta。

完成后：回填本 invoke 交付摘要 + task「自检结论（执行者）」；**不 CLOSE（留给 00）**；commit 不 push。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权 · 2026-09-01 · VERIFY PASS

---

## 交付摘要

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS · 可开工（三闸 approved · verify exit 0 · 开工前与收尾各复跑一次均 PASS） |
| 实现 | 新模块 `app/ops/prompts/packs.py`：`render_pack("comms", *, slots=None, base_dir=None) -> PromptPack`（独立装配 · 不改 `render()` · slots 沿用 `<!-- slot:name -->` 机制 · 传入 slots 须含 `REQUIRED_SLOTS=("task_slug","hat_id")` 缺则 `PromptPackError` 点名槽位）· `route_intent`（`strip().lower()` 后词表匹配 · 严格二值 Literal · 异常/None/非 str 一律 product · 永不外抛）· 元信息 `name/session_scope="comms"` · `version="v1"` · `capabilities=("harness.verify","harness.task_lint")`（仅声明）；`__init__.py` 仅追加导出（`render`/`get_template` 原样） |
| FRAGMENT 注入形态（30 定） | **运行时读仓内真值文件**（`docs/harness/prompts/FRAGMENT_*.md` · 仓根 `parents[3]` 解析 · `base_dir` 可覆盖）。理由：SoT 单份无拷贝故物理无漂移；仓内无构建期步骤承载内嵌，内嵌反引入第二份拷贝；部署路径风险由「缺失/为空 → PromptPackError 不静默降级」兜底（tmp_path 断言），且本波纯函数层无部署接线 |
| 关键词词表（30 定） | SPEC §4 种子全量收录：立项 / 开task / 开 task / 开个task / 开个 task / 起草task / 起草 task / 写spec / 写 spec / 写个spec / 写个 spec / 起草spec / 起草 spec / 拆波次 / 走harness / 走 harness / harness流程 / harness 流程；词表外业务措辞一律回退 product（「这个 spec 字段含义」→ product 有断言） |
| 测试 | 新 `tests/test_prompt_packs.py` **44 用例**全纯函数（零 LLM/零网络）：FRAGMENT 子串+真值逐字一致（防漂移）· 禁令条文（永不签发 human_gate / 写盘边界 / Skills≠verify）· task 字段清单 · 对话策略 · 缺文件/空文件/缺槽位/未知 pack 报错 · slots 追加 · 元信息 · route_intent 参数化 comms 9 + product 7 + 回退 7 + 严格二值 · 纯函数可重入 · product 渲染不变 · AST 断言不 import session/chat |
| 自检 | verify exit 0（×2）· ruff 触及路径 exit 0（全量 `ruff check app tests` exit 1 = 2 处**既有**问题 rag/tokenizer UP035 · test_rag_chunker I001 · git stash 核实 HEAD 既有 · 按 P-07 不顺手改）· pytest **CI 等价 exit 0**（543 passed · 39 skipped · 旧 `test_prompt_assembly.py` 8 用例零破坏）· graph-compile exit 0（9 graphs · 生成物 graph.json 仅 generated_at 刷新）· task lint PASS（W4 合法）· lint-wiki-delta PASS（exit 0） |
| 图谱 | `01_modules.md` lg_rag 行备注（C2 pack=comms · prompts 归属本行 · packs.py 纯函数层）+ 人签记录行（00 代签）；未增 implementedBy → G-L2 indexes 无需同步；不新增一级模块 |
| R1 非阻塞 4 条 | 全部处置（① 运行时读形态+理由落自检 ② 词表钉死并落自检 ③ **跨 session 交还未做**（留 C3/C4 · 无范围蔓延）④ 独立装配函数仅复用 slot 机制 · product 零影响由验收条 4 钩住） |
| 已知未测项 | 真 LLM 消费 pack system（非范围）；`base_dir` 缺省解析在部署/打包环境的路径有效性（无部署接线 · 报错语义已测）；误判的运行时跨 session 交还（留 C3/C4）；`harness.*` 真调用（仅声明 · Policy 默认关保持） |
| 禁区核对 | `router.py` 零 diff · `render.py`/`templates.py` 零 diff · 未 import session/chat（AST 断言）· 未做跨 session 交还 · 未签 human_gate · 未切分支/未 push/未开 PR |
| 收尾 | task 验收 9 条勾选 + 自检结论（执行者）表 + 修订记录 30+40 行 + 文末「不 CLOSE（留给 00）」；分笔 commit · 未 push |

关键路径：
- `app/ops/prompts/packs.py`（新增）· `app/ops/prompts/__init__.py`（追加导出）· `tests/test_prompt_packs.py`（新增）
- `docs/_tech_graph/l1/01_modules.md`（lg_rag 行备注 + 人签记录）· `docs/_tech_graph/shared/graph.json`（生成物时间戳）
- `docs/tasks/active/task_host_comms_prompt_pack.md`（验收勾选 · 自检结论（执行者）· 修订记录 · 不 CLOSE）
