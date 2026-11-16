# invoke_40 · acceptance（p3-t2b-create-schedule-capability）

## 内容

40 验收：全量测试复跑 + 提交后闸测试复绿实证 + 验收标准逐条核对 + CI 四绿终裁。

## 验证台账

| 项 | 结果 |
|---|---|
| `pytest tests/test_p3_t2b_create_schedule_capability.py`（真 PG · p3t2b 前缀） | **14 passed** |
| 钉演进三面（smoke + env_candidates + 本波） | **48 passed**（rebase 后并入 p3-t5 admin 用例复跑 84 passed） |
| `pytest tests` 全量（提交后净树 · rebase e83537a9 上面 8addf01f+2580ba0b） | **2405 passed, 1 skipped · EXIT=0**（脏树期 9 红=6 钉演进已修+3 净树门提交后自解实证） |
| `ruff check app tests` | All checks passed |
| spec-wave task lint | PASS（自检回填后 W3 消除） |
| spec-wave verify | PASS（HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 均 approved） |
| registry.yaml entry | yaml.safe_load 27 waves · 末位=p3-t2b-create-schedule-capability · status=active · base=17337d35 |
| **CI 终裁（PR #425）** | **四绿：pytest 2m54s · check 23s · import-linter 12s · lint-wiki-delta 13s** |

## 过程备忘

- **CI 事件未派发异常**：PR #425 opened/reopened/synchronize（bea5cc6b 空提交）三事件
  均未派发 workflow（check-runs=0 · 同期 p3-t3 PR 正常派发）；根因不可考（GitHub 侧
  偶发），rebase origin/master（17337d35→e83537a9 · p3-t5 两 merge 入链）后强推
  2580ba0b 触发 synchronize 正常派发。rebase 冲突仅 registry.yaml 追加型
  （p3-t5 closed entry 与本波 entry 相邻），两 entry 全保留解冲突。
- **锚点补齐**：40 对账发现验收标准两锚未落（when_to_use/when_not_to_use 逐字 +
  词表外 kind 422 透传），30 补 test_manifest_fields_pinned 引导语钉 +
  test_adapter_422_kind_vocabulary_passthrough（13→14 用例），amend 入 feat commit。

## 验收标准逐条（对账 task 档 11 条）

- [x] manifest 加载成功且 V1（idempotency_key 声明）/V2（hitl.required）/V13
  （tenant_scoped）逐字段断言有锚 → test_manifest_fields_pinned
- [x] catalog 引导语 when_to_use/when_not_to_use 逐字断言有锚 → test_manifest_fields_pinned
- [x] HITL 拒绝路径：blocked=capability_write_hitl_required + hitl_required=True +
  零行落库有锚 → test_hitl_rejected_settles_without_write
- [x] HITL 通过路径：真行落库 + output 四键 + approval_id 串链有锚 →
  test_hitl_approve_resume_real_write
- [x] 双上限 422 逐字透传（per-user 20 / per-tenant 200）+ 词表外 kind 422 透传有锚 →
  test_adapter_422_dual_quota_passthrough / test_adapter_422_kind_vocabulary_passthrough
  （interval<300 → test_adapter_422_interval_passthrough）
- [x] 幂等重放 duplicated=true 零新行 + 回退键 {run_id}:{subtask_id} 重放不双写有锚 →
  test_adapter_idempotent_replay_no_double_write / test_adapter_request_id_fallback_run_subtask
- [x] allowlist 计数 9→10 有锚 → test_allowlist_supervisor_9_to_10（+smoke/env_candidates
  钉演进 · test_supervisor_allowlist_exactly_ten）
- [x] 委派层 monkeypatch.delenv fail-closed 不落笔有锚 → test_delegation_off_failclosed_no_user_id
- [x] pytest 目标测试绿（14/14 · 真 PG opsdesk_test）· 全量 2405 passed 净树实证 · CI 终裁
- [x] ruff check app tests 绿
- [x] 01_modules.md capability 行备注 + schedule 行 deps 登记 + HG-GRAPH-MODULES
  签收行已回写（:34 / :40 / 签收表 P3-T2b 行）

## 结果

进 50（squash merge PR #425 → CLOSE：task done 搬家 + registry closed+wave_tip 钉 +
invoke_50 → close PR → CI 四绿 → merge → 清分支/worktree）。
