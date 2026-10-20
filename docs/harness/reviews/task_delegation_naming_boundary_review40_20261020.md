# 审查文：delegation-naming-boundary · 40 实施审查 · 2026-10-20

- **hat**：40（实施审查 · 只审不改）
- **对象**：分支 `task/delegation-naming-boundary` · diff `d337486..HEAD`（commit `cd9b217` · 10 文件 +606/-25）
- **契约锚**：task v0.2（`docs/tasks/active/task_delegation_naming_boundary.md` · 三闸全 approved）+ SPEC v0.1（signed）+ R2 审查文（`docs/harness/reviews/task_delegation_naming_boundary_audit_R2_20261020.md` · pass）+ invoke `docs/harness/invokes/by-task/delegation-naming-boundary/invoke_20261020_30_implement.md`
- **结论**：**approve**（阻塞项 0 · 非阻塞观察 2 项）

---

## 一、复跑数字（park .env CI 等价 · 跑后已复原）

| 项 | 结果 | 与 invoke 对拍 |
|---|---|---|
| 全量 pytest（.env park） | **1762 passed / 184 skipped / 0 failed**（25.25s） | 逐字一致 ✔ |
| .env 在场对拍 | branch FAILED 37 项 vs base `d337486` worktree 同条件 37 项 → **diff IDENTICAL**（独立复跑复现，本波次零新增噪声） | 一致 ✔ |
| ruff check app tests | All checks passed | ✔ |
| graph-compile | EXIT=0 | ✔ |
| lint-imports（.importlinter） | 12 kept · 0 broken | ✔ |
| 红测先行复验 | `d337486` worktree 覆贴新测试文件 + 正名后 delegation 测试 → **23 failed / 32 passed**，与 invoke 逐字一致；RED 集合 = TC3 ×1 + TC5-b ×1 + TC7 全组 ×15（行为 2 + 解析矩阵 13）+ 三正名 def ×6 测试 ID（parametrize 展开）；TC4/TC5-a/TC8 按设计绿 ✔ | 逐字一致 ✔ |

跑后复原：.env 已归位 · base worktree 已移除 · 探针文件已删 · 工作区仅剩外波次 untracked（`backups/`、`task_query_coref_rewrite_review40_20261019.md` · 非本波次产物 · 未动）。

## 二、逐行 diff × task D1/D2 对拍

### D1 正名（auto_approve_ok → issuance_policy_allows · 直改不留别名）✔

- 定义 `app/ops/capability/delegation.py:479` `def issuance_policy_allows(specs, *, effective_scope)`——diff 仅符号名 1 行，三条件判定体逐字节不动 ✔（TC2/FP-5）
- 调用 `app/ops/lg_rag/multi/nodes.py:445` `dl.issuance_policy_allows(...)` + docstring :433 同步 ✔
- 测试三 def 同步：`tests/test_capability_delegation.py:339/:353/:359`（test_issuance_policy_allows_readonly_in_scope / _denies_write_and_sandbox_cli / _denies_out_of_scope）+ 三调用点 ✔
- 注释级三处 `tests/test_capability_testing_write.py:185/:412/:468` 仅注释改名、逻辑零改 ✔（R1 M1 补登面）
- 图谱 lg_rag 行 T1 备注换新名且去字面化（防 TC1 自咬）✔
- **TC1 grep 实证**：`grep -rnI 'auto_approve_ok' app/ tests/ docs/_tech_graph/ docs/guides/` 唯一命中 `01_modules.md:116` 闸登记表历史回写行（豁免② · 不可变历史记录）→ 三面零残留 ✔
- 无别名/无 deprecation 过渡 ✔

### D2 护栏解耦（两处真门控切新开关 · 其余耦合不动）✔

- 新开关 `nodes.py:266` `ENV_WRITE_REPLAY_GUARD_ENABLED="LG_RAG_WRITE_REPLAY_GUARD_ENABLED"` + `_write_replay_guard_enabled()`（:271-289 · 布尔默认 true=开 · 非法值 `logger.warning` 留痕回退开 · 解析承 SESSION_SUMMARY_ENABLED 先例唯方向相反，docstring 自注 R1 N-d 防误抄）✔
- 真门控仅两处切换：:931 `write_done_keys` 条件建索引 + :960 guard-skip 块头（原 :903/:931 因插入前移）✔；:987-988 关联行 `batch_write_keys` 登记在门控块外由 write_key 惰性控，跟随关系未破（全量绿 + TC3/TC4/TC5 实证）✔
- **不动实证（grep 复核）**：签发审批门 `nodes.py:999` `if _delegation_active() and str(row.get("type") or "") == "tool":` 与 scope 门 `:1300` `if _delegation_active() and not fallback and subtasks:` 保持 `_delegation_active()` 耦合未触（另 :1349/:1595 存量调用亦未动）；R1 N3 误并澄清落地 ✔
- app/ diff 面 = delegation.py 1 行 + nodes.py（净 +25 行）· 与 invoke 声明一致 ✔

### FP-2 三牙测试质量（钉行为非形态）✔

