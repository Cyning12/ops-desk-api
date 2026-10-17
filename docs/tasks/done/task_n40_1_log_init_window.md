# Task：n40-1-log-init-window（logging 初始化窗口收口 · app/main.py:9-12 import 链先于 :38 _init_logging 的 lastResort 裸格式 / INFO 吞失）

> **状态**：done（CLOSED 2026-10-17 · PR [#239](https://github.com/Cyning12/ops-desk-api/pull/239) MERGED（squash `9c07ab4` · 2026-10-11T05:56:16Z）· 方向 A 落地（app/main.py 行序上移 +10/-5）· 红测先行 RED(5)→GREEN(7+3) · TC1–TC4 全绿 · 20 R1 PASS-WITH-NITS（NIT×4 已回填）· 三闸 approved（00 代录 · 授权 m00106）· CLOSE 归档 done/ · 细节见 CLOSE 文档 [`../close/close_n40_1_log_init_window_20261017.md`](../close/close_n40_1_log_init_window_20261017.md)）
> **类型**：上游 nit 收口（bugfix 性质 · nit 级 · 实证驱动 · repo-logging-init CLOSE N-40-1 裁定落地）
> **依据**：`docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 2 项 · `docs/tasks/close/close_repo_logging_init_20261011.md` §四 N-40-1（nit 照登原文）+ §七 后续建议 1（修法候选留本 task 裁定）· `docs/harness/invokes/by-task/repo-logging-init/invoke_20261011_40_verify.md` :77/:91 NIT 登记
> **分支**：`task/n40-1-log-init-window`（base = master `286d825`）
> **worktree**：`../ops-desk-api-worktrees/t-n40-1-log-init-window`

## Harness 元信息

| 字段 | 值 |
|------|-----|
| **task_slug** | `n40-1-log-init-window` |
| **git_branch** | `task/n40-1-log-init-window` |
| **implement_repo** | `ops-desk-api` |
| **test_strategy** | `required` |
| **test_strategy_note** | TC1 子进程 import 顺序红测先行（修复前裸格式红、修复后钉死格式绿 · 禁赌时机）+ TC2 窗口 INFO 可见性断言 + TC3 OPS_LOG_LEVEL 回归组 + TC4 工程面（pytest 基线对拍 / ruff / graph-compile / lint-wiki-delta） |
| **code_quality_bar** | `L2_backend` |
| **graph_change_layer** | `n/a`（预判无图谱变更 · 若 30 采方向 B 新增 `app/ops/logging_config.py` 则按实判升 G-L2 indexes 同步义务 + HG-GRAPH-MODULES 00 代录） |
| **graph_delta** | `n/a`（预判 · 无新一级模块/跨模块边/路由/SSE 事件/表） |
| **graph_delta_note** | 候选修复面收敛于 app/main.py 行序或新增 app/ops 内 logging 工具模块；方向 B 若落地须 30 判 G-L2 indexes 是否收录新符号并回写 |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 无 coding_wiki 条目变更；行为真值在本 task + 上游 CLOSE 档 `docs/tasks/close/close_repo_logging_init_20261011.md` |
| **review_hat** | `20` |
| **required_invoke_hats** | `10,20,30,40` |
| **invoke_retention_profile** | `default` |
| **experience_capture** | `required` |
| **kpi_aggregator** | `CLOSE` |
| **orchestration** | 10 落稿 → 20 R1 → 维护者签 → 30（红测先行 · 方案裁定留痕）→ 40 → PR+CI 绿 → CLOSE |
| **freeze_id** | 无（零新表/零迁移/零新 SSE 事件/零新 env） |
| **close_pr_policy** | `required` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 22-R1, 30 | 初稿人扫 · 00 代录（授权 m00106 · 2026-10-11） |
| HG-AUDIT-R1 | approved | 30 | R1 PASS-WITH-NITS（docs/harness/reviews/task_n40_1_log_init_window_audit_R1_20261011.md · NIT×4 随 30 回填 · 窗口发射点全集实证闭合）· 00 代录（授权 m00106） |
| HG-GRAPH-MODULES | approved | 30 | 图谱预判 n/a 按实判复核通过 · 方向 B 落地触发 G-L2 同步义务+回填代录在案 · 00 代录（授权 m00106） |

---

## 背景与目标

### 实证锚点（上游 CLOSE 照登 + 本棒亲读复核 · base 286d825 成立）

- **窗口存在**：`app/main.py:9-12` 的 app 包 import 链（`app.config` / `app.ops.hitl` / `app.ops.router` / `app.ops.tracing`）先于 `app/main.py:38` 的模块级 `_init_logging()` 调用（定义在 `app/main.py:18-35`）——import 链执行期间 root logger 无 handler。
- **窗口内确有发射**（传递链亲读钉实）：`app.ops.router` → `app/ops/lg_rag/multi/nodes.py:36-39` / `app/ops/admin/capability.py:28` 等 `from app.ops.capability import ...` 触发 `app/ops/capability/__init__.py` 模块级 `:112 configure_persistence_from_env()` → `app/ops/capability/persistence.py:65-68` `logger.warning("能力层持久化未配置（%s 未设）…")` 在窗口内发射。
- **后果二态**（40 核验实证照登）：
  1. WARNING+ 走 `logging.lastResort` **裸格式**——启动日志首行「能力层持久化未配置（OPS_CAPABILITY_PERSISTENCE 未设）…」无 asctime/name/level，与钉死格式 `%(asctime)s %(name)s %(levelname)s %(message)s`（`app/main.py:14`）不一；
  2. 窗口内 INFO 级**整行被吞**（lastResort 门槛 WARNING）——`OPS_CAPABILITY_PERSISTENCE=db` 时 `persistence.py:48` `logger.info("能力层持久化：db（跨实例防重 + 回执落库）")` 不可见。
- **nit 级定性**（承上游裁定存续）：验收三键（hitl_persist_guard_skip / delegation_approval_consumed / token_issued）均请求期发射，窗口外不受影响。

**目标**：首个 app 包 import 之前 root handler 已就位——窗口内既有 WARNING 发射以钉死格式落 stderr、db 模式 INFO 发射可见；`OPS_LOG_LEVEL` 语义 / 格式口径 / uvicorn logger 共存 / pytest·caplog 测试面全部零 diff。

### 候选修法（开放给 30 实证后定 · 起草不锁死）

- **方向 A · main.py 内行序上移**：`_init_logging()` 定义与模块级调用上移至 `app/main.py:9` 首个 app 包 import 之前（函数仅用 stdlib `logging`/`os`，无循环 import 风险）——最小面 · 零新模块。
- **方向 B · 抽 `app/ops/logging_config.py`**（上游 CLOSE §七 建议形态）：初始化函数抽离为独立模块，`app/main.py` 在首个业务 import 前调用；scripts/evals/自写启动器后续可选复用——可演进性最强，但引入新模块（图谱 G-L2 判定义务触发）。
- **不采纳方向 C（窗口发射点挪窝/延迟装配）**：改 `capability/__init__.py:112` 模块级装配时序属治标且动业务装配面 → 列入非范围。
- 倾向 A（最小面 · 窗口根因即行序），B 的可复用价值留 20 审/30 裁定。

## 钉死契约

1. **`OPS_LOG_LEVEL` 语义零 diff**：缺省/非法=INFO fail-closed · `.strip().upper()` 归一 · 非法值 ERROR 告警行存续（`app/main.py:27-35` 口径逐字不动）。
2. **格式钉死零 diff**：`%(asctime)s %(name)s %(levelname)s %(message)s`（`app/main.py:14`）——台账 grep 脚本（验收便签口径）零改。
3. **uvicorn logger 共存口径零 diff**：`uvicorn`/`uvicorn.access` propagate=False 自带 handler 不动；access log 不吞 · 同一事件不双行（承 repo-logging-init D4/TC4 实证存续）。
4. **幂等存续**：`basicConfig` 在 root 已有 handler 时天然 no-op（`--reload` supervisor 子进程重启 / 自写启动器 / scripts/evals/alembic 自含配置面零 diff）。
5. **pytest/caplog 测试面零 diff**：propagate 链不动；仓根 .env 经 `app/config.py:11` load_dotenv 渗入 pytest 全进程的环境事实不变（承前 CLOSE 钉案）。
6. **最小面**：改动收敛于 `app/main.py` 行序（方向 A）或 `app/main.py` + 新增 `app/ops/logging_config.py`（方向 B）；`app/ops/capability/__init__.py`、`persistence.py` 发射点字面零 diff；若 30 实证须动 → GATE_STOP 回 10/维护者裁定。
7. **零新依赖（stdlib only）· 零新 env · 零新表/迁移 · 零新 SSE 事件**。

## 范围

- **F1 窗口复现红测**：子进程 import 顺序探针（修复前红 · 修复后绿 · 注入式口径不赌时机）。
- **F2 修法裁定与实现**：方向 A/B 择一，30 invoke 留裁定依据（含图谱判定回写）。
- **F3 测试断言化**：TC1–TC3（窗口格式 / 窗口 INFO 可见 / OPS_LOG_LEVEL 回归组）。
- **F4 图谱判定回写**：预判 n/a 照实写；方向 B 落地则 G-L2 indexes 同步判定 + HG-GRAPH-MODULES 代录。
- **F5 invoke 留档**：10/20/30/40 按 required_invoke_hats 落 `docs/harness/invokes/by-task/n40-1-log-init-window/`。

## 非范围

- 窗口发射点本身的挪移/降级/延迟装配（`app/ops/capability/__init__.py:112` 等）——治标且动业务装配面。
- 结构化日志（JSON）/ 日志落盘轮转 / 分模块级别细配——承 repo-logging-init 非范围存续。
- scripts/evals/alembic 既有自含 logging 配置面。
- uvicorn logger 配置与 access log 行为。
- 最小面之外的任何业务码改动。

## 失败路径

| 触发条件 | 系统行为 | 可重试 | 用户可见 |
|----------|----------|--------|----------|
| HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 任一 pending 即 30 改码 | 执行 Agent **拒开工**（闸表 pending 不代签） | 是 | 须先 20 R1 + 维护者签 task 闸表 |
| 方向 B 新模块引入 app 包依赖致循环 import | `import app.main` 即 ImportError · CI 红 | 是 | 启动失败直见；收口=初始化仅 stdlib |
| 子进程探针环境敏感（sys.path[0] 指错码 / .env 渗入 · 承 CLOSE 偏差 4 教训） | 探针假绿/假红 | 是 | 须钉 `PYTHONPATH=$PWD` + 显式 env 复跑 |
| `--reload` supervisor 双 import 重复初始化 | `basicConfig` 幂等 no-op · 行为零 diff | 否 | 无 |
| 自写启动器先 basicConfig 再 import app.main 形态 | 既有 handler 存续 · 幂等零 diff | 否 | 无 |
| 修复后窗口外请求期台账回归 | TC4 pytest 基线对拍检出 | 是 | 全量红 diff 可归因判定 |

## 验收标准

- [ ] **TC1 窗口格式反转（核心验收 · 红测先行）**：`PYTHONPATH=$PWD` 裸 `python -c "import app.main"`（无自写启动器 · 显式清 `OPS_CAPABILITY_PERSISTENCE`）——stderr「能力层持久化未配置…」行修复前为裸格式（红）、修复后匹配钉死格式 `<asctime> app.ops.capability.persistence WARNING …`（绿）。
- [ ] **TC2 窗口 INFO 可见性**：同探针 `OPS_CAPABILITY_PERSISTENCE=db`（memory 模式同组可并）——stderr 含钉死格式 INFO 行「能力层持久化：db（跨实例防重 + 回执落库）」；修复前整行被吞（红）、修复后可见（绿）。
- [ ] **TC3 OPS_LOG_LEVEL 回归组**：非法值 BOGUS → INFO 回退 + 格式化 ERROR 告警行存续；DEBUG 生效；缺省 INFO——裸探针口径承 repo-logging-init TC1 四组存续。
- [ ] **TC4 工程面**：`pytest tests` 全量零新增红（master 基线 4 failed=capability_lookups×3+lg_rag_multi×1 环境性钉案照登 · 对拍口径承前 CLOSE）；ruff 触及路径零新增；graph-compile EXIT=0；`npx --yes spec-wave task lint-wiki-delta --target .` 通过；三闸 approved 后才 30。

## 依赖

- 上游 CLOSE：`docs/tasks/close/close_repo_logging_init_20261011.md`（§四 N-40-1 nit 原文 · §七 后续建议 1 修法候选 · 偏差 4 PYTHONPATH 坑位）。
- 40 核验留痕：`docs/harness/invokes/by-task/repo-logging-init/invoke_20261011_40_verify.md`（:77/:91 NIT 登记）。
- 上游 task 钉死契约：`docs/tasks/done/task_repo_logging_init.md` §4（55 处 getLogger 零 diff · uvicorn 共存 · caplog 面）。
- 交接档：`docs/harness/invokes/by-task/_prompts/PROMPT_00_spec-campaign-handoff_20261011.md` §2.2 第 2 项。
- 编码规范：`docs/standards/CODING_BACKEND_L2_v1_zh.md`（L2_backend bar）。

## 给执行帽的必读列表

1. `docs/tasks/close/close_repo_logging_init_20261011.md` §四 N-40-1 + §七 1 + 偏差 4（PYTHONPATH/sys.path 坑位 · 探针纪律）。
2. `app/main.py` 全文（:9-12 import 链 · :14-15 常量 · :18-35 `_init_logging` 定义 · :38 模块级调用 · :41-54 lifespan）。
3. `app/ops/capability/__init__.py` :106-112（模块级装配四调用 · :112 为窗口发射源触发点）。
4. `app/ops/capability/persistence.py` :31-69（`configure_persistence_from_env` · 窗口发射三行 :48/:54/:65-68）。
5. `docs/tasks/done/task_repo_logging_init.md` §4 钉死契约 + §5 TC 口径（uvicorn 共存 / caplog / 台账键零改）。
6. `docs/standards/CODING_BACKEND_L2_v1_zh.md`。

## 思考轮控制

| 轮 | 结论 | early_stop | reason（early_stop） | residual_risks |
|---|---|---|---|---|
| R0 | 问题框定：import 链（main.py:9-12）先于 _init_logging()（:38）→ 窗口内 WARNING 走 lastResort 裸格式 · INFO 被吞 · nit 级 | false | — | 窗口内发射点全集是否仅此一处 |
| R1 | 证据收集：上游 CLOSE/40 invoke 逐字 + main.py/capability 传递链亲读 → 窗口发射源钉实为 capability/__init__.py:112 模块级装配 → persistence.py 三行 | false | — | 其余 import 链分支是否有第二发射点未全量排查 |
| R2 | 方案生成：A main.py 行序上移（最小面）/ B 抽 logging_config.py（可复用 · CLOSE 建议形态）/ C 发射点挪窝（治标 · 否决入非范围） | false | — | A/B 取舍未裁定（刻意留 20/30） |
| R3 | 反例/边界：OPS_LOG_LEVEL 语义与格式零 diff · uvicorn 共存不双行 · basicConfig 幂等（--reload/自写启动器）· caplog 面不动 · 方向 B 循环 import 红线 | false | — | 探针环境敏感性（PYTHONPATH/.env） |
| R4 | 收敛：最小面锁 app/main.py（± 新模块 logging_config.py）· capability 发射点字面零 diff · 图谱预判 n/a 照实写（B 落地触发 G-L2 判定） | false | — | 方向 B 的图谱回写义务为条件触发 |
| R5 | 收口：TC1–TC4 验收口径（TC1 窗口格式反转为核心 · 红测先行）+ failure_paths + 三闸 pending 不代签 | true | 范围/非范围/验收/failure_paths/锚点齐备 · 方案开放性显式留 20/30 · 再轮无新增信息 | 窗口发射点全集排查与 A/B 裁定留 30 |

**actual_last_round**：R5（early_stop）

### R0 · 问题框定

repo-logging-init 40 核验 N-40-1：`app/main.py:9-12` app 包 import 链先于 `:38 _init_logging()`，窗口内 logging 走 lastResort——WARNING+ 裸格式（启动首行实证无 asctime/name/level）、INFO 被吞（db 模式 persistence.py:48 情形）；验收三键请求期发射不受影响 → nit 级。上游 CLOSE §七 1 把「初始化挪 import 链之前」留本 task 裁定。本 task = 该 nit 的收口（bugfix 性质 · 无需新 SPEC）。

### R1 · 证据收集

逐字实读：CLOSE 档 §四 N-40-1 原文与 §七 建议 1、40 invoke :77/:91 NIT 登记、上游 task 钉死契约 §4；亲读复核（base 286d825）：`app/main.py` 全文 77 行（import 链 :9-12 · 常量 :14-15 · `_init_logging` :18-35 · 调用 :38）；传递链 `app/ops/capability/__init__.py:112` 模块级 `configure_persistence_from_env()` → `persistence.py:48/:54/:65-68` 三行发射——窗口内确有 WARNING 发射点（实证首行即此）。lastResort 机理：root 无 handler 时 WARNING 门槛裸格式输出，INFO 静默丢弃。

### R2 · 方案生成

候选三方向：A · `app/main.py` 内 `_init_logging` 定义+调用上移至首个 app 包 import 前（函数纯 stdlib · 零新模块 · 最小面）；B · 抽 `app/ops/logging_config.py`（上游 CLOSE 建议形态 · scripts/evals/自写启动器可复用 · 代价=新模块+图谱 G-L2 判定义务）；C · 窗口发射点挪窝/延迟装配（治标且动业务装配面 · 否决入非范围）。倾向 A，B 的复用价值留 20 审/30 裁定，起草不锁死。

### R3 · 反例与边界

- OPS_LOG_LEVEL fail-closed 语义与非法值 ERROR 告警行逐字存续（钉死契约 1）；格式常量 :14 不动（钉死契约 2）。
- uvicorn 共存口径不回归：access 不吞不双行（承上游 TC4 4 请求 4 行实证）。
- `--reload` supervisor 子进程双 import：basicConfig 幂等 no-op 存续（钉死契约 4）。
- 自写启动器先 basicConfig 形态：root 已有 handler → 本 task 初始化 no-op 零 diff。
- 方向 B 红线：新模块若 import 任何 app 包即循环 import——收口=初始化仅 stdlib（failure_paths 第 2 行）。
- 探针纪律：承 CLOSE 偏差 4（sys.path[0] 指错码 + 主仓 .env 渗入）——TC 探针钉 `PYTHONPATH=$PWD` + 显式 env。

### R4 · 收敛

最小面锁 `app/main.py` 行序（方向 A）或 `app/main.py` + 新增 `app/ops/logging_config.py`（方向 B）；`capability/__init__.py`/`persistence.py` 发射点字面零 diff，实证须动则 GATE_STOP 回 10/维护者。图谱照实预判 n/a；方向 B 落地触发 G-L2 indexes 同步判定 + HG-GRAPH-MODULES 代录（条件义务写入元信息与闸表说明）。验收口径 TC1–TC4：窗口格式反转为核心验收（红测先行 · 修复前裸格式红、修复后钉死格式绿）。

### R5 · 收口

范围 F1–F5、非范围五条、失败路径六行（闸行+五条技术路径）、验收四条勾选、必读六项齐备；三人工闸 pending 不代签；思考轮控制表 R0–R5 落盘。裁定收口，early_stop at R5。

### 自检结论（执行者）

- **30（2026-10-11）**：裁定**方向 A**（main.py 行序上移 · 根因即行序 · 最小面 · B 的复用价值当前无消费者反触发 G-L2 义务）——红测先行 RED 5 红实证（窗口 WARNING 裸格式 / db INFO 被吞）→ GREEN（tests/test_log_init_window.py 7 例 + 上游 test_logging_init.py 3 例全绿）；TC4 全绿（pytest 对拍零新增归因红 4 环境性钉案 · ruff 触及路径净 · graph-compile EXIT=0 · lint-wiki-delta@3.0.1 PASS）；capability 发射点字面零 diff；图谱 n/a 照实成立（A 零新模块）。详见 docs/harness/invokes/by-task/n40-1-log-init-window/invoke_20261011_30_implementation.md。R1 NIT×4 已回填闭合（N-1 四处计全断言化 · N-2 门控面登记 · N-3 钉版执行 · N-4 memory 口径）。
- （40 回填）

---

### KPI（00）

（`kpi_aggregator: CLOSE` · 关账回溯填写）

---

### 经验总结

（`experience_capture: required` · 关账必填）

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | 10 落稿（worktree `t-n40-1-log-init-window` · base master `286d825`）：交接档 §2.2 序2 逐字承接 · CLOSE N-40-1 nit 原文与 §七 修法候选照登 · 传递链亲读钉实（main.py:9-12 先于 :38 · capability/__init__.py:112 模块级装配为窗口发射源 · persistence.py:48/:65-68 两态后果）· 候选 A/B 开放不锁死（C 否决入非范围）· 钉死契约 7 · TC1–TC4（TC1 窗口格式反转红测先行为核心）· 图谱预判 n/a（方向 B 条件触发 G-L2 义务）· 三闸 pending 不代签 |
| 2026-10-11 | 三闸 approved（**00 代录 · 授权 m00106**）：HG-TASK-DRAFT · HG-AUDIT-R1（R1 PASS-WITH-NITS · 审查文址A 在案 · NIT×4 随 30 回填）· HG-GRAPH-MODULES（n/a 复核通过 · 方向 B 条件义务在案）→ 30 解锁 |
| 2026-10-11 | 30 实施：方向 A 裁定落地（app/main.py +10/-5 行序上移 · capability 发射点零 diff · 图谱 n/a 照实）· 红测先行 RED(5)→GREEN(7+3) · TC1–TC4 全绿（pytest 对拍零新增归因红 · ruff 触及路径净 · graph-compile EXIT=0 · lint-wiki-delta@3.0.1 PASS）· R1 NIT×4 回填闭合 · 30 invoke 落盘 |
| 2026-10-17 | CLOSED：PR #239 MERGED（squash `9c07ab4` · 2026-10-11）· 归档 done/ · CLOSE 档 `../close/close_n40_1_log_init_window_20261017.md` · 批量关账 PR 待开（close/active-batch-20261017）· 分支 `task/n40-1-log-init-window` 移交 00 统一清理 |
