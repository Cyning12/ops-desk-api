# Harness 40 核验 invoke — hitl-replan-carry-and-persist-guard

- task：docs/tasks/active/task_hitl_replan_carry_and_persist_guard.md
- 核验对象：30 交付三 commit（228d7d2 nodes.py 保号+建单检查 · 687689d 14 枚测试 · b857af6 invoke+图谱）
- 30 invoke：docs/harness/invokes/by-task/hitl-replan-carry-and-persist-guard/invoke_20261010_30_implement.md
- worktree：ops-desk-api-worktrees/t-hitl-carry-and-persist-guard（分支 task/hitl-carry-and-persist-guard · base master bdd45f9）
- 日期：2026-10-10 · 帽位：40 核验
- 纪律：独立复跑 · 不采信 30 自报 · 骨架先行逐项回填 · FAIL 退回详录

## 核验总表（七项 · 逐项回填）

| # | 核验项 | 结论 | 实证 |
|---|--------|------|------|
| 1 | diff 面对拍 + 面外零 + interrupt 语义段空 | **PASS** | 真 base=merge-base bdd45f9（本地 master 已前进至 5c70787=PR#220 仅补登 .env.example T1/T2/T3 env 键 · git diff master 的 .env.example -34 行为 base 漂移伪象非本分支删除）。git diff bdd45f9 --stat=恰 10 文件：nodes.py +102/-7 · tests/test_hitl_approval_consumption.py +512 · 图谱 l1/01_modules.md+graph.json 各 ±4 · 6 文档新增（含本 task R1 审查文 150 行）· 面外零。registry/policy/delegation/store/router/auto_resume glob diff 全空 · observe_node/interrupt 区零 diff（interrupt 语义段空 ✓）。nodes.py 全 diff 亲读：_stamp_host_plan 增 preserved 形参（full=locked+preserved+plan · cap 计入 preserved · plan_prefix_ids/recoverable_point 仍仅随 locked · 空 preserved 逐字节不变）· _unlocked_preserved_rows(state,locked)=unlocked∩plan行∩非terminal(_terminal_index)∩非locked·dict(row) 副本 · supervisor_node 三路径接线（:1010 空 allowlist 短路 · :1091 统一收口 · fallback-carry 零改）· _approved_fresh_for_subtask 镜像消费门（_BLOCKED_BY_DELEGATION_ISSUE 守卫+三元组+缺 capability_id 键不匹配+_decided_at_ts 归一+同一 TTL 实现）·读异常 fail-open False+warning 键 hitl_persist_guard_read_failed · _persist_hitl :1670-1680 命中→hitl_persist_guard_skip info+continue（不产新行不伪造行） |
| 2 | 新测试 14 枚抽跑 + TB3 变异组/TB6 七枚断言强度亲读 | **PASS** | 14 枚 TB 抽跑 14 passed/0.18s（含 TB6⑦ Db store 真跑非 skip · DB_AVAILABLE=True 本地 PG 在）。TB3 强度核验：_unresolved_suffix docstring(nodes.py:706-708) 定义「未解决=没有终态或终态是 error」，TB3 control 的 s2 带 error 终态恰为 codebase 语义下的「未解决」，FP-1 误取未解决后缀的 bug 形态会被抓住（非假绿）；第二枚 FP-8 双终态（output/error）防御断言 preserved==[]。TB4 五键序列化逐字节+golden 字面钉。TB5 真 supervisor_node replan 保号 [sid,run:2]+消费门台账+令牌+tool_exec 真执行+done==planned==1。TB6 七枚（①命中跳过 created==[]且 store pending==[]且 skip 日志②无 approved 照建③TTL 过期照建④缺 capability_id 键照建⑤blocked_by=prefix_touch 照建⑥alist 抛错 fail-open 照建+warning 键断言⑦Db store 真读 ISO decided_at 归一命中跳过+清理）。残留观察（非阻塞）：「preserve 仅无终态行而不看 unlocked」第三种 bug 形态无测试覆盖，不在 FP-1 枚举内且 TB1/TB4 精确 id 钉部分覆盖 |
| 3 | 全量 pytest（.env 核对）+ ruff 零新增 + graph-compile | **PASS** | .env 与主仓逐字节一致（ENV_IDENTICAL）。环境坑：worktree 自带 .venv 为空壳（无 pytest/asyncpg）·真跑测解释器=主仓 venv /Users/cyning/Desktop/Ops-desk/ops-desk-api/.venv/bin/python（pytest 8.4.2·py3.11.15）。全量 4 failed/1762 passed/1 skipped/60s——4 红=test_capability_lookups×3+test_lg_rag_multi::test_unknown_tool_at_invoke_recorded_and_continues（delegation no_token · 与 master 基线钉案同名同数 · 零新增红）。ruff：nodes.py 6 告警（C401×1/F401 CapabilityFilter×1/I001×2/UP045×2）与 bdd45f9 base 版按类按数全同 · 测试文件零告警 · 零新增（全仓 55 错均在未触及文件）。graph-compile EXIT=0（复跑改 graph.json generated_at 日期噪音 · 已 git checkout 还原） |
| 4 | B1 亲跑抽核（test_react_observe + T1/T2 测试文件） | **PASS** | 三文件（test_react_observe+test_hitl_approval_consumption+test_hitl_auto_resume）107 passed/0.93s · 与 30 自报一致 |
| 5 | live 全链终验（重头戏） | **PASS（核心两靶点闭合 · 带字面钉案）** | 环境：docker PG15 · uvicorn :8040（辟 8000/8020/8030）· 剥代理含 NO_PROXY（IPv6 项会炸 httpx URLPattern）· 六 env 组（enforce+SECRET+EXTRA_MANIFESTS+ALLOW_WRITE_TAGS=testing+STRATEGY_EXTRA=testing.write.echo+OPS_HITL_PERSISTENCE=db+OPS_CAPABILITY_ALLOW_WRITE=1）· 启动器 sys.path 钉 worktree+日志自证 CODE_UNDER_TEST=worktree 路径（**事故复盘：venv 为主仓 editable 安装·首轮 import app 解析到主仓 master 码·run a82d280f 复现 T1 重盖章偏差=阴性对照后作废**）。**靶点一 保号消费命中原 sid（T1 :1→:11 偏差正面收口）**：run 568d288a approve :1→resume→日志 15:34:33 delegation_approval_consumed{request_id=hitl_727093ad · capability_id=testing.write.echo · subtask_id=:1}（消费键三元组命中）· 后续轮 :2/:3 同形态各自 consumed；run a0850a8e approve :1(hitl_9253abff)→15:51:15 consumed{subtask_id=:1}→token_issued/verified :1→echo 真执行。**靶点二 重放不重建孤儿单（T2 hitl_5cefb116 偏差正面收口）**：每次 resume 重放期 hitl_persist_guard_skip subtask=:1/:2 在案（不再建单）· 终态 run（92539a4a · a0850a8e）pending 归组计数=0。**全链终态**：run a0850a8e（MAX_STEPS=8）approve :1→:2 两轮→seq16 hitl.resumed{approved:[:1,:2]}→seq17 observe 剪结果→seq18 supervisor 保号行 [:1,:2]+LLM 新铸 :3→预算耗尽写错误终态→seq21 aggregator→seq22 critic{outcome:end · reason:budget_exhausted}→**seq23 done{status:resumed} 终态**·Round3 探测 NO_PENDING。**字面钉案（如实登记）**：TB8 字面「done{completed}」在含 HITL 手动 resume 流**结构性不可达**——resume.py:131 硬编码 status=waiting_approval if re_interrupted else "resumed"（本 task diff 空 · 既有设计）；终态语义判定 event_store.py:99-107（done 且 status≠waiting_approval 即终态 · 缺省 coalesce completed）·history.py:161-168 同义——done{resumed} 语义=终态达成。字面 completed 仅纯 stream 无挂起流（sse_stream.py:482-490 终帧不带 status 键）可读得。**approved 路径自然完成双重结构性不可达（均面外既有语义）**：①LLM 不知晓保号行（钉死契约明写）→每轮 replan 必新铸 echo 步→新 pending（568d288a 四轮 :2/:3/:4/:5 · a0850a8e :3 实证）· 且 observe 解锁剪旧结果（:1766-1791 keep=plan_ids-approved）使 LLM 永远看不到已执行 echo 结果→盲循环；②router.py:328-357 _collect_decisions 聚合 approved 非空→恒 replan（驳回轮实测：rej :4 但 approved=[:1,:2,:3] 非空→verdict=replan 而非 settle）。**孤儿 pending 观察**：终态 run 零 pending ✓；审批列表现存 10 项分属 5 个历史 run=今日 T1/T2 及本帽早轮实验**挂起中申请**（其 run 仍在 waiting_approval 态 · 非孤儿） |
| 6 | 闸面终态：verify · lint · 图谱在册行实证 | **PASS（带钉案）** | npx spec-wave task lint PASS exit 0。npx spec-wave verify REAL_EXIT=2「VERIFY: BLOCKED · 仓级 reviews 缺口 92」——缺口全在 docs/tasks/done/ 遗留档（missing R<n> review / 结论节语义判）· 3.0.1 与 npx 解析的 3.0.2 对拍同结果 · **主仓 master(5c70787) 对拍同 BLOCKED 同 92** → 仓级基线非本 task 归因；本 task R1 审查文已在册（branch 内 committed）；30 invoke「verify EXIT=0 · VERIFY: PASS」自报不准（疑管道吞退出码）· 如实钉案。图谱在册行实证：l1/01_modules.md+graph.json 各 ±4 行 diff 在册（项1 对拍已录） |
| 7 | task 自检结论段回填 + 现场清理 | **PASS** | task 自检段回填于 docs/tasks/active/task_hitl_replan_carry_and_persist_guard.md:245（40 核验段）· 服务已杀（:8040 PORT_CLOSED）· /tmp/t4_40_* 全销毁（TMP_CLEAN）· .env 全程未触（git diff 空）· 工作区仅自产两文件（本 invoke + task 自检段）· commit 只 add 自产文件 --body-file 不 push |

