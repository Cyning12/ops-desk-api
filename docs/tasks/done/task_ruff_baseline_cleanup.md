# Task：ruff-baseline-cleanup（A1 方向 · ruff 存量基线漂移收口：52 错清零 + format 漂移量化/收口 + CI 闸实况裁定）

> **状态**：done（2026-10-18 CLOSE · PR #274 MERGED squash b73bb8a · TC-RC-1~8 全 PASS · ruff check 52→0 · format 223→0（326 全 formatted）· CI 接入 ruff==0.15.21 闸 · F811×9 裁定删死码 262 行 · 归档 done/）
> **类型**：代码质量基线收口（**有码改 · 30 棒 worktree PR 流** · lint/format 机械修复为主 + 24 处人工裁定）
> **上游**：维护者 2026-10-18 会话 m01071「开始A1」选定方向 A1（ruff 存量基线漂移收口）· 00 委派 10 起草（实证基线 00 亲跑提供，本帽已亲跑复核，见「实证锚点」）
> **分支**：`task/ruff-baseline-cleanup`（30 开工时自 master 切出 · 本帽零 git 操作）
> **历史脉络（00 转述 · 未亲核）**：2026-10-17 晨审计时存 F811×4 + ruff format 基线漂移，现已扩散到 ruff check 52 错 → 本 task 同时覆盖 format 漂移量化与收口裁定

