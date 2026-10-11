# n40-1-log-init-window 审查（R1 · 20-task-audit）

> **审查对象**：`docs/tasks/active/task_n40_1_log_init_window.md`（commit 17bfaf8 · logging 初始化窗口收口 · 序2 repo-logging-init CLOSE N-40-1 nit 落地 · 10 落稿）
> **审查帽**：20-task-audit（R1 书面审查 · 未改 task 实质内容 · 未代签任何 human_gate · 未执行 30 · 未切分支）
> **日期**：2026-10-11 · **审查时仓态**：worktree `t-n40-1-log-init-window` · 分支 `task/n40-1-log-init-window`（base master `286d825` · task 文档 commit 17bfaf8 在 HEAD · docs-only · 码面与 base 同一）
> **委托令**：20 R1 审查棒——对照 CLOSE N-40-1 原文与 §七 建议 · 代码锚点亲读复核 · TC1–TC4 可机断性（TC1 子进程探针红测先行为核心）· failure_paths 四列表 · 思考轮 R0–R5 · 闸表契约 · graph_change_layer=n/a 条件触发自洽 · 10 棒留要点逐条（A/B 开放性 · 窗口发射点全集排查 · 探针 PYTHONPATH 纪律）

## 结论

**裁定：PASS-WITH-NITS**——本帽书面审查裁定 task 内容可执行、验收可机断 · 零内容阻塞 · 锚点 8 组全亲读核真（行号/格式串/logger 名逐字在案）· TC1/TC2 红前提本帽子进程探针实证成立（修复前裸格式红 · db 模式 INFO 被吞）· 窗口发射点全集本棒亲跑闭合（默认 env 仅 persistence 一处 · 另两枚 env 门控发射点登记 N-2，修法发射点无关全覆盖）· A/B 开放姿态得当 · 非阻塞观察项 N-1~N-4 列明于 §六 · 三流程闸全 pending 待维护者签（本帽未代签）。

| 维度 | 结论 |
|------|------|
| task **内容**可执行 | ✅ **PASS-WITH-NITS**——依据三源（交接档 §2.2 序2 · CLOSE §四 N-40-1/§七 1 · 40 invoke NIT 登记）逐字核真；目标与钉死契约 7 条可机验；候选 A/B 开放留 30 裁定姿态正确 |
| **流程闸** HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES | 全 `pending`（照实 · 本审查文落盘即 HG-AUDIT-R1 前置交付 · 维护者签 task 闸表后方 approved · blocks 30） |
| draft 洁净度 | ✓ 分支仅 17bfaf8 一个 task 文档 commit · 工作树无提前实施（本帽仅落审查文与 20 invoke） |

---

## 一、锚点逐一亲读核真（全亲读 · 如实）

| 锚点（task 声称） | 本帽亲读实证 |
|---|---|
| `app/main.py:9-12` import 链先于 `:38` `_init_logging()`（定义 :18-35 · 格式常量 :14） | ✅ 逐行亲读全文 77 行：:9-12 `app.config`/`app.ops.hitl`/`app.ops.router`/`app.ops.tracing` 四链 · :14 `%(asctime)s %(name)s %(levelname)s %(message)s` 逐字 · :18-35 定义纯 stdlib（logging/os · 零 app 包依赖 · 方向 A 无循环 import 风险成立）· :38 模块级调用 |
| `app/ops/capability/__init__.py:112` 模块级 `configure_persistence_from_env()` | ✅ :106-112 模块级装配四调用逐行在案（ensure_default_capabilities / register_mcp_client_if_enabled / load_extra_manifests_from_env / configure_persistence_from_env）· :112 逐字 |
| `persistence.py:48` INFO（db）/ `:65-68` WARNING（null 默认） | ✅ 逐字核真 · logger 名 `app.ops.capability.persistence`（:22 `getLogger(__name__)`）与 TC1 绿断言口径吻合；**另 :54 WARNING（memory）· :60-64 ERROR（非法值）同在窗内**——task 必读 4 称「三行」漏计 :60-64，记 N-1 |
| CLOSE §四 N-40-1 原文（`docs/tasks/close/close_repo_logging_init_20261011.md:51`） | ✅ 逐字对照：task 背景「窗口存在/窗口内确有发射/后果二态/nit 级定性」四面照登无走样；「验收三键请求期发射不受影响 → nit 级」存续理由成立 |
| CLOSE §七 后续建议 1（:83） | ✅ 逐字：「初始化挪 import 链之前（如抽 app/ops/logging_config.py）」——task 方向 B 逐字承接该建议形态 · 方向 A 为其最小面变体 · 承接忠实 |
| 交接档 §2.2 序2（PROMPT_00_spec-campaign-handoff_20261011.md:45） | ✅ 逐字在案：「app/main.py:9-12 import 链先于 :38 _init_logging() 窗口（WARNING+ 走 lastResort 裸格式 / INFO 被吞 · nit 级）」 |
| 偏差 4 PYTHONPATH 坑位（CLOSE :58） | ✅ task 吸收到位：TC1 钉 `PYTHONPATH=$PWD` + 显式清 env · failure_paths 第 3 行「探针假绿/假红」对口 |
| TC4 pytest 基线 4 failed（capability_lookups×3+lg_rag_multi×1） | ✅ 与 CLOSE §二/§五 反回归基线逐名吻合（主仓 master 带 .env 环境性钉案）· 对拍口径承前 CLOSE 成立 |