- **TC3 正牙**（默认开 · delegation off）：断言 s2 不派发 + guard-skip 终态 + `write_replay_guard_skip is True` + `replay_of == s1` + 已成功写结果照抄 + 日志钩子——行为+台账双钉 ✔
- **TC4 逆牙**（开关 false · delegation off）：断言 s2 照派 + 零 guard 终态 + 零 guard 日志——恢复 master 基线，防「关也拦」退化（FP-4）✔
- **TC5 矩阵**：on×on 照拦（与 master 零 diff）；on×off 不 skip 但签发审批门照常拦 `blocked_by=delegation_issue_hitl_required`——直接钉死「签发门保持 delegation 耦合」这一 N3 澄清的行为面 ✔
- **TC7**：行为面 2 例（非法值仍拦 + warning 留痕）+ 解析矩阵 13 例（缺省/空/真/假/大小写/空白/非法）· 解析面用 getattr 存在性断言（RED 可咬未实施态）✔

## 三、00 裁定 A/B 落实核验

- **裁定 A**（`tests/test_hitl_approved_replan_quality.py:357-359`）：`test_tc2_guard_zero_touch_when_delegation_off` 增补一行 `monkeypatch.setenv("LG_RAG_WRITE_REPLAY_GUARD_ENABLED","false")` + 2 行裁定注释——夹具级、断言/场景构造零改，与限定语逐字相符 ✔；定向复跑该钉 1 passed ✔
- **裁定 B**（`tests/test_strategy_scenario.py`）：`_banned` 收窄至 `_BANNED_PREFIXES`（app/ 越界改走波次分类）+ 注释注明裁定 ✔。**三态独立复验**：
  1. #4 分支上 #3 闸 → SKIPPED，reason 列 12 项越界全为 foreign（可审计）✔
  2. banned 探针（untracked `scripts/__tmp_gate_probe_40.py`）→ #3 闸与 #4 TC8 双 fail「禁改面（scripts/ alembic/…）出现改动」→ 删探针后恢复 skip/pass ✔
  3. 波内 fail 保牙：invoke 已动态实证（含闸文件误还原事故发现并即修复重验）；本审静态复核码径（`violations ∩ _touched_in_wave → assert not internal` 硬 fail · `_WAVE_TIP=None` 期等价判定逻辑与先例一致）成立 ✔
- #4 TC8 自身：本分支态①钉锚命中零越界 → PASSED ✔；四态结构（banned 前置全部 skip 出口 · 态④ vs HEAD+untracked 兜底）照抄蓝本 ✔

## 四、freeze 与边界

- SSE `lg-rag-sse-v1` / HTTP `lg-rag-http-v1` / 审计五动作词表 / 拒绝码 R-a~R-f / TTL 600s / HITL TTL 3600s / 三档默认值：diff 零触达 ✔
- app/ 仅白名单两文件；scripts//alembic/ 零触达；零新 event_type/路由/表 ✔
- 图谱：capability 行 delegation 备注段写实十项职责（承 §4 Q3 不增行）✔ · lg_rag 行正名同步 + 解耦/新开关/FP-2 intentional behavior change 显式声明 ✔ · 闸登记表新行（HG-GRAPH-MODULES approved 2026-10-20）✔ · 不增一级模块/边/implementedBy ✔
- env 台账：GUIDE 83→84 键（头计数 + lg_rag 段新行 + 扫描基线计数 + 修订行四处同步）✔
- 枚举外连带授权链：裁定 A/B + cap_env 快照夹具（新文件内 autouse 注册表快照恢复 · 不动共享夹具与他文件 · 修复 fp5 翻转实证）均在 invoke 呈裁→裁准链内，挂账口径一致 ✔
- 遗留挂账 4 项口径核对：GATE_VERIFY 机读误报（第四次 · status 栏 approved vs 机读 pending 矛盾，另案）· .env 37 项噪声族（对拍 IDENTICAL 实证非本波次）· 共享 cap_env 夹具泄漏面（本波次隔离未根治 · 另案）· 他务 untracked 两件（实证在场未动）✔

## 五、非阻塞观察（2 项 · 不阻塞合并）

1. **图谱 lg_rag 行双分号笔误**：`01_modules.md:35` 「三处同增）；；**delegation-naming-boundary」处连续两个 `；`（承 query-coref-rewrite 段尾叠印）。纯标点，建议 30 顺手修或留待 tech-graph-flow-resync（建议序 5/5 正好收口图谱流）。
2. **TC8 白名单联动（本审查文入库时须同步）**：本审查文路径 `docs/harness/reviews/task_delegation_naming_boundary_review40_20261020.md` 当前不在 `tests/test_lg_rag_write_replay_guard.py` TC8 白名单。untracked 态仅入 banned 检查（非禁区 · 闸不受影响）；**30 走白名单入库 commit 时须同步将本路径补入 `_TREE_ALLOWED_FILES`**（否则入库后该文件成 changed 越界 → 落态③ foreign 可审计 skip，虽不 fail 但削弱闸的严格 pass 语义）。此联动请 30 在入库 commit 一并处理。

## 六、结论

**approve**。D1 正名 8 处 + 图谱字样全落位零残留；D2 两处真门控解耦、签发门/scope 门耦合不动实证成立；FP-2 三牙钉行为；裁定 A/B 落实且三态独立复验通过；红测 23/32 与全量 1762/184/0 逐字一致；freeze 零触达。非阻塞观察 2 项（图谱双分号笔误 · 本审查文入库 TC8 白名单联动），移交 30/00 处置，不构成合并阻塞。