---

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `ruff_baseline_cleanup` |
| **git_branch** | `task/ruff-baseline-cleanup` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | 硬闸 = PR CI pytest 绿；本地 `.venv/bin/python -m pytest tests -q` 全量复跑红集须 ⊆ 基线红集（本 task 实证 19 红，见 R1/TC-RC-6），**任一新增红即 FAIL**。ruff 机断：`uv run --extra dev ruff check app tests` → 0 errors；`ruff format --check` 依 F3 裁定形态验收。 |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `none` |
| **graph_delta** | `none` |
| **graph_delta_note** | 纯 lint/format 收口：无新路由/表/事件类型/模块/对外契约；若 F2 裁定涉及 N818 重命名（本 task 默认不取，见范围 F2）须回评本字段 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 基线收口不涉 WikiTrack 正文真值；CI 闸裁定结论留痕于 invoke 与本档修订记录即可 |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,30,40` |
| **invoke_retention_profile** | `default`（10 起草 + 30 修复与逐处裁定 + 40 验证；20 按维护者授权取舍） |
| **experience_capture** | `recommended` |
| **kpi_aggregator** | `n/a` |
| **orchestration** | 10 落稿 → 20 R1（按维护者授权）→ 维护者签闸 → 30 分支修复（F1 自动修 → F2 人工裁定 → F3 format → F4 CI 裁定）→ 40 验收复跑 → PR → CLOSE |
| **freeze_id** | 无 |
| **related_tasks** | [`task_ci_specwave_pin_align.md`](../done/task_ci_specwave_pin_align.md)（CI workflow 改动先例）· [`close_hitl_resume_async_20261015.md`](../close/close_hitl_resume_async_20261015.md) §七.2（仓级测试基线收口建议，红集基线口径参照） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 20, 30 | 2026-10-18 维护者「全A」（m01101）授权 00 代录 · 签注：N1 CI 钉 ruff==0.15.21 · F3 一次性 format 独立 commit · F4 接入 pytest.yml |
| HG-AUDIT-R1 | approved | 30 | R1 签收零阻塞 nit×1（[审查文](../../harness/reviews/task_ruff_baseline_cleanup_audit_R1_20261018.md)）· 2026-10-18 维护者「全A」（m01101）授权 00 代录 · N1 已顺手精化（CI 钉 ruff==0.15.21） |
| HG-GRAPH-MODULES | n/a | — | `graph_change_layer=none` 零图谱改动（纯 lint/format 收口 · 无新模块/路由/表/事件）；若 F2 裁定偏离默认（如 N818 重命名 app 公开异常名）须回评并补签 |

> 关联事实照登：本仓 pytest 本地基线 19 红（2026-10-18 亲跑，见 R1），多为环境依赖面（PG/multi-proc 等）；本 task 不以「本地全绿」为闸，以「CI 绿 + 本地零新增红」为闸。

---

## 背景与目标

方向 A1：ruff 存量基线漂移收口。ruff 配置早已在库（`pyproject.toml:64-73`：target py311 · line-length 100 · select E,F,I,N,W,UP,B,C4,SIM · ignore E501,B008），但存量违规扩散到 52 错且 format 漂移面达 223 文件——根因之一是 **CI 无 ruff 闸**（`.github/workflows/pytest.yml:52-53` Ruff 步骤整段被注释）。本 task 一次性清零存量、量化并裁定 format 漂移、裁定 CI 闸接线，并留可复核证据。

### 实证锚点（10 亲跑复核 2026-10-18 · master `c956d87` · 30 必读）

| 主题 | 命令 / 路径 · 锚点 | 现状（亲跑实录） |
|------|---------------------|-------------------|
| ruff 版本 | `uv run --extra dev ruff --version` · `uv.lock:1831-1835` · `pyproject.toml:47` | **0.15.21**（specifier `>=0.5,<1` · lock 钉 0.15.21 · 本 task **钉死不升级**） |
| check 总量 | `uv run --extra dev ruff check app tests` | **Found 52 errors · 28 fixable with --fix**（另 8 hidden unsafe fixes · 不启用） |
| check 分布 | `... --statistics` | F811×9 · I001×9[*] · C408×7 · SIM117×7[*] · E402×5 · SIM300×4[*] · UP035×3[*] · F401×2[*] · UP045×2[*] · C401×1 · N814×1 · N818×1 · UP034×1[*]（[*]=自动可修共 28 · 其余 24 需人工判） |
| F811 九对（先定义行→遮蔽行） | `--select F811 --output-format concise` | tests/eval/test_capability_redlines.py：572→777（test_r10_declared_contract_rejects_nonconforming_result）· 617→822（test_r10_is_not_vacuous）· 640→845（test_r11_session_budget_and_kill_switch_block_before_downstream）· 703→908（test_r11_kill_switch_disables_capability）· 743→948（test_r11_is_not_vacuous）；tests/test_capability_manifest.py：468→523（test_output_schema_bad_shape_rejected）· 476→531（test_output_schema_valid_shape_loads）· 554→597（test_environmental_failure_classification）· 581→624（test_http_capability_error_exposes_structured_cause） |
| E402 五处 | `--select E402` | app/ops/capability/adapters/http_generic.py:65-66（:63-64 有注释说明与 jsonpath.py 共用实现 · :66 已带 `# noqa: F401` 兼容导出注记 → 疑似有意布局，判 noqa 留痕或上移）· tests/test_lg_rag_sse_token_stream.py:32,33,39 |
| C408 七处 | `--select C408` | tests/eval/test_capability_redlines.py:113 · tests/test_capability_domain_allowlist.py:50 · tests/test_capability_http_adapter.py:59 · tests/test_capability_idempotency.py:70 · tests/test_capability_persistence_db.py:166,228 · tests/test_capability_visibility_and_receipts.py:44（dict()→字面量 · unsafe fix 存在但本 task **不启用 --unsafe-fixes**，手工改） |
| C401 / N814 / N818 | `--select C401,N814,N818` | C401：app/ops/lg_rag/multi/nodes.py:1922（generator→set comprehension）· N814：tests/test_admin_capability_observability.py:214（`GenericHttpAdapter` 别名为常量 `_A`）· N818：app/ops/capability/circuit.py:76（异常类 `CircuitOpen` 无 Error 后缀 · **app 侧公开名，重命名=语义/API 变更，默认裁定 noqa 留痕不改名**，见非范围） |
| format 漂移 | `uv run --extra dev ruff format --check app tests` | **223 files would be reformatted, 103 already formatted**（拆分：app 115 reformat/74 ok · tests 108 reformat/29 ok）——漂移面巨大 |
| CI 闸实况 | `.github/workflows/pytest.yml:46-53` | pytest job 仅跑 pytest；`:52-53` `# - name: Ruff / #   run: uv run ruff check .` **整段注释** → ruff 未入 CI，存量 52 未拦即此因。其余 workflow（lint-wiki-delta/import-linter/tech-graph/deploy-api/ops_sync_kimi_code）均无 ruff |
| pytest 基线 | `.venv/bin/python -m pytest tests -q --tb=no` | **19 failed, 1828 passed, 1 skipped**（68.77s · master c956d87）；红集多为环境依赖面（PG 实连/multi-proc/golden 对拍等），完整红集清单留档于 10 invoke——本地不以全绿为闸，以零新增红为闸 |