## 二、子进程探针实证（本帽亲跑 · base 码面 · PYTHONPATH=$PWD · 主仓 venv python）

| 探针 | 结果 | 对应验收 |
|---|---|---|
| 显式清 `OPS_CAPABILITY_PERSISTENCE` 裸 `python -c "import app.main"` | stderr 仅一行裸格式「能力层持久化未配置（OPS_CAPABILITY_PERSISTENCE 未设）…」（无 asctime/name/level）· EXIT=0 | **TC1 红前提成立**（修复前裸格式红） |
| `OPS_CAPABILITY_PERSISTENCE=db` 同探针 | stderr **空** · EXIT=0（DbIdempotencyStore 构造不连库 · 探针无需真 DB · 可行性实证） | **TC2 红前提成立**（INFO 整行被吞） |
| `OPS_CAPABILITY_PERSISTENCE=memory` | 裸格式 WARNING「能力层持久化：memory（进程内）…」（persistence.py:54） | TC2 memory 子组红前提成立（注意该组断言对象为 WARNING 非 INFO · 记 N-4） |
| `OPS_LOG_LEVEL=BOGUS` | 窗内裸 WARNING 照发 + `_init_logging` 后格式化 ERROR 告警行存续（`app.main ERROR OPS_LOG_LEVEL='BOGUS'…`） | TC3 前提成立 |
| **全集排查**：root+lastResort 降至 DEBUG 后复跑 unset/db 两探针 | 窗内发射**仅** persistence 一处 · app/ 全仓 grep 零裸模块级 `logger.*` 调用 | 10 棒留要点 2 闭合（默认 env 面无第二发射点） |
| `OPS_CAPABILITY_EXTRA_MANIFESTS=/nonexistent/x.yaml` | 窗内**第二枚 env 门控发射点实证**：manifest.py:218 裸格式 ERROR「manifest 加载失败（已跳过该文件）…」 | 登记 N-2（非默认面） |
| `OPS_CAPABILITY_REVERSIBILITY_MODE=enforce` | 无新增发射（builtin 清单能力全声明 reversibility · manifest.py:827/:840 理论可达当前不发射） | 登记 N-2（理论可达） |

## 三、10 棒留审要点逐条

1. **A/B 裁定倾向开放性** ✅——方向 A（main.py 行序上移）倾向理由「最小面 · 窗口根因即行序」成立（函数纯 stdlib · 亲读 :18-35 佐证）；方向 B（抽 `app/ops/logging_config.py`）逐字承接 CLOSE §七 建议形态、可复用价值留 20/30 裁定 · 起草不锁死；方向 C（发射点挪窝）否决入非范围且理由（治标 · 动业务装配面）成立。开放得当，无越断锁死。
2. **窗口发射点全集排查** ✅（本棒实证闭合，超 task 自证）——默认 env 面全集=persistence.py 一处（DEBUG 降门槛探针 + 全仓 grep 双重佐证）；另钉两枚 env 门控发射点（manifest.py:218 ERROR · :827/:840 WARNING）登记 N-2。**修法为发射点无关（初始化行序/抽模块前移）——全集是否完备不影响修复覆盖性**，R0/R1 residual「留 30 实证」姿态本可接受，本棒顺手闭合。
3. **探针 PYTHONPATH 纪律** ✅——TC1 钉 `PYTHONPATH=$PWD` + 显式清 `OPS_CAPABILITY_PERSISTENCE` · failure_paths 第 3 行对口偏差 4 · 本帽四组探针同纪律复跑全中，口径可复跑。

## 四、钉死契约与 TC1–TC4 可机断性

