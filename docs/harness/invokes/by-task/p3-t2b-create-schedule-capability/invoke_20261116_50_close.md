# invoke_50 · close（p3-t2b-create-schedule-capability）

## 内容

- PR Cyning12/ops-desk-api#425 squash merge 完成（merge commit
  57e0c727 · CI 四 job 全绿：check 22s / import-linter 21s /
  lint-wiki-delta 26s / pytest 2m37s · exact head e99842a0）。
- 本 invoke：task 档 active → done；registry entry status=closed +
  wave_tip=57e0c727。
- 交付物：`app/ops/capability/manifests/ops.schedule.v1.yaml`
  （ops.schedule.create · write/medium/tenant_scoped · hitl.required +
  snapshot_fields 九键 · idempotency_key {{request_id}} · args_schema
  required 四键逐字 + request_id 可选 · output_fields 四键）+
  manifest.py `ADAPTER_PREFIX_SCHEDULE_SERVICE` 第三前缀（冒号串形态
  偏差 D1）+ `app/ops/schedule/service.py` adapter
  create_schedule_from_capability（薄委托 store.create_schedule
  kw-only · claim/acomplete/release 幂等链 · 422 逐字透传 ·
  tenant/user 只取 ctx 双谓词 fail-closed · request_id 回退
  {run_id}:{subtask_id}）+ strategy/config.py supervisor allowlist
  9→10 + tests/test_p3_t2b_create_schedule_capability.py 14 用例 +
  钉演进两件（smoke/env_candidates）+ 图谱 01_modules.md 登记与
  HG-GRAPH-MODULES 签收行。

## 过程要点

- PR #425 事件派发异常：opened/reopened/空提交/docs push/amend 强推
  五事件未派发 CI（check-runs=0），同期 p3-t3/p3-t5 PR 正常派发 →
  判 #425 特异性偶发；两次 rebase 后 synchronize 均正常派发。
- 并行波次 CONFLICTING 两次：p3-t5 两 merge（e83537a9）与 p3-t3
  两 merge（3683b8df）先后入链 → 两轮 rebase，冲突均为追加型
  （registry.yaml 相邻 entry · 01_modules.md schedule 行/签收表），
  双侧全保留原则解冲突；schedule 行手工融合（p3-t3 lg_rag deps +
  本波 capability.idempotency deps · 备注双登记）；P3-T3 签收行在
  冲突解决中一度误丢，立即从 origin/master 恢复补回。
- 40 对账补锚：when_to_use/when_not_to_use 逐字钉 + 词表外 kind
  422 透传钉（13→14 用例）。

## 验证台账

| 项 | 结果 |
|---|---|
| CI check / import-linter / lint-wiki-delta / pytest（PR #425 · e99842a0） | 全 pass |
| 目标 14 用例（真 PG opsdesk_test · p3t2b 前缀） | 绿 |
| 全套件净树（rebase 后） | 2405 passed, 1 skipped · EXIT=0 |
| 钉演进三面（smoke + env_candidates + 本波 · rebase 后） | 48 passed |
| ruff check app tests | 绿 |
| spec-wave task lint / verify | PASS（三闸 approved） |
| registry yaml safe_load | PASS（27 entries · 本 entry closed+wave_tip） |

## 结果

P3-T2b close。清理：删除 task/p3-t2b-create-schedule-capability 与
close 分支 + worktree（.venv 符号链接全程未入树）。