### 目标

F1：`--fix` 自动修 28 处并逐类复核无语义变更。F2：人工裁定 24 处（F811 九对逐个 diff 裁定为重中之重）。F3：format 漂移 223 文件量化已得，裁定并执行收口形态。F4：CI ruff 闸裁定（接线或明裁不接 + 理由）。F5：invoke 留档（前后 statistics 对比 + F811 逐对裁定表 + format 数据 + CI 裁定）。终态：`ruff check app tests` = 0 errors，pytest 零新增红，PR CI 绿。

---

## 范围

- **F1 · 自动修 28 处**：在 `task/ruff-baseline-cleanup` 分支跑一次 `uv run --extra dev ruff check --fix app tests`（**不加 --unsafe-fixes**）。逐类复核 diff：I001 仅 import 排序 · SIM117 合并嵌套 with（等价语义）· SIM300 yoda 条件翻转 · UP035/UP045/UP034 现代化改写 · F401 删未用 import。**任一类 diff 出现语义可疑即停下单独裁定**，不混入自动修。
- **F2 · 人工判 24 处**：
  - **F811×9（重点风险）**：九对逐对 diff 先定义与后定义函数体。**两版一致** → 删先定义死码（保留后定义）；**两版发散** → 判定保留意图（重命名先定义使两测并存，或确认先定义确为过时死码再删），**意图不明即停派照登不硬删**（见非范围）；每对裁定在 30 invoke 留痕（对名/两版行号/一致或发散/裁定/理由）。
  - **C408×7**：手工 dict()→字面量（不启用 unsafe fixes）。
  - **E402×5**：判定有意延迟/布局（如 http_generic.py:65-66 与 :63-64 注释、:66 既有 noqa 互证有意）→ 加 `# noqa: E402` + 一句话理由留痕；非有意 → 上移 import。
  - **C401×1**（nodes.py:1922）：改写 set comprehension，确认消费方只要集合语义。
  - **N814×1**：测试内别名 `_A` 改非常量形或 noqa，30 裁定。
  - **N818×1**（circuit.py:76 `CircuitOpen`）：**默认裁定加 `# noqa: N818` 留痕，不改名**（app 侧公开异常名，重命名属语义/API 变更，非本 task 范围；若维护者另欲改名须另立 task）。
- **F3 · format 漂移收口**：漂移面已量化（223 reformat/103 ok · app 115 + tests 108）。**本 task 采纳「一次性格式化收口」**：`uv run --extra dev ruff format app tests` 全量跑，**独立 commit**（与 F1/F2 修复 commit 分离，便于 review 时整commit跳过机器格式化 diff）；format 后 `ruff format --check app tests` 须 0 would-reformat。若 30 实证发现格式化引发任何测试新增红或 import-linter 破约，回退该 commit 并明裁「不修只钉现状」+ 理由留档。
- **F4 · CI 闸裁定**：实况 = ruff 未入 CI（pytest.yml:52-53 注释段）。**本 task 提议把 ruff check 接入现有 `.github/workflows/pytest.yml`**（解开/改写注释段为 `.venv/bin/ruff check app tests`，与既有 uv 安装面一致）；此属 CI workflow 改动，须在 PR 描述与 30 invoke 显式注明。若维护者在签闸时裁定本 task 不接 CI，则 30 明裁「不接 + 理由 + 后续建议」留档，不擅自改 workflow。
- **F5 · 留档**：30 invoke 含 修复前后 `--statistics` 全量对比、F811 逐对裁定表、F3 format 数据与裁定、F4 CI 裁定；40 invoke 含验收复跑证据。

## 非范围