## 过程留痕

- 2026-10-10 40 骨架先行落盘（本文件）。
- diff 面对拍：真 base=merge-base bdd45f9；本地 master 已前进至 5c70787（PR#220 仅给 .env.example 补登 T1/T2/T3 env 键）——git diff master 的 .env.example -34 行系 base 漂移伪象，非本分支删除。
- 环境坑两枚如实录：①shell 注入 NO_PROXY 含 IPv6 项 → httpx URLPattern 炸 InvalidURL("Invalid port: ':1]'")·剥代理须连 NO_PROXY/no_proxy/NODE_USE_ENV_PROXY 一起 pop；②主仓 venv editable 安装 → import app 默认解析主仓 master 码·首轮 live 跑错代码（run a82d280f 复现 T1 重盖章偏差 :1→:2·作阴性对照后作废）·v2 启动器 sys.path.insert(0,worktree)+断言 _unlocked_preserved_rows 存在+日志自证 CODE_UNDER_TEST。
- 跑测解释器=主仓 venv /Users/cyning/Desktop/Ops-desk/ops-desk-api/.venv/bin/python（pytest 8.4.2·py3.11.15）；worktree 自带 .venv 为空壳（无 pytest/asyncpg）。
- live 查询意图坑：首跑 query 未触 needs_tool（app/ops/prompts/assets/lg_rag.intent.system.md:9 语义=需调工具查询）→纯 RAG 无 HITL；改写为「这是一个需要调用工具的任务（就像查询 issue 状态一样）：请调用工具 testing.write.echo…」后挂起成功。

