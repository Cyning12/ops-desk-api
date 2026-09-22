# invoke · 40 核验 · test-baseline-reds 测试基线红清理（30 交付 5a5db27）

> hat=40 · task=test-baseline-reds · 2026-09-22 · 分支 fix/test-baseline-reds（核验时 HEAD=5a5db27）
> 核验方式：全部亲跑真跑留证据 · 宿主 env 双态 · origin/master worktree 对照 · 变异复做

## 总判定：PASS（零阻塞 · A1–A6 全过 · 30 自称逐条属实）

## 一、全量 pytest（双态亲跑）

| 态 | 环境 | 结果 |
|----|------|------|
| 态① 宿主现状 | 宿主 shell 含 http(s)_proxy/all_proxy=127.0.0.1:7890 + no_proxy 含 `[::1]`；.env MEMORY_FACTS_ENABLED=true + MEMORY_FACTS_VECTOR_RECALL_ENABLED=true | **1367 passed / 1 skipped / 0 failed**（50.3s） |
| 态② 净 env（delenv 场景） | `env -u no_proxy -u NO_PROXY -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY` + `MEMORY_FACTS_VECTOR_RECALL_ENABLED=false`（覆盖 .env） | **1367 passed / 1 skipped / 0 failed**（23.1s） |
| 态① 复跑（A3② 第三连跑） | 同态① | **1367 passed / 1 skipped / 0 failed**（53.5s） |

两态皆绿 —— 双态核验通过。

## 二、前红→后绿对照（git worktree @ origin/master 2cb67c0 · 补同 .env · 双态）

| 缺陷 | master 宿主 env | master 净 env | fix 分支（双态） |
|------|----------------|---------------|------------------|
| D1 chat_ws | **2 failed / 4 passed**（与 10/R1 基线逐字一致） | 挂真网（embedder HTTP · 无打桩），超时未收敛 —— 佐证「修复方向即去除外部依赖」 | 6 passed ×2 态 |
| D2 proxy | **1 failed / 1 passed**（DID NOT RAISE · 与基线一致） | 2 passed（净 env 无 no_proxy 旁路条目 → 与「CI 绿」机理一致） | 2 passed ×2 态（打桩恒 False · 确定性） |
| D3 flaky | **3 failed / 10 连跑**（30% · 与 8/20、6/15 同量级 · 翻车率坐实） | —（机理与 env 无关） | 20 连跑 0 failed |

**假绿实证（30 返工实录复核 · 逐字成立）**：master 上 4 memory 文件（test_memory_injection / test_input_isolation_wiring / eval/test_memory_preference_redline / test_memory_vector_p1）——
- 宿主 env：**62 passed**（假绿：no_proxy `[::1]` → httpx InvalidURL 意外兜底回确定性通路）
- 净 env + VECTOR_RECALL=true：**7 failed / 55 passed**，失败清单与 30 返工实录**逐字一致**（memory_injection×4 + input_isolation×1 + eval redline×1 + memory_vector_p1×1）
→ 「基线绿实为 httpx InvalidURL 假绿」论断属实；fix 分支 4 文件 delenv 钉 off 后双态全绿。

## 三、flaky 核验（A3）

- fix 分支 `test_reconcile_mismatch_marks_failed` 单测 **20 连跑：20 passed / 0 failed**（每次 0.15–0.21s，确定性）。
- 读码核 UUID(int=1) 确定性论证 **成立**：种子行 `_write_null` 用 `uuid.uuid4()`（tests/test_memory_embedding_backfill.py:313，v4）；PG uuid 按字节序比较，UUID(int=1) 前 15 字节全 0，v4 第 6 字节高位必 0x4_ → 任意 v4 > UUID(int=1) 恒成立；keyset 分页 `id > last_id ORDER BY id ASC`（scripts/memory_embedding_backfill.py:220-221）下一页恒扫不到注入行 → embedded==2/remaining==1/status==failed 确定性。非「重试到绿」/sleep，符合钉死契约。

## 四、D1 断言对齐 + 变异复做（A1 + 变异检验）

- 读码核断言严格性 **未降反升**：旧期望 6 事件 `[run.start,thinking,thinking,answer,answer,done]` → 新期望 8 事件 `[run.start,thinking,tool_result,tool_result,thinking,answer,answer,done]`，与现行拓扑一致（graph.py:45-46 general/overview→retrieve · :50 retrieve→grade；rag_nodes.py:107 retrieve 发 tool_result · :175 grade 再发）。内容断言保留（agent_role/content/model）。非放松断言。
- 打桩面读码核：stub_rag_chain 打 _get_embedder / hybrid_recall / grader get_llm_provider / rerank_enabled=False 四处，全在 rag_nodes 命名空间，最小面合规；answer 节点仍由各例 fake/slow_provider 自打。
- **变异复做（亲做 1 条）**：断言临时回旧期望（删 tool_result×2）→ `pytest tests/test_chat_ws.py::test_ws_message_streams_events` **真挂 AssertionError** → 还原后 6 passed 复绿，且 `git status` tests/ 零残留。
- teardown 噪音：fix 分支 chat_ws 全文件跑 grep "Event loop is closed" = **0**（噪音消，A1 附带项过）。

