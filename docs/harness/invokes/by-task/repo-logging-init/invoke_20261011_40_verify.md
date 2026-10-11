---
hat: 40
task_slug: repo-logging-init
date: 2026-10-11
---

# invoke · 40-verify · repo-logging-init（仓级 logging 初始化）

> 骨架先行 · 逐 TC 增量回填。核验对象：b329aec feat app/main.py import 期 basicConfig + 445ce28 TC1 红测 + ed69292 30 invoke/图谱回写。

## 环境口径与偏差登记（先行）

- **worktree 无 .env**（N-5 承 30）：live server = 主仓 venv python（pytest 8.4.2 · uvicorn 0.51.0）+ cwd=worktree → `python -c` sys.path[0]='' 解析本 worktree 码，启动自证 `CODE_UNDER_TEST=…/ops-desk-api-worktrees/t-repo-logging-init/app/main.py`。
- **坑位（脚本侧解析）**：`python scripts/create_initial_user.py` 的 sys.path[0]=scripts/，import app 落到主仓 editable 码并加载主仓 .env → OPS_DESK_SECRET=change-me-in-production；而 `python -c` 起的 server 用 worktree 码、默认 secret=change-me → HMAC hash 不一致 → login 401「Invalid or expired invite token」。**解法**：两侧统一 `PYTHONPATH=$PWD` + 显式 `OPS_DESK_SECRET=tc2-40verify-secret`（env 优先于 .env）。承验收文档「venv editable 指错码」历史教训同族。
- **端口偏差**：父令指定 8021，实测被 macOS launchd socket-activation 占用（tcp4+tcp6 LISTEN · pid 1 · 不可杀）→ 切 **8022**，口径不变。
- LLM key = `SILICONFLOW_API_KEY=dummy-probe`（父令口径）：挂起→decide→resume 三键全链需真 LLM 规划，本环境不可及 → **三键全链照登为偏差**，机理面由 app.* INFO 行实证 + 验收文档 20261010 :60 先例（同 root handler 管道）覆盖。
- 六 env 组照验收文档 :20 逐字；另剥 proxy/no_proxy 全大小写（no_proxy 含 [::1] 会致 httpx URLPattern InvalidURL ':1]'，干扰 LLM 调用面，与台账核验无关但污染日志判读）。

## TC1 单测（30 已绿 · 40 复核）

- tests/test_logging_init.py 三组（默认 INFO / DEBUG 覆盖 / BOGUS 回退）系裸 python 子进程断言。40 复跑随 TC5 全量一并核。
- 40 独立裸 import 探针（非 pytest）实证：
  - UNSET → ROOT_LEVEL=INFO · HANDLERS=1 · FMT=['%(asctime)s %(name)s %(levelname)s %(message)s']
  - OPS_LOG_LEVEL=DEBUG → ROOT_LEVEL=DEBUG · HANDLERS=1 · 格式同上
  - OPS_LOG_LEVEL=debug（小写）→ ROOT_LEVEL=DEBUG（.upper() 归一 ✓）
  - OPS_LOG_LEVEL=BOGUS → ROOT_LEVEL=INFO · HANDLERS=1（fail-closed ✓）

## TC2 裸 uvicorn live（核心验收 · 坑位1 反转）

### 修复后（after）

起法：`python -c "import uvicorn; uvicorn.run('app.main:app', port=8022)"`（父令口径 · 六 env 组 + dummy key）。实证链：

- 登录 200 → `GET /api/ops/hitl/runtime` 200 `{"mode":"db","store":"DbHitlStore","persists":true,...}`
- **app.* INFO 行以钉死格式落 stderr**（/tmp/tc2_after3.log）：
  - `2026-10-11 01:53:58,566 app.ops.hitl.persistence INFO HITL 持久化：db（审批申请跨实例、跨重启可查）`
  - `2026-10-11 01:53:58,666 app.ops.rag.embedder INFO query embedder backend=siliconflow model=BAAI/bge-m3`
  - app.ops.strategy.intent / app.ops.lg_rag.nodes / **app.ops.lg_rag.multi.nodes**（父令例举命名空间）/ app.ops.lg_rag.answer_stream / app.ops.lg_rag.sse_stream 各级行同格式可见（WARNING/ERROR 为 dummy key 下 LLM 不可达的预期失败面，非本 task 红）