## live 实录（三 run · seq 序列与终态证据）

### run 568d288a60584aaaa11ea4353a60defa（默认步预算 · 四轮 approve+一轮驳回）

- 主流：seq6 hitl.waiting{subtask=:1 · request=hitl_727093ad} · seq7 done{waiting_approval}。
- Round1 approve :1 → resume 200 re_interrupted=true → seq8-15：15:34:09 hitl_persist_guard_skip subtask=:1（重放不再建单 · TB6 live 对口）→ 15:34:33 **delegation_approval_consumed{request_id=hitl_727093ad · capability_id=testing.write.echo · subtask_id=:1 · ttl_remaining}**（消费键命中原 sid=T1/T2 偏差正面收口）→ token_issued+token_verified :1 → echo 真执行（subtask_result id=:1 tool=testing.write.echo done）→ replan 新铸 :2（hitl_0d95d996）→ seq15 done{waiting_approval}。
- Round2 approve :2 → guard_skip :2 → consumed{request hitl_0d95d996 · subtask_id=:2} → 执行 → 新铸 :3（hitl_bea4baa4）seq23。
- Round3 approve :3 → consumed :3 → 新铸 :4（hitl_16e357f0）seq33。四轮全部保号原 sid 消费命中。
- Round4 驳回 :4 试 settle 路径 → 意外实证：日志「HITL 已批准，解锁 3 步 unlocked=[':1',':2',':3']」——根因 app/ops/hitl/router.py:328-357 _collect_decisions（T1 时代既有 · 本 task diff 空）汇总同 run 全部已决申请：approved=[:1,:2,:3] 非空 → nodes.py:1759 verdict=replan（approved 空才 settle）→ 剪结果重跑三连（token_issued/superseded :1/:2/:3 · :3 撞 policy writes=8/8 预算 policy_blocked）→ 新铸 :5（hitl_f892a304）。**裁定：approved 路径 done 自然完成在聚合语义+LLM 铸步双重作用下结构性不可达 · 均 T4 面外既有语义**。

