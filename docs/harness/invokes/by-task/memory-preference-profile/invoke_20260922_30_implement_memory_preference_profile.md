# invoke · 30-implement · memory-preference-profile

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 30 实现（不改闸 · 不签闸 · 不 push） |
| **分支** | `task/memory-preference-profile`（每次 commit 前 `git branch --show-current` 核验） |
| **task** | `docs/tasks/active/task_memory_preference_profile.md`（signed · HG-TASK-DRAFT/HG-AUDIT-R1/HG-GRAPH-MODULES 全 approved · `npx spec-wave verify` PASS 后可 30） |
| **SPEC** | `docs/spec/memory-preference-profile/SPEC-memory-preference-profile_v1.md`（signed 4a2f4d9） |

## 实现（D1→D5 · 承 SPEC §8 序）

- **D1 闸放开**：`gate.py` `ALLOWED_KINDS=frozenset({"fact","preference"})`；双向 key 域绑定（`kind=preference` ⟺ key 首段 `pref`）→ 新原因码 `key_kind_mismatch` 入 `REJECT_REASONS`（7→8 码）；显式-only 通路约束：extract schema 无 kind 字段 + 构造点钉死 fact（代码零改动 · 单测断言钉死）。
- **D5 迁移先行**：`alembic/versions/20260922_memory_kind_preference.py`（drop+add `ck_ops_memory_facts_kind` → `IN ('fact','preference')`；零新列零新索引；回滚注释含「先清 preference 行」）；`models.py:470` 同步。**往返实测**（scratch 库 `opsdesk_migration_test`）：upgrade ✓ → 带 preference 行 downgrade **显式炸**（CheckViolationError · 停原地）✓ → 清行 downgrade ✓（旧 CHECK 拒 preference 写、收 fact 写）→ re-upgrade ✓。
- **D3 service**：`_write_in_session` 查重谓词补 `kind == candidate.kind`（双保险第二道）；新增 `revoke_by_key(tenant_id, user_id, key)`——必带 tenant+user 谓词 · 只动 active（幂等 0 行）· 审计日志记 affected（含 0）· 不物理删。
- **D2 渲染**：`continuity.py` 分节渲染（`[已知事实]` 节 / `[用户偏好]` 节 + 引导语「显式陈述 · 非客观事实 · 无偏好不要假设或编造」）；仍单条独立 SystemMessage（`inject_memory_facts_block` 零改动）；**无 preference → 偏好节物理不存在**；fact-only 渲染与现网**逐字节一致**（对拍断言 + 实跑验证）；span 双计数 `memory_facts_injected` / `memory_preferences_injected`（preference=0 不出该 key，fact-only 观测面零变化）；召回 SQL 不加 kind 谓词 · 零新 env · 零新 SSE 事件。
- **D4 红线**：结构断言（无偏好无节）+ 离线金样 `evals/memory/preference_redline_v1.yaml`（P0 清单↔实现对应 / P1 无记忆用户偏好类提问零偏好节 G1–G4 / P2 引导语锚点 / P3 偏好不污染事实节 · 各带反向对照防空真 · 热路径零 LLM-as-judge · 判定面=注入上下文结构）+ 实现 `tests/eval/test_memory_preference_redline.py` + 三态全链路变异检验（test_memory_service_db 写入→污染→revoke_by_key→消失）。

## B1 旧测影响面 13 行 · 逐条处置回填