## 五、A3② 全量三连跑汇总

| 跑次 | 态 | 结果 |
|------|----|------|
| 1 | 宿主 | 1367 passed / 0 failed |
| 2 | 净 env | 1367 passed / 0 failed |
| 3 | 宿主 | 1367 passed / 0 failed |

加 flaky 单测 20 连跑零复发 —— A3 双门槛满足。

## 六、改动边界 · lint · 图谱（A6 + 附带项）

- `git diff origin/master --stat`：码改动仅 tests/ 8 文件（conftest.py / test_chat_ws.py / test_capability_http_adapter.py / test_memory_embedding_backfill.py / test_memory_injection.py / test_input_isolation_wiring.py / test_memory_vector_p1.py / eval/test_memory_preference_redline.py）；**app/ · scripts/ · alembic/ · .github/ 零 diff** ✅（其余 diff 为 docs/ 过程文档）。
- `ruff check tests`：master 29 条 = fix 29 条（逐条比对触及 8 文件：唯一 C408 test_capability_http_adapter.py:59 为 HEAD 预存，双 branch 同在）→ **零新增** ✅。ruff check app 因 app/ 零 diff 与 master 恒等。
- `./scripts/graph-compile.sh` exit 0（9 graphs / 143 nodes / 210 edges · check 全 OK）；脚本重写 shared/graph.json 属生成副作用，已 `git checkout` 还原，git status 零码残留 ✅。
- `npx spec-wave task lint` PASS（W1 状态词 signed 提示 · 非阻塞）✅。

## 七、观察项（不阻塞 · 与本 task 无关 · 另议）

1. **既有顺序依赖脆弱面（master 同源）**：`pytest tests/test_capability_http_adapter.py` 单文件独立跑在宿主 .env（OPS_CAPABILITY_PERSISTENCE=db）下 4 红（test_write_is_never_retried 等 · DbIdempotencyStore 只支持异步接口，同步 invoke 路径 upstream_error → 0 calls）；master 同态独立跑为 5 红（同 4 + D2）。全量跑双 branch 皆绿 → 系**预存**单文件独立跑顺序依赖 + 宿主 .env 持久化开关耦合，非本 task 引入、非本 task 范围（钉死契约只保「有 PG 本地环境全量确定性绿」）。建议另 task 议（单文件独立跑确定性）。
2. master 净 env 下 chat_ws 挂真网不收敛 —— 反向佐证 D1 打桩必要性与「不连外网」test_strategy_note 的正确性。
3. CI 假绿缺口（workflow 无 postgres service → DB 用例 skip 绿）已按 F4 落 conftest docstring 注记；修 CI 另 task 议 —— 与本核验一致。

## 八、A1–A6 逐条判定

| 验收 | 判定 | 证据 |
|------|------|------|
| A1 D1 前红→后绿 | ✅ | master 2f/4p（亲跑）→ fix 6 passed ×2 态 · 噪音 0 · 变异真挂还原 |
| A2 D2 前红→后绿 | ✅ | master 宿主 1f/1p（亲跑）→ fix 2 passed ×2 态 · proxy_bypass 打桩恒 False 与宿主 OS 无关 |
| A3 D3 flaky 零复发 | ✅ | master 3f/10（亲跑）→ fix 单测 20 连跑 0 失败 + 全量 3 连跑零复发 |
| A4 双环境同绿 | ✅ | 本地真 PG 双态全绿；CI 假绿缺口已注记且未把 skip 绿当真跑证据 |
| A5 全量回归 | ✅ | 1367 passed / 0 failed ×3（含 B1 五处 TestClient 文件与 memory 全量，全量即覆盖） |
| A6 改动边界 | ✅ | diff 仅 tests/ 8 文件 · app//scripts//alembic//.github/ 零 diff |
| ruff / task lint | ✅ | tests 29=29 零新增 · lint PASS |

## 九、30 自称核验结论

| 30 自称 | 核验 |
|---------|------|
| D1 双补丁 + 三例打桩 + 断言对齐 [run.start,thinking,tool_result×2,thinking,answer×2,done] | 属实（读码 + 亲跑 + 变异） |
| D2 proxy_bypass 恒 False | 属实（读码 + 双态绿） |
| D3 UUID(int=1) 恒落水位前 | 属实（读码论证成立 + 20 连跑） |
| 前红后绿实证 D1 2f/4p→6p · D2 1f→2p · D3 20 连跑 0 失败 | 属实（全部亲跑复核） |
| 全量 pytest×3 = 1367/0 ×3 | 属实（亲跑 3 次同数） |
| 返工实录 purge unmask 7 红 → 4 文件 delenv | 属实（master 双态复现逐字一致） |
| ruff 零新增 · graph-compile 绿 · diff 仅 tests/ | 属实（亲核） |
| 变异 D1 回旧期望真挂已还原 | 属实（亲做复现） |
