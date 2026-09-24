# Invoke · 30（改码 · 委派子 Agent）· host-v1-splittability-hardening（V1-E）

> **日期**：2026-09-24  
> **帽**：30（**00 委派子 Agent** · 00 不亲自 30）  
> **闸态**：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 全 **approved**（00 代录）· `npx spec-wave verify` **PASS**（tip `4e6d28d` 对齐后）  
> **task**：`docs/tasks/active/task_host_v1_splittability_hardening.md`  
> **SPEC**：`docs/spec/host-v1-splittability-hardening/SPEC-…_v0.md`（signed）+ D1 真值 `docs/spec/multi-replica-verify/SPEC-…_v1.md`  
> **分支 / 工作目录**：`task/host-v1-splittability-hardening` · `/private/tmp/opsdesk-wt-master40`

## 实现序（钉死）· 完成度

| 块 | 状态 | 摘要 |
|----|------|------|
| D2 | ✅ | `.importlinter` 12 contracts KEPT（`allow_indirect_imports=True` 直边）· ignore 逐条理由 · CI `import-linter.yml` · dep 入 requirements/pyproject |
| D3 | ✅ | `RegistryReader`/`RegistryWriter` + `CapabilityRegistry` 本地 dict · `set_registry` 注入 · mock/变异测 · 对拍（B1 子集绿） |
| D4 | ✅ | `GUIDE_env_inventory_v1.md`（83 键）· `llm_tiers.v0.yaml` + `strategy_pack.py` · env>pack>code · 缺省零 diff |
| D1 | ⚠ | GUIDE 补扫 9–11 已落；双进程 **9 ERROR**（`ops_sessions.tenant_id` NOT NULL · fixture 未写 · **环境/基建漂移** → D5 #1）· 未改 app/ 生产语义 |
| D5 | ✅ | FINDINGS 表 1 条另开建议 · 变异①②③ 测在 `test_splittability_hardening.py` · 图谱 capability 备注已落 · **人签待 00 代录** |

## 验证留痕

| 项 | 结果 |
|----|------|
| `npx spec-wave verify --task …` | PASS |
| `lint-imports` | 12 kept, 0 broken |
| `pytest --collect-only` | **1594** collected（承 1587 + 本波新增 7） |
| `pytest tests/test_splittability_hardening.py` | **7 passed** |
| B1 子集（capability gateway/manifest/visibility + llm budget + infer_cache + model_catalog） | **115 passed, 1 skipped** |
| `pytest tests/test_multi_replica_dualproc.py` | **9 ERROR**（FINDINGS #1 · 环境性实证） |
| `ruff check app tests` | **56** errors（开工基线约 57 · **净增 ≤0**） |
| `./scripts/graph-compile.sh` | 绿 |

## 交付 SHA

- **tip**：`41fca32`（`feat(host-v1): V1-E 可拆性硬化 D2–D5…`）
- 基线 tip（开工）：`4e6d28d`（verify PASS）

## 红线自检

- 未重写 #165 双进程基建 · 未外置状态 · 未远程 registry · 未全量策略搬家  
- 零 alembic / 零新路由/SSE / 零 freeze  
- 可 push 本分支 · **不开 PR**

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 00 下发 30（AUDIT 代录 approved · verify 后开工） |
| 2026-09-24 | 30 交付回写：D2–D5 · collect 1594 · dualproc 环境红 · 图谱待 00 代录 |