| 面 | 可机断性 |
|---|---|
| 钉死契约 1-7（OPS_LOG_LEVEL 语义 / 格式 / uvicorn 共存 / 幂等 / caplog 面 / 最小面 / 零新增） | ✅ 均可机验（探针断言 · git diff · grep 计数 · requirements diff 空）；契约 6「实证须动发射点 → GATE_STOP 回 10/维护者」兜底正确 |
| **TC1（核心 · 红测先行）** | ✅ 可机断——子进程探针命令显式 · 红（裸格式）/绿（`<asctime> app.ops.capability.persistence WARNING …` 正则）判据显式 · 红前提本帽实证成立 · logger 名核真（persistence.py:22） |
| TC2 | ✅ 可机断——db 模式 INFO 行有无即可断 · 本帽实证 db 探针无需真 DB（EXIT=0）；「memory 模式同组可并」措辞可收紧（memory 组断言对象为 :54 WARNING 格式化行 · 记 N-4） |
| TC3 | ✅ 可机断——BOGUS 回退 + ERROR 告警行存续本帽实证 · DEBUG/缺省组承 repo-logging-init TC1 裸探针口径 |
| TC4 | ✅ 可机断——pytest 基线对拍（4 红环境性钉案照登）· ruff 触及面 · graph-compile EXIT=0 · lint-wiki-delta；**惟命令未钉版**（`npx --yes spec-wave task lint-wiki-delta` 缺 `@3.0.1` · CI lint-wiki-delta.yml:35 与 package.json:6 均钉 3.0.1 · 承 CLOSE §七 3 钉法教训）· 记 N-3 |
| failure_paths（四列六行） | ✅ 契约合式（触发条件/系统行为/可重试/用户可见）· 闸行+循环 import+探针环境+reload 幂等+自写启动器+回归检出 六行覆盖完备 |
| 思考轮 R0–R5 | ✅ 控制表齐（轮/结论/early_stop/reason/residual_risks）· early_stop at R5 理由成立（范围/非范围/验收/锚点齐备 · 开放性显式留 20/30）· residual 两条本棒已实证闭合其一（发射点全集） |

## 五、图谱预判与闸表契约

- **graph_change_layer=n/a 条件触发自洽** ✅——预判 n/a 照实写 + 「方向 B 新增 `app/ops/logging_config.py` 则按实判升 G-L2 indexes（docs/_tech_graph/l2/indexes/）同步义务 + HG-GRAPH-MODULES 00 代录」条件句，与 repo-logging-init 先例（done task :14「图谱预判 n/a 照登 · 30 按实判回写义务」）同构；graph_delta/graph_delta_note 双字段口径一致，无自相矛盾。
- **闸表契约** ✅——4 列（human_gate_id/status/blocks_hats/说明）与 TASK_TEMPLATE:41 同构 · 三闸 status 纯 pending · 无代签 · HG-GRAPH-MODULES 说明「30 按实判回写义务触发时人签」读法与先例一致（闸签为 30 前置 · 回写义务为条件触发 · 二层不混）。

## 六、NIT 清单（非阻塞 · 照登 · 随 30 回填闭合）

- **N-1**：必读 4 与 R1 节称 persistence.py 窗口发射「三行 :48/:54/:65-68」——实为**四处**（:48 INFO db · :54 WARNING memory · **:60-64 ERROR 非法值** · :65-68 WARNING null）；非法 `OPS_CAPABILITY_PERSISTENCE` 值时 :60 ERROR + :65-68 WARNING 两行同窗裸发。建议 30 探针组顺手覆盖非法值子组或 invoke 留一行说明。
- **N-2**：窗内**第二、三枚 env 门控发射点**（本棒实证钉实）：`manifest.py:218` ERROR（`OPS_CAPABILITY_EXTRA_MANIFESTS` 指向坏文件即窗内裸发 · 本棒实证）· `manifest.py:827/:840` WARNING（`OPS_CAPABILITY_REVERSIBILITY_MODE=observe|enforce` + 能力未声明 reversibility · 当前 builtin 全声明故不发射）。修法发射点无关全覆盖 · 不阻塞；建议 30 invoke 留一行「全集已闭合 · 门控面登记」。
- **N-3**：TC4 lint-wiki-delta 命令未钉 `spec-wave@3.0.1`（CI/package.json 钉法在案 · CLOSE §七 3「一切 npx spec-wave 调用面统一钉版」教训）——30 执行以钉版形态为准。
- **N-4**：TC2「memory 模式同组可并」措辞——memory 组断言对象为 :54 WARNING 格式化行（非 INFO）；机断可行，30 invoke 断言口径写清即可。

---

## 维护者签闸（20 后 · 30 前）

- [ ] 已读 R1 审查结论
- [ ] 在 task 人工闸表将 HG-AUDIT-R1 改为 approved（维护者 · 日期）
- [ ] commit task 文档或确认已签
- [ ] 再下发 Harness 30 Prompt

30 Agent 将以 task 表为准；pending 时必须拒开工（见 TEMPLATE_30_gate_stop.md）。