| # | 处置 | 回填 |
|---|------|------|
| 1 | 改编 | `test_kind_not_allowed` 改用集合外值（parametrize `"profile"/"PREFERENCE"/"prefs"/""`）；preference 放行面由新 `test_preference_with_pref_key_allowed` + 双向绑定三态覆盖 |
| 2 | 改编 | enumerable 覆盖清单补 `key_kind_mismatch` 双向两态 + `kind_not_allowed` 换集合外触发；新增 `REJECT_REASONS` 8 码集合钉死 |
| 3 | 回归 | gate 其余 10 用例零改动全绿（40 passed 含新增） |
| 4 | 改编 | `test_gate_rejection_writes_nothing` 换 `key_kind_mismatch`（preference+非 pref. key）触发 + 补集合外 `kind_not_allowed`；「闸拒不落库」语义不变 |
| 5 | 回归+新增 | `test_same_key_supersedes_old_value` 零改动全绿；新增 `test_preference_same_key_supersedes_old_value` + `test_cross_kind_same_key_no_supersede`（直插 ORM 绕闸模拟域松动 · 谓词含 kind 钉死） |
| 6 | 回归 | revoke_by_source 幂等/三态先例零改动全绿；范式被 `revoke_by_key` 三态沿用 |
| 7 | 回归 | service_db 召回谓词/过期/租户面零改动全绿（召回 SQL 未加 kind 谓词） |
| 8 | 回归+新增 | injection 既有 15 用例零改动全绿（fact-only 逐字节守护成立）；新增分节/无节物理不存在/逐字节对拍/锚点/span 双计数 8 断言 |
| 9 | 回归+新增 | extract 12 用例零改动全绿；新增 schema 无 kind 字段 + 构造点 kind==fact 断言 |
| 10 | 回归+新增 | vector 8 用例零改动全绿；新增向量通路召回 preference 进偏好节断言 |
| 11 | 回归 | 辅扫 4 文件（time_decay_tz/embedding_backfill/session_continuity/lg_rag_session_continuity）零改动 · 全量重跑确认 |
| 12 | 新增 | 守护测试 +25（gate 40 / injection 27 / service_db 13 / extract 16 / vector 9 / redline eval 4 · collected 1210→1235）；evals 金样 `evals/memory/preference_redline_v1.yaml` 新增 |
| 13 | 新增迁移 | `20260922_memory_kind_preference` 挂 `20260921_llm_usage` 后（slug 从 task 建议名缩短——alembic_version varchar(32) 实测溢出显式炸）；既有迁移零改动 |

## 变异检验三条（实操 · 非空真）

- **① 污染可检**：临时把渲染改为 preference 进事实节 → 分节断言 **8 挂**（injection×5 + redline×3 含 P1/P2/P3）；恢复后 31 全绿。✓
- **② 清除可检**：`test_mutation_wrong_preference_pollutes_then_revoke_by_key_erases` 三态全断言（写入错误偏好 → 注入块偏好节真出现污染且不串事实节 → `revoke_by_key` → 消失 + 偏好节物理不存在）；真 PG 通过。✓
- **③ 显式-only 可检**：临时给 extract 构造点传 `kind="preference"` → 构造点单测 + 噪声拒写用例 **2 挂**；恢复后 16 全绿 · `git diff extract.py` 为零。✓

## 验证（真跑）

- `pytest tests` 全量：**1235 passed / 3 failed / 1 skipped**（collected 1210→1235，+25 新增守护，**无既有用例删除**）；3 红 = 基线环境性同款（capability proxy ×1 + chat_ws ×2，本机代理/WS 环境），与 master 基线 4 红对照：memory_backfill flaky 本轮未复现（偶发随机序已知）。
- `ruff check app tests`：**57 = 基线零新增**（新增代码期间曾 +2 SIM300，已改 `sorted()` 断言消除）。
- alembic 往返：upgrade →（脏 downgrade 显式炸）→ 清行 downgrade → re-upgrade 全真跑通过（见 D5）。
- `./scripts/graph-compile.sh`：**绿**（`01_modules.md` memory 行备注级更新 + HG-GRAPH-MODULES 新行写内容留 00 代录位；`shared/graph.json` 仅时间戳漂移已还原不提交）。
- 生产路径 diff 白名单：`git diff master -- app/ alembic/` = gate / service / continuity / models CHECK / memory README + 新迁移文件（tests/evals/conftest 在测试面）——**零偏离零变更预判**（无新一级模块/路由/表/事件类型/列/索引），无回炉。

## 图谱

`docs/_tech_graph/l1/01_modules.md` memory 行备注补「memory-preference-profile（2026-09-22）：kind=preference 放开（闸 + 绑定 + CHECK + revoke_by_key + 分节 · 显式-only）；零新路由/表/事件类型/列/索引」；HG-GRAPH-MODULES 表末新增行（内容已写 · status=pending **00 代录位** · 30 不留签）。

## 闸态（30 不动闸）

- HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES = approved（30 前 verify PASS）；HG-PILOT-OPSDESK-GLAYER=n/a。

## 遗留（承 R4/R5 residual）

- 统一预算下 preference 挤占 fact 召回：首期量少 + span 双计数可观测，真出现再切预算另案。
- 显式-only 靠构造点单测 + 非范围维持（非闸内单规则）：未来新增写入通路时必须复判。
- 金样判定面 = 注入上下文结构（确定性），不裁判模型自由文本——「编造偏好」的模型端残余风险由引导语 + 结构断言双保险承接。

## 下一棒

40 核验：fact 节逐字节对拍独立重做 · 变异检验三条复做 · alembic 往返复跑 · 验收 27 条逐条亲跑 · 全量 pytest/ruff/graph-compile 复核 → PR。