### run 92539a4ad24b4eeba9f0e79fe0bab017（MAX_STEPS=4 · 预算收口路径）

- approve :1 → guard_skip :1 → unlock[:1] → replan 即预算耗尽 → 未终态子任务 :1/:2 写错误终态「supervisor 总步预算耗尽」→ aggregate → critic{outcome:end · reason:budget_exhausted} → done{status:resumed} 终态。零消费台账零执行（预算太紧）· 该 run 终态 pending=0 ✓。

### run a0850a8e17ae428cafce6d98db91d506（MAX_STEPS=8 · 全链两轮 approve 终态）

- 主流：seq6 hitl.waiting :1 · seq7 done{waiting_approval}。
- Round1 approve :1（hitl_9253abff）→ 15:50:59 guard_skip :1 → unlock[:1] → 15:51:15 **consumed{request_id=hitl_9253abff · capability_id=testing.write.echo · subtask_id=:1 · ttl_remaining_seconds:3583}** → token_issued{dt-1-14afb107d915 · :1}+token_verified{testing.write.echo · :1} → echo 真执行 → 新铸 :2 → resume 200 re_interrupted=true（cursor :15）。
- Round2 approve :2（hitl_617e3993）→ 15:51:16 guard_skip :2 → unlock[:1,:2] → seq16 hitl.resumed{approved:[:1,:2] · decided_by:admin} → seq17 observe 剪结果（subtask_result:[]）→ seq18 supervisor 保号行[:1,:2]+LLM 新铸 :3 → 预算耗尽 → seq19 subtask_join{:3 错误终态=supervisor 总步预算耗尽} → seq21 aggregator（如实报告失败终态）→ seq22 critic{outcome:end · reason:budget_exhausted} → **seq23 done{run_id · status:"resumed" · thread_id:9a34a7cc662e4443ba4f5630230ddfbc · events_persisted:7} 终态** → Round3 探测 NO_PENDING。
- 终态 pending 归组：a0850a8e=0 ✓ · 92539a4a=0 ✓。

## 30 自报对拍（不采信 · 独立复跑结论）

- 「全量 4failed/1762passed · ruff 6 类与 master 同 · graph-compile EXIT=0 · B1 107 枚」——独立复跑全数吻合 ✓。
- 「verify EXIT=0 · VERIFY: PASS」——**不准**：实测 REAL_EXIT=2「VERIFY: BLOCKED · 仓级 reviews 缺口 92」（疑管道吞退出码）· 3.0.1/3.0.2 对拍同结果 · 主仓 master(5c70787) 同 BLOCKED 同 92 → 仓级基线非本 task 归因（本 task R1 审查文已在册）· task lint PASS exit 0 ✓。

## 总结论

七项核验六项全 PASS · 项 5 核心两靶点（保号消费命中原 sid · 重放不重建孤儿单）live 全链闭合 · 终态 done{resumed}+零 pending 达成 · TB8 字面 done{completed} 不可达系 resume.py:131 既有设计（面外 · 语义终态已达成）· 两条钉案（verify 自报不准 · approved 路径结构性不可达成因）如实登记。**裁定：可进 PR 队列（附钉案）**。