- ✅ 结论：裸 uvicorn 下 app 模块 INFO 台账开箱可见，格式='%(asctime)s %(name)s %(levelname)s %(message)s' 逐字。

### 修复前模拟（before · 坑位1 复现）

同起法外套 wrapper：import app.main 后剥光 root handlers + root level 回 WARNING（精确复制修复前运行态：root 无 handler · WARNING）。同打 login+runtime：

- app.* 任意级命名行数 = **0**（'HITL 持久化：db' INFO 消失 · grep 空）——坑位1「裸 uvicorn 吞 app INFO」精确复现
- uvicorn access 行仍 3（health+login+runtime）——修复前 access 不吞、独吞 app INFO 的机理面吻合
- ✅ 反转成立：同码同环境唯一变量=root handler 有无，before grep 空 / after 可见。

## TC3 compose 形态

- `git diff cae745e -- docker-compose.yml` = **空**（scripts/ evals/ alembic/ requirements.txt 同空；本 task diff 仅 app/main.py +28、tests/test_logging_init.py、docs 三面）。
- compose api 命令=`uvicorn app.main:app`（docker-compose.yml:80），与 TC2 裸 uvicorn 同一 import 期初始化路径 → 机理等价（初始化在 app/main.py import 期，与启动形态无关）。compose build/run live 复跑承父令「零 compose diff 照登即可」不重复执行 → 照登。

## TC4 access 单行（共存口径）

- after run 观察：uvicorn.access 保持自带格式 `INFO:     127.0.0.1:57362 - "GET /health HTTP/1.1" 200 OK`（propagate=False 自带 handler · 未被本 task root handler 重格式化 · 未双行）。
- 精确计数补跑（:8023 · /tmp/tc4b.log）：就绪探测 1 + 显式 3 = **4 请求 → access 行恰好 4 条**（`INFO:     127.0.0.1:57xxx - "GET /health HTTP/1.1" 200 OK` ×4，端口 57883-57886 逐一对应）；root handler 重格式化迹象（钉死格式的 uvicorn 行）= **0**；双行 = **0**。
- ✅ 结论：propagate=False 共存口径成立——每请求恰好一条 access 行，自带格式不被 root handler 截获重发。

## TC5 反回归 · master 基线对拍

- **主仓 master@cae745e 带 .env 全量 pytest**：`4 failed, 1764 passed, 1 skipped in 56.93s`
  - 红集逐名：tests/test_capability_lookups.py::test_tool_exec_lookup_ainvoke_and_error_continues / ::test_tool_exec_prefers_args_over_input_no_db / ::test_tool_exec_prefers_args_over_input + tests/test_lg_rag_multi.py::test_unknown_tool_at_invoke_recorded_and_continues
  - 与 task 契约3「本地 4 红=master 基线环境性（capability_lookups×3+lg_rag_multi×1）」逐名吻合 ✅
- **下半（worktree 码 + 主仓 .env set -a source 全量 pytest · job bash-876）**：`16 failed, 1755 passed, 1 skipped in 64.71s`。红集=基线 4 + chat_service×5 + chat_ws×3 + memory×4（memory_purge_db×3 + memory_service_db×1）。
- **A/B 归因（同 env 主仓复跑 · job bash-935）**：主仓 master + 同一 source env → `12 failed, 1756 passed`，红集=基线 4 + **同一 chat×8**（test_chat_service TestRunChatStream×5 + test_chat_ws×3）→ chat×8 系 source env 口径（set -a 导出 vs load_dotenv）的环境敏感面，两侧完全同红，非本 task diff 引入。
- **memory×4 复跑归因**：worktree 同 env 单点复跑 4 条 → `4 passed in 6.24s` → bash-876 的 memory 红系跑批与 40 并行 live server 窗口（8023/8024/8025 起停 + create_initial_user 写库）叠加的瞬态，非码因。
- ✅ 结论：**零新增红可归因于本 task diff**（对拍两侧同 env 同红；瞬态红复跑即绿）。