- **不改任何业务逻辑语义**：自动修逐类复核 + 人工裁定均以零语义变更为硬约束；F811 裁定若涉测试意图不明 → **照登停派，不硬删**，上抛维护者。
- **不升级 ruff 版本**：钉 0.15.21（uv.lock:1833）；不改 `pyproject.toml:47` specifier、不改 `[tool.ruff]` select/ignore 规则集（规则集演进另立 task）。
- **不启用 `--unsafe-fixes`**（8 个 hidden fixes 不在面内；C408 等手工改）。
- **不重构被触及文件的无关代码**（不动函数体逻辑、不改测试断言意图）；format commit 仅 ruff format 产物，零手改混入。
- **存量本地红集不治理**：pytest 基线 19 红的消解非本 task（承 close_hitl_resume_async §七.2 仓级测试基线收口建议，另案）。
- 图谱/Wiki/部署面零改动；不改 alembic/、docker-compose.yml、生产任何面。

---

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| FP-1 闸 pending 即 30 改码 | GATE_VERIFY **拒开工**（真值在本档人工闸表；HG-AUDIT-R1 pending → 30 拒改码） | 是 | — |
| FP-2 `--fix` diff 语义可疑 | 停下不提交；可疑类剔出自动修，转人工裁定并留痕 | 是 | 30 invoke |
| FP-3 F811 两版发散且意图不明 | **不硬删不硬改**，照登停派上抛维护者裁定；该对可挂起，其余对继续 | 是 | 30 invoke 裁定表 |
| FP-4 E402 误判（上移后循环 import/破约） | 改回 noqa: E402 + 理由留痕；import-linter 复跑证零破约 | 是 | 30 invoke |
| FP-5 format 引发新增红 / import-linter 破约 / CI 红 | 回退 format commit，明裁「不修只钉现状」+ 数据留档；不带着红交付 | 是 | 30 invoke + PR 说明 |
| FP-6 本地 pytest 新增红（红集 ⊄ 基线 19 红集） | 定位是否本 task diff 所致：是 → 修到零新增红才许交付；否（环境抖动）→ 复跑实证 + 与基线逐名对拍留档 | 是 | 40 invoke |
| FP-7 CI ruff 步骤接上后因版本漂移（CI 装出不同 ruff）误拦 | 步骤须钉 `ruff==0.15.21`（维护者签注 m01101 明裁 · 与 uv.lock:1831-1835 同源一致），禁 `pip install "ruff>=0.5,<1"` 漂移版；出现即修正步骤 | 是 | CI 日志 + PR |
| FP-8 修复过程中发现 ruff 配置本身须改（规则集/select/ignore） | **本 task 不改配置**，照登记录，另立 task | — | 30 invoke |

---

## 验收标准

- [x] **TC-RC-1（机断 · 基线留档）**：30 invoke §一 实录修复前 statistics 全量分布（52 错 · 13 类）· `ruff --version`=0.15.21 · base SHA c956d87。
- [x] **TC-RC-2（机断 · F1）**：`--fix` 后 52→24（28 处消除）；30 invoke §三 逐类复核「无语义变更」留痕；F2 触及面冒烟 166 passed 0 failed。
- [x] **TC-RC-3（机断+人工 · F2）**：24 处全裁定（30 invoke §二/§四）；F811 九对裁定表在 §二（九对全 IDENTICAL → 删先定义）；E402 两处 noqa+理由、三处上移；N818 noqa 不改名。**`ruff check app tests` → Found 0 errors（exit 0）实证**。
- [x] **TC-RC-4（机断 · F3）**：一次性收口执行：format 独立 commit 710521c（纯机器产物）· `ruff format --check app tests` → 326 files already formatted（exit 0）；连锁 noqa 位移单列 commit 66a36eb 留痕。
- [x] **TC-RC-5（机断 · F4）**：接闸落地：pytest.yml 含生效 Ruff 步骤（`.venv/bin/ruff check app tests` · 安装钉 `ruff==0.15.21`）；PR 描述注明 CI 改动；CI 绿以 PR 实证为准（40 复核）。
- [x] **TC-RC-6（机断 · pytest 硬闸）**：本地全量（拷入基线环境 .env）**19 failed / 1828 passed / 1 skipped**，FAILED 清单与基线 19 红集逐名全等、零新增红（30 invoke §六 对拍表）；PR CI pytest 绿以 CI 实证为准（40 复核）。
- [x] **TC-RC-7（机断 · 零越界）**：`git diff --name-only master...HEAD` 全白名单内；pyproject.toml/uv.lock/图谱/Wiki/alembic/docker-compose.yml 零 diff；ruff 仍 0.15.21（30 invoke §八）。
- [x] **TC-RC-8（机断 · 门禁）**：verify EXIT=0（开工+收尾两跑）· task lint LINT: PASS；30 invoke 已落盘 by-task/ruff-baseline-cleanup/（40 invoke 待验收帽落）。

