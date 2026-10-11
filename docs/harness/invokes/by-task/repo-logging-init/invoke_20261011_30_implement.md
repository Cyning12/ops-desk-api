---
hat: 30
task_slug: repo-logging-init
date: 2026-10-11
---

# invoke · 30-implement · repo-logging-init（仓级 logging 初始化）

## 实施摘要

- 裁定落地：D1=A（app/main.py 模块级 import 期 `logging.basicConfig`）· D2=A（`OPS_LOG_LEVEL` 默认 INFO · 非法值回退 INFO fail-closed · 承 auto_resume.py:76 env 先例）· D3 format='%(asctime)s %(name)s %(levelname)s %(message)s'（验收文档 :139 逐字）· D4 不动 uvicorn logger（propagate=False 自带 handler · 不双行机理承 R1 实证 uvicorn 0.51.0 · disable_existing_loggers 默认 False 无冲突）。
- commits（红测先行时序）：`445ce28` test TC1 红测先行（3 红在案）→ `b329aec` feat 实现（app/main.py +28 行）。
- 测试：tests/test_logging_init.py 三组（默认 INFO / OPS_LOG_LEVEL=DEBUG 覆盖 / BOGUS 非法回退）全绿（3 passed in 2.58s）；全量 pytest：**1770 passed · 1 skipped · 1 failed**（test_memory_vector_p1.py::test_embedder_failure_degrades_with_marker · SILICONFLOW_API_KEY 缺失环境性 · 以 base main.py 对拍同红 → **零新增红**）。
- ruff：app/main.py + tests/test_logging_init.py All checks passed；全仓 55 errors 与 master 基线持平（全 pre-existing · 零新增）。

## NIT 回填（承 R1 N-2~N-6）

- **N-2（caplog 论证补一句）**：basicConfig(level=INFO) 抬 root level WARNING→INFO 后，app INFO 记录确首次进入 stderr 捕获面（全量跑 Captured stderr 见 `app.ops.rag.embedder INFO query embedder backend=siliconflow` 行实证）；惟 caplog 捕获机理系 propagate 链挂 handler（非 root handler），本改动不动任何 logger 的 level/propagate → caplog 记录面不变；tests/ 305 处 caplog 使用面由 TC5 全量跑兜底——1770 passed 零新增红即「caplog 面零 diff」实证落地。
- **N-3（TC1 识别口径钉死）**：裸 python 子进程断言——`_run_bare_import` 以 `sys.executable -c` 起子进程 import app.main，断言 root.handlers 计数==1 / level / formatter._fmt 格式串；**非 pytest 进程内**（pytest 捕获 handler 致计数误判）。
- **N-4（TC2 复跑锚点钉行号）**：六 env 组 = docs/acceptance/20261010_hitl-consumption-loop_local_acceptance.md **:20** 逐字（LG_RAG_DELEGATION_TOKEN_MODE=enforce · OPS_CAPABILITY_EXTRA_MANIFESTS=app/ops/capability/manifests/testing.v1.yaml · OPS_CAPABILITY_ALLOW_WRITE_TAGS=testing · OPS_STRATEGY_EXTRA_CANDIDATE_CAPABILITY_IDS=testing.write.echo · OPS_HITL_PERSISTENCE=db · OPS_CAPABILITY_ALLOW_WRITE=1）；坑位注 **:64**（首轮 INFO 未开台账空 · 本 task 场景反转点）；挂起→decide→resume 链台账三键（delegation_approval_consumed / token_issued / token_verified）在案 **:60**。TC2/TC3/TC4 live 验收属 40 面。
- **N-5（pytest 执行环境口径）**：本次 = worktree（**无 .env** · config.py:11 load_dotenv 静默 no-op）+ **主仓 venv python**（worktree .venv 系 231 包 no-dev 同步 · 缺 pytest/pip · 未动未软链 · 主仓 venv 经 cwd 优先解析 import 本 worktree 码 · editable .pth 主仓路径居 sys.path 末位）。task 契约3 所述 4 红基线（capability_lookups×3 + lg_rag_multi×1）系主仓带 .env（LG_RAG_HTTP_CHECKPOINTER=postgres 等渗入）口径，本环境不复现；本环境 1 红 = SILICONFLOW_API_KEY 缺失环境性（base 对拍同红）。**master 基线对拍 deferred 给 40**（须主仓 .env 环境复跑）。
- **N-6（--reload 形态裁定）**：uvicorn --reload = supervisor 起子进程重启（子进程全新 import app.main → 每进程首挂唯一 handler · 同进程双 import 不存在），叠加 basicConfig root 已有 handler 天然 no-op → 幂等成立。属论证覆盖非实证覆盖，40 可选补强。

## 契约自查（钉死 5 条 + 三面零 diff）

1. **55 处 getLogger(__name__) 既有调用点零 diff**（`git diff cae745e -- app/` 仅 main.py +28）；计数 55→56 系 main.py 初始化模块自身错误台账新增 1 处（非法 OPS_LOG_LEVEL 的 logger.error）——属「只加初始化」面，既有使用面零改。
2. **零新依赖**（requirements.txt diff 空 · logging/os 皆 stdlib）。
3. **pytest 全量零新增红**（对拍口径见 N-5 · master 基线对拍 deferred 40）。
4. **TestClient/caplog 测试面零 diff**（TC5 实证 · N-2 论证补足）。
5. **台账键字面零改**（未触碰 auto_resume.py / nodes.py 等任何台账调用点）。
- scripts / evals / alembic 零 diff（`git diff cae745e` 该三面为空）· uv.lock 等副作用无（工作区干净）。
- 图谱回写：docs/_tech_graph/l1/01_modules.md :27 `entry` 行补 logging 初始化表述（图谱预判「若有涉台账表述须回写」按实判履行）。
- TC2/TC3（裸 uvicorn live 六 env 三键 grep · compose 形态）与 TC4（access log 单行）为 live 验收面，随 40 执行；机理与锚点已备（N-4）。