## OPS_LOG_LEVEL live 组（父令第 5 项）

- BOGUS live：启动即落格式化错误行 `2026-10-11 01:55:33,507 app.main ERROR OPS_LOG_LEVEL='BOGUS' 无法识别（仅 CRITICAL/ERROR/WARNING/INFO/DEBUG），按 INFO 处理` ✅ fail-closed 告警可见
- DEBUG live（:8024 · /tmp/tc_debug2.log /tmp/tc_debug3.log 两轮）：login+runtime+pending 全链打下后 **DEBUG 级行数=0**。机理：触达链（auth/hitl/runtime/pending）无 logger.debug 发射点；asyncio selector 的 DEBUG 行发射于 loop 创建时（先于 app import 期的 basicConfig）被吞。app.* INFO 行同级管道仍正常可见 → env 生效的权威证据以 TC1 裸 import 探针为准（OPS_LOG_LEVEL=DEBUG → ROOT_LEVEL=DEBUG · HANDLERS=1 · 格式钉死），live 面无反证。照登为口径说明，非偏差。

## NIT 候选（随裁定回填）

- **N-40-1（import 窗口裸格式）**：app/main.py:9-12 的 app 包 import 链先于 :38 `_init_logging()`；该窗口内 logging 走 lastResort 裸格式（实证：启动日志首行 '能力层持久化未配置（OPS_CAPABILITY_PERSISTENCE 未设）…' 无 asctime/name/level）。WARNING+ 仍可见但格式不一；若该窗口存在 INFO 级发射（如 OPS_CAPABILITY_PERSISTENCE=db 时 capability/persistence.py:48 的 '能力层持久化：db'）仍会被吞。验收三键均请求期发射不受影响 → nit 级，修法候选=初始化挪 import 链之前（后续 task 裁定）。

## 裁定

**PASS-WITH-NITS**（2026-10-11 02:10 · 40-verify）

| 核验面 | 结论 | 证据 |
| --- | --- | --- |
| TC2 裸 uvicorn app INFO 可见（核心） | ✅ | after /tmp/tc2_after3.log：app.ops.hitl.persistence / app.ops.rag.embedder INFO 钉死格式落 stderr；before wrapper 复现 grep 空、access 仍 3 → 坑位1 反转成立 |
| TC3 compose 零 diff | ✅ | git diff cae745e -- docker-compose.yml（及 scripts/ evals/ alembic/ requirements.txt）= 空；compose 与裸 uvicorn 同 import 期初始化路径，照登 |
| TC4 access 不双行 | ✅ | /tmp/tc4b.log：4 请求→4 条 access 行，root handler 重格式化=0，双行=0 |
| TC5 master 基线对拍 | ✅ | 主仓 4 failed/1764 passed 与契约3 逐名吻合；同 env A/B 两侧同红（chat×8 环境敏感），memory×4 瞬态复跑全绿 → 零新增红归因本 diff |
| OPS_LOG_LEVEL live | ✅ | UNSET/DEBUG/debug/BOGUS 裸探针四组全中；BOGUS live 告警行格式化可见且回退后 app INFO 仍可见；DEBUG live 无发射点触达（口径说明非偏差） |

NIT：**N-40-1**（import 窗口裸格式，见上节）——app/main.py:9-12 import 链先于 :38 初始化，窗口内 WARNING+ 走 lastResort 裸格式、INFO 被吞；验收三键请求期发射不受影响，nit 级，留后续 task 裁定（修法候选：初始化挪 import 链之前）。

偏差登记：8021→8022（launchd 占用）；三键全链缺真 LLM key 照登；DEBUG live 无 DEBUG 发射点，env 生效以裸探针为权威。