## 依赖

- ruff 配置真值：`pyproject.toml:64-73`（[tool.ruff] · 本 task 零改动）· 版本钉 `uv.lock:1831-1835`（0.15.21）。
- CI 实况：`.github/workflows/pytest.yml:46-53`（ruff 段注释）· 其余 workflow 五件（无 ruff）。
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`。
- CI 改动先例：`docs/tasks/done/task_ci_specwave_pin_align.md` · `docs/tasks/close/close_ci_specwave_pin_align_20261017.md`。
- 闸与流程：`docs/harness/prompts/FRAGMENT_30_gate_verify_v1_zh.md`（GATE_VERIFY 形状 · 本 task 阻塞面 = 30）。

## 给执行帽的必读列表

1. 本 task 全文（实证锚点表 · F811 九对清单 · 非范围五条 · 闸表）。
2. `pyproject.toml:64-73` 与 `uv.lock:1831-1835`（ruff 配置与钉版 · 禁改）。
3. `.github/workflows/pytest.yml` 全文（F4 接闸落点与既有 uv 安装面）。
4. F811 九对所涉两文件（tests/eval/test_capability_redlines.py · tests/test_capability_manifest.py）相关行段亲读后再裁定（禁信转述）。
5. `app/ops/capability/adapters/http_generic.py:40-70` 与 `app/ops/capability/circuit.py:70-80`（E402/N818 裁定上下文）。
6. 10 invoke `docs/harness/invokes/by-task/ruff-baseline-cleanup/invoke_20261018_10_task_draft.md`（实证基线与本地 pytest 19 红集清单）。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|------|------------|----------------------|----------------|
| R0 | 框定：A1 = ruff 存量 52 错清零 + format 漂移（223 文件）裁定收口 + CI 闸实况裁定；30 棒 worktree PR 流 | false | — | 闸未签 |
| R1 | 证据：52 错 13 类分布/24 处坐标/F811 九对行号/format 223 拆分/CI 注释段 :52-53/ruff 0.15.21 钉版 全部亲跑实录；pytest 本地基线 19 红留档 | false | — | 本地红集含环境面，须以零新增红为闸而非全绿 |
| R2 | 方案：F1 自动修逐类复核 → F2 人工裁定（F811 逐对 diff 表 · N818 默认 noqa）→ F3 format 独立 commit 收口 → F4 接 pytest.yml（钉 ruff==0.15.21）→ F5 留档 | false | — | F811 发散对意图不明须停派 |
| R3 | 反例：禁 --unsafe-fixes · 禁升级 ruff · 禁改规则集 · 禁硬删发散 F811 · format 破约即回退明裁 · CI 步骤禁 pip 漂移版 | false | — | format 223 文件 diff 大，review 靠独立 commit 隔离 |
| R4 | 验收：TC-RC-1..8 全机断或可断言（statistics 对比/0 errors/format check 0/CI 绿/红集 ⊆ 基线/零越界白名单/门禁 PASS） | false | — | 无 |
| R5 | 收口：实证齐备、方案与反例闭合、验收可机断；草稿交维护者签闸（HG-TASK-DRAFT/HG-AUDIT-R1 pending · GRAPH n/a） | true | 基线全部亲跑量化，F1–F5 边界闭合，再轮无新信息 | 闸未签；F3/F4 最终形态待维护者签闸时确认 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

ruff 配置在库已久但存量违规扩散（52 错）且 format 漂移 223 文件，根因含 CI 无 ruff 闸。本 task 一次性收口存量并裁定防回归面，不碰语义、不碰配置、不碰版本。

### R1 · 证据收集

全部实证亲跑于 2026-10-18（master c956d87）：check 52 错 13 类（28 自动可修/24 人工判）· 每类精确坐标（F811 九对含先定义行号）· format 223/103（app 115+tests 108）· pytest.yml:52-53 ruff 段注释（其余五 workflow 无 ruff）· ruff 0.15.21（uv.lock 钉）· pytest 本地 19 failed/1828 passed 基线（红集清单留档 10 invoke）。00 提供的基线与亲跑复核一致。

### R2 · 方案生成

30 单分支流水线：F1 `--fix` 28 处逐类复核 → F2 24 处人工裁定（F811 逐对 diff 裁定表为核心交付）→ F3 format 独立 commit 一次收口（破约即回退明裁）→ F4 接 ruff 入 pytest.yml（uv.lock 同源，PR 注明 CI 改动；维护者签闸时可改判不接）→ F5 invoke 留档 → 40 复跑验收。

### R3 · 反例与边界

最大风险一是 F811 误删仍有意图的先定义（对策：逐对 diff + 意图不明停派）；二是 format 大 diff 夹带手改（对策：format 独立 commit 零手改混入）；三是 CI 接闸引入版本漂移（对策：走 uv.lock 同源安装）；四是把本地环境红误当本 task 回归（对策：基线 19 红集逐名对拍）。配置/版本/语义三不碰钉死非范围。

### R4 · 验收/可测性

八条 TC 全部可机断或可对拍断言：statistics 前后对比、ruff check/format --check exit 0、CI 绿、本地红集 ⊆ 基线、git diff 白名单、spec-wave 门禁 PASS、invoke 落盘存在性。

### R5 · 收口

实证齐备、F1–F5 边界闭合、反例有对策。草稿交维护者签 HG-TASK-DRAFT / HG-AUDIT-R1（GRAPH n/a 零图谱变更）；F3 收口形态与 F4 接闸与否的默认建议已写明，签闸时可改判，30 以签注为准。

### 自检结论（执行者）

**30 棒自检：TC-RC-1..8 全 PASS**（CI 绿待 PR 实证由 40 复核，本地面全部机断通过）。实证指针：

- statistics 52→0 · format 223→0（326 ok）· 本地 pytest 19 红集与基线逐名全等零新增红：30 invoke `docs/harness/invokes/by-task/ruff-baseline-cleanup/invoke_20261018_30_ruff_cleanup.md` §一/§五/§六。
- F811 九对全 IDENTICAL 删先定义（§二裁定表）· F1 逐类复核零语义可疑（§三）· F2 余项裁定含 N814 去别名终裁、E402 分治（§四）。
- 越界零：diff 全白名单 · pyproject/uv.lock 未动 · ruff 钉 0.15.21（§八）。
- 已知留痕：F3 连锁 noqa 位移 ×1（commit 66a36eb）；CI Ruff 步骤首跑绿待 PR 实证（FP-7 钉版已落实）。

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-18 | 10-task 落稿（A1 方向 · 实证基线 10 亲跑复核：ruff 0.15.21 · check 52 错 13 类 28 可自动修 · format 223 文件漂移 · CI ruff 段注释未接闸 · pytest 本地基线 19 红 · 三闸 pending/GRAPH n/a 未代签 · 零 git 操作零码改） |
| 2026-10-18 | 30 修复执行回填：TC-RC-1..8 全 PASS（statistics 52→0 · format 223→0 · F811 九对全 IDENTICAL 删死码 · 本地红集与基线 19 逐名全等零新增红 · CI 接 ruff==0.15.21 闸 · diff 全白名单）· 自检结论节实填 · 30 invoke 落盘 |
| 2026-10-18 | 50 CLOSE（维护者 m01131 授权合并+关账）：PR #274 squash b73bb8a 已并 · 归档 done/ · 状态行 CLOSED · README 登记 · invoke_20261018_50_close.md 落盘 |
