# CLOSE：repo-logging-init（2026-10-11）

> **task**：[`../done/task_repo_logging_init.md`](../done/task_repo_logging_init.md)（已归档 done/ · 状态行回填 CLOSED）
> **类型**：仓级基建（可观测性 · SPEC §9 序2 · 维护者令 2026-10-11 立项）
> **关账日期**：2026-10-11 · 帽位：CLOSE（50）

---

## 一 · 任务信息

| 字段 | 值 |
|---|---|
| **task_slug** | `repo-logging-init` |
| **目标** | 任意启动形态（裸 `uvicorn app.main:app` / 自写启动器 / docker compose）下 app INFO 台账开箱可见，三形态口径一致；既有测试面与 logger 调用点零 diff（task §2 逐字承接） |
| **依据三源** | `docs/spec/hitl-approval-consumption/SPEC-hitl-approval-consumption_v1.md` §9 序2（:264 题字「仓级 logging 初始化缺失」）· `close_hitl_auto_resume_claim_race_20261010.md` 第九节改进建议 #1 · `docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md` 操作便签坑位 1（:64 在案 · 维护者复跑亲撞） |
| **分支 / base** | `task/repo-logging-init`（base = master `cae745e`） |
| **PR / merge** | [#227](https://github.com/Cyning12/ops-desk-api/pull/227) · **MERGED · squash `e5b5c3d`**（2026-10-11 09:39 CST · CI 绿） |
| **帽链** | 10 落稿（`73b79e6` · 00 代笔 · 授权 m01606）→ 20 R1（骨架 `32f5d18` → 定稿 `2ffdd29`）→ 三闸代录（`a31d471`）→ 30 红测先行 `445ce28` → 实现 `b329aec` → 30 invoke+图谱回写 `ed69292` → 40 核验（`6bd4cec` → `268e46c` → `642a4d0`）→ 40 自检回填 `2a6ffe3` → CI 修复 `2d686f0`/`5e07040` → CLOSE（本档） |

## 二 · 交付清单

**码面与测试面**（squash diffstat：10 files · +428/-2）：

| 面 | 实证 |
|---|---|
| `app/main.py` +28 | import 期 `_init_logging()`（D1=**A** 裁定落地）：root 挂唯一 StreamHandler · `logging.basicConfig` 幂等天然；`OPS_LOG_LEVEL` 默认 INFO、非法值回退 INFO fail-closed + ERROR 台账（D2=**A** · 承 auto_resume.py:76 env 先例）；格式 `%(asctime)s %(name)s %(levelname)s %(message)s` 钉死（D3 · 验收文档 :139 逐字）；uvicorn logger 不动（D4 · propagate=False 自带 handler 不双行，承 R1 uvicorn 0.51.0 机理实证） |
| `tests/test_logging_init.py` +78 | TC1 红测先行三组（默认 INFO / OPS_LOG_LEVEL=DEBUG 覆盖 / BOGUS 非法回退）· 裸 python 子进程断言（N-3 口径 · 非 pytest 进程内防捕获 handler 误判） |
| 图谱回写 | `docs/_tech_graph/l1/01_modules.md:27` entry 行补 logging 初始化表述（图谱预判「若有涉台账表述须回写」按实判履行 · HG-GRAPH-MODULES 在册） |
| 文档面 | task 文档 76 行 + R1 审查文 78 行 + invokes 10/20/30/40 四件 + 40 自检回填 + `wiki_delta`/`wiki_delta_note` 元信息补登（`2d686f0`） |
| `scripts/graph-compile.sh` ±7 | GRAPH_CLI 默认钉 `spec-wave@3.0.1`（`5e07040` · 上游 3.2.0 发布漂移断 check/tech-graph · implementedBy schema 收紧 · 非本 diff 引入 · 对齐 package.json 与 lint-wiki-delta.yml 钉法 · 环境变量回退口保留） |

**钉死契约 5 条自查**（30 invoke 契约自查节全过）：55 处 `getLogger(__name__)` 既有调用点零 diff（计数 55→56 系 main.py 自身非法值告警新增 1 处 · 属「只加初始化」面）· 零新依赖 · pytest 零新增红（对拍口径）· TestClient/caplog 测试面零 diff · 台账键字面零改。scripts/evals/alembic 三面零 diff。

**反回归基线**：30 环境（worktree 无 .env + 主仓 venv）全量 1770 passed/1 failed（SILICONFLOW_API_KEY 缺失环境性 · base 对拍同红）；40 主仓 master 带 .env 全量 4 failed/1764 passed 与契约3 逐名吻合（capability_lookups×3+lg_rag_multi×1 环境性）· ruff 触及面零新增（全仓 55 errors 与 master 基线持平）· graph-compile EXIT=0。

## 三 · 核验结论

**40 核验裁定：PASS-WITH-NITS**（2026-10-11 02:10 · 独立复跑不采信 30 自报 · [40 invoke](../../harness/invokes/by-task/repo-logging-init/invoke_20261011_40_verify.md)）：

| 核验面 | 结论 | 证据 |
| --- | --- | --- |
| TC1 单测 | ✅ | 三组全绿（3 passed in 2.58s）；40 独立裸 import 探针四组全中：UNSET→INFO · DEBUG→DEBUG · debug 小写→DEBUG（.upper() 归一）· BOGUS→INFO 回退，HANDLERS=1 · 格式钉死逐字 |
| TC2 裸 uvicorn live（**核心验收 · 坑位1 反转**） | ✅ | after（`/tmp/tc2_after3.log`）：`app.ops.hitl.persistence` / `app.ops.rag.embedder` / `app.ops.lg_rag.multi.nodes` 等 INFO 行以钉死格式落 stderr；before wrapper（剥光 root handlers+回 WARNING 精确复制修复前运行态）：app.* 任意级行数=0、access 仍 3 → 同码同环境唯一变量=root handler 有无，反转成立 |
| TC3 compose 形态 | ✅ | `git diff cae745e -- docker-compose.yml`（及 scripts/ evals/ alembic/ requirements.txt）= 空；compose api 命令（docker-compose.yml:80）与裸 uvicorn 同 import 期初始化路径 → 机理等价照登 |
| TC4 access 单行 | ✅ | 精确计数补跑（:8023 · `/tmp/tc4b.log`）：4 请求 → access 行恰好 4 条，root handler 重格式化=0，双行=0（propagate=False 共存口径实证） |
| TC5 反回归 · master 基线对拍 | ✅ | 主仓 4 failed/1764 passed 逐名吻合契约3；同 env A/B 两侧同红 chat×8（source env 口径环境敏感 · 非本 diff 引入）；memory×4 瞬态复跑 4 passed 归因跑批与 live server 窗口叠加 → **零新增红可归因于本 task diff** |
| OPS_LOG_LEVEL live | ✅ | BOGUS live：启动即落格式化 ERROR 告警行且回退后 app INFO 仍可见；DEBUG live 无 DEBUG 发射点触达（口径说明非偏差 · env 生效以裸探针为权威） |

## 四 · 偏差与 nit

**N-40-1（import 窗口裸格式 · 照登）**：`app/main.py:9-12` 的 app 包 import 链先于 `:38` `_init_logging()`；该窗口内 logging 走 lastResort 裸格式（实证：启动日志首行「能力层持久化未配置（OPS_CAPABILITY_PERSISTENCE 未设）…」无 asctime/name/level）。WARNING+ 仍可见但格式不一；若该窗口存在 INFO 级发射（如 `OPS_CAPABILITY_PERSISTENCE=db` 时 `capability/persistence.py:48` 的「能力层持久化：db」）仍会被吞。验收三键均请求期发射不受影响 → **nit 级**，修法候选=初始化挪 import 链之前，留后续 task 裁定。

**偏差登记（40 invoke 环境口径节在案）**：

1. **端口偏差 8021→8022**：父令指定 8021 实测被 macOS launchd socket-activation 占用（pid 1 不可杀）→ 切 8022，口径不变。
2. **三键全链缺真 LLM key 照登**：`SILICONFLOW_API_KEY=dummy-probe` 下挂起→decide→resume 三键全链需真 LLM 规划不可及；机理面由 app.* INFO 行实证 + 验收文档 20261010 :60 先例（同 root handler 管道）覆盖。
3. **DEBUG live 无 DEBUG 发射点**：触达链无 logger.debug 发射点；asyncio selector DEBUG 行先于 app import 期 basicConfig 被吞——照登为口径说明，非偏差。
4. **脚本侧解析坑位**：`python scripts/create_initial_user.py` 的 sys.path[0]=scripts/ 致 import 落主仓 editable 码 + 主仓 .env → HMAC secret 不一致 login 401；解法=两侧统一 `PYTHONPATH=$PWD` + 显式 `OPS_DESK_SECRET`（承「venv editable 指错码」历史教训同族）。

**R1 N-1~N-6 闭合**：N-2 caplog 论证补足（root level 抬高副作用 · caplog propagate 链机理 + TC5 兜底实证）· N-3 TC1 裸子进程口径钉死 · N-4 TC2 复跑锚点钉行号（验收 :20 六 env · :64 坑位注 · :60 三键）· N-5 pytest 执行环境口径（worktree 无 .env · master 基线对拍 deferred 40 完成）· N-6 --reload 论证覆盖（supervisor 子进程重启 + basicConfig 幂等）。

**仓级 verify 基线**：仓级 `npx spec-wave verify` EXIT=2 BLOCKED（done/ 遗留档 reviews 缺口 · 仓级基线 · 主仓同 · 承前两 CLOSE 钉案）——照登不新增；本 CLOSE 实测见 §九附录。

## 五 · 签录

| 环节 | 文档 / 实证 |
|------|------|
| 10 落稿 | `73b79e6` · [10 invoke](../../harness/invokes/by-task/repo-logging-init/invoke_20261011_10_task_draft.md)（00 代笔 · 首棒长读卡滞 interrupt 留痕 · 授权 m01606） |
| 20 R1 审查 | [`docs/audits/task-review/20261011_repo-logging-init_r1.md`](../../audits/task-review/20261011_repo-logging-init_r1.md)（**PASS-WITH-NITS** · 零内容阻塞 · 锚点 12 组全亲读核真 · N-1~N-6 非阻塞随 30 回填闭合） |
| 人工闸 | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 **approved**（维护者授权 · 00 代录 2026-10-11 · `a31d471` · 授权 m01606）· HG-PILOT-OPSDESK-GLAYER n/a（纯 app/ 内基建 · 无图谱物理分层面） |
| 30 实现 | `445ce28` 红测先行（3 红在案）→ `b329aec` feat 实现 → `ed69292` [30 invoke](../../harness/invokes/by-task/repo-logging-init/invoke_20261011_30_implement.md) + 图谱 :27 回写 |
| 40 核验 | `6bd4cec`/`268e46c`/`642a4d0` [40 invoke](../../harness/invokes/by-task/repo-logging-init/invoke_20261011_40_verify.md) · 自检回填 `2a6ffe3` · 裁定 **PASS-WITH-NITS** |
| CI 修复 | `2d686f0`（lint-wiki-delta 红：Harness 元信息补 `wiki_delta`/`wiki_delta_note` · 值 `n/a` 按规约形态）· `5e07040`（graph-compile GRAPH_CLI 钉 spec-wave@3.0.1） |
| invokes | [`docs/harness/invokes/by-task/repo-logging-init/`](../../harness/invokes/by-task/repo-logging-init/)（10 落稿 / 20 审查 / 30 实现 / 40 核验 / 50 收口） |

## 六 · 资源清理

- **本 CLOSE 不删任何东西**（父令明示）：worktree `t-repo-logging-init` 与分支 `task/repo-logging-init`（已 merge）、`close/repo-logging-init` 均保留，**移交 00 统一清理**。
- 归档动作：task 档 `docs/tasks/active/` → `docs/tasks/done/`（`git mv` 保留全文 · 状态行回填 CLOSED+日期 · 修订记录追 CLOSE 行）；`docs/tasks/active/README.md` 登记表补行（active 目录无在途 task）；`docs/tasks/done/README.md` Hub 表行 + 修订记录行补登；CLOSE 文档与 50 invoke 落盘。

## 七 · 后续建议

1. **N-40-1 修法候选（建议后续 task 裁定）**：把 logging 初始化挪至 `app/main.py:9-12` app 包 import 链之前（如抽 `app/ops/logging_config.py` 于首个 app 包 import 前执行），消除 lastResort 裸格式窗口与窗口内 INFO 吞失风险。
2. **仓级 verify 缺口清零**（承前两 CLOSE 钉案 · 第三次照登）：done/ 遗留档 reviews 缺口属仓级卫生项，建议另立 chore task 批量补登或在 verify 配置标 baseline——每 task CLOSE 重复「仓级基线照登」信噪比递减。
3. **spec-wave 版本钉法推广**：3.2.0 发布漂移断 check/tech-graph 实证（`5e07040` · implementedBy schema 收紧）——建议仓内一切 npx spec-wave 调用面统一钉版（graph-compile.sh 已钉 3.0.1 · package.json 与 lint-wiki-delta.yml 同钉法），verify 自报须附 REAL_EXIT 取证（承 CLOSE hitl-replan-carry-and-persist-guard 学习要点 3）。

## 八 · 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-11 | CLOSE 落稿（九节：任务信息/交付清单/核验结论/偏差与 nit/签录/资源清理/后续建议/修订记录/附录 · PR #227 squash `e5b5c3d` 已 merge · 归档 done/ · 双侧 README 补登 · 50 invoke 落盘） |

## 九 · 附录

**PR / merge 事实**：PR [#227](https://github.com/Cyning12/ops-desk-api/pull/227) MERGED 2026-10-11T01:39:30Z（09:39 CST）· squash commit `e5b5c3dc5f874c344fc649eaf971967f838650a4` · base master / head task/repo-logging-init。

**交付 commit 链（13 枚 · 按序）**：`73b79e6`（10 落稿）→ `32f5d18`（R1 骨架）→ `2ffdd29`（R1 定稿）→ `a31d471`（三闸代录）→ `445ce28`（TC1 红测先行 3 红）→ `b329aec`（feat 实现）→ `ed69292`（30 invoke+图谱回写）→ `6bd4cec`（40 骨架）→ `268e46c`（40 增量 TC4+DEBUG）→ `642a4d0`（40 终稿）→ `2a6ffe3`（40 自检回填）→ `2d686f0`（CI 修复 wiki_delta 元信息）→ `5e07040`（CI 修复 graph-compile 钉版）。

**关键路径指针**：task 档 `docs/tasks/done/task_repo_logging_init.md` · R1 `docs/audits/task-review/20261011_repo-logging-init_r1.md` · invokes `docs/harness/invokes/by-task/repo-logging-init/` · 实现 `app/main.py`（`:9-12` import 链 / `:38` `_init_logging()`）· 测试 `tests/test_logging_init.py` · 图谱 `docs/_tech_graph/l1/01_modules.md:27`。

**CLOSE 机械闸复跑（本棒实测 · REAL_EXIT 取证）**：spec-wave task lint 与 verify（npx spec-wave@3.2.0）结果见 50 invoke「质量钉」节如实登记。
