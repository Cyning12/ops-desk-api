# CLOSE：graph-json-freeze-date-pin（2026-10-17）

## 一、任务信息

| 字段 | 值 |
|---|---|
| task_slug | graph_json_freeze_date_pin |
| 类型 | 仓卫生 / 工具链产出确定性收口（chore · 零 app/ 改动 · graph_change_layer=none） |
| 出处 | close_ci_specwave_pin_align_20261017.md §四·2 / §七·1「graph.json freeze_id 脱日期化另立案」 |
| 分支 | task/graph-json-freeze-date-pin（worktree t-graph-freeze · 已清理） |
| PR | #266 MERGED · squash 72b5740 · 2026-10-17 |
| 关账帽 | 50（00 兼 · 维护者授权代合并 m00571 问答选定） |

## 二、交付清单

- scripts/graph_yaml_to_json.py：freeze_id/generated_at 脱日期化（+57/-14 行量级 · datetime 时钟依赖整体移除）
- docs/_tech_graph/shared/graph.json：一次性落定 freeze_id=OPS_DESK_API_TECH_GRAPH_FREEZE_e42e95d67c050b36_V1 · generated_at=sha256-e42e95d67c050b36
- 归档随 PR：task 档 + 10/20/30 invoke×3 + R1 审查文（址A）

## 三、验收核验（逐 TC）

- TC-1 PASS：graph-compile.sh 双跑 + TZ=America/New_York 扰动三跑，sha256 全等 7d84fdc6db427a9e…，cmp 字节一致；md 产出幂等零 diff
- TC-2 PASS：graph.json:3 骨架 grep ✓（前缀+_V1 后缀兼容）· compile 内 check 9/9 全 OK
- TC-3 PASS：build_site.py EXIT=0 · site-data.json freeze_id 非空透传 · 消费方（build_site.py:558-559 / app.js:55）grep 实证纯透传/纯展示无格式解析；dist 为 git 追踪构建产物验证后已恢复（N-3 裁定留痕）
- TC-4 PASS：CI 三轮全绿（check/pytest/import-linter/lint-wiki-delta）· CI run 39012125582 日志 graph.json sha256=7d84fdc6… 与本地完全一致（stdout 打哈希取证法）· 异绝对路径干净 worktree 复跑同值（FP-3 排除）
- TC-5 PASS：grep datetime 零命中（时钟模块整体不导入 · docstring 字面噪声已清除）
- TC-6 PASS：diff 白名单 7 档零越界 · 钉版 spec-wave 3.3.0 字面零 diff · 零 app/ diff
- pytest：1843 passed / 1 skipped / 4 failed——4 失败环境归因实证（3 例 master 基线同败 asyncpg/dualproc · 1 例 worktree 缺 .env 补入后 PASS），与本 diff 零因果

## 四、偏差与钉案

1. 方案定案=候选①内容 hash 派生（freeze_id=..._FREEZE_<sha256-16hex>_V1 · generated_at=sha256-<16hex> · digest 由 schema_version+graphs+nodes+edges 规范化 json.dumps(sort_keys,separators,ensure_ascii=False) 派生）。未偏离 task 框定三候选，无需回 10。弃②env 注入（默认值确定性约束下等价①+注入面 · FP-5 分裂风险）· 弃③git commit 时间（tech-graph.yml:15 checkout@v5 无 fetch-depth 浅克隆实证不可行）。
2. FP-1 顺序硬遵守：先实证 spec-wave@3.3.0 freeze 字面仅 cli-graph-yaml.js:7/:453/:511（compile/export 路径）· checkGraph 仅比对 nodes/edges 集合与计数、check 路径零 freeze 断言，再动手定案。
3. 语义变化钉案：freeze_id/generated_at 语义由「何时编译」转为「编译的是什么内容」——内容不变则戳不变（字节级幂等）· 内容变则戳变；冻结骨架与展示面（arch-browser 页头 freeze_id · gen）零感知。
4. 20 R1 非阻塞 N-1~N-4 全部遵循留痕（照录段标法 / 「编译产出 md」口径收紧 / TC-4 双取证法 / K7 grep 实证覆盖）。

## 五、签录

- HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES：approved（2026-10-17 维护者签 · 00 代录 · 维护者会话授权）
- 20-task-audit R1：内容签收（docs/harness/reviews/task_graph_json_freeze_date_pin_audit_R1_20261017.md）
- 30：f319c103 交付 · 30 invoke docs/harness/invokes/by-task/graph_json_freeze_date_pin/invoke_20261017_30_impl.md
- 40 轨：本 task 编排面 40=PR CI 绿核验，已由 30 invoke TC-4 CI 实证覆盖 + 父级 gh pr checks 复核（4/4 绿）收口，未另派独立 40 帽（照登）

## 六、资源清理

- 远程分支 task/graph-json-freeze-date-pin 已删 · 本地分支已删 · worktree t-graph-freeze 已移除（干净）
- master=72b5740 · 工作树净 · 无残留

## 七、维护者 checklist

- [x] PR #266 合并（squash 72b5740 · CI 4/4 绿）
- [x] 分支/worktree 清理
- [x] task 档入 done/ · README 登记 · 50 invoke 落盘
- [ ] （无遗留开账项）

## 八、修订记录

| 日期 | 说明 |
|---|---|
| 2026-10-17 | CLOSE 落盘（50 帽 · 全链当日闭环：10 落稿→20 R1→签闸→30 交付→PR #266→CLOSE） |

## 九、附录

- 质量钉复跑（本帽亲跑）：npx --yes spec-wave verify --target . → EXIT=0 VERIFY: PASS（4 条存量基线豁免留痕 · 无新增）；spec-wave task lint done/ 档 EXIT=0 LINT: PASS
- 关键哈希：graph.json sha256=7d84fdc6db427a9e448ea8cff3180212a8850b28f8893a35cd0dec9b06dd2f1a（本地/TZ 扰动/异路径/CI 四面一致）
