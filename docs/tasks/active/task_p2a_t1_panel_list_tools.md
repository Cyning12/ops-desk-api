---
title: task · feat · P2a-T1 面板列表双工具 + 闸基
---

# task · feat · P2a-T1 面板列表双工具 + 闸基

> **状态**：`active`（2026-11-16 落卡）
> **来源**：issue Cyning12/ops-desk-workspace#23（m03064 夜间授权 · 设计真源 workspace 08-p2a-tools-design.md 终稿 §7 T1 行）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p2a-t1-panel-list-tools |
| base | e0a6734 |
| 关联 issue | Cyning12/ops-desk-workspace#23 |
| 关联 PR | （落 PR 后回填） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 capability 数据面（manifest/allowlist）+ 元数据补全 |

## 人工闸（维护者授权）

| human_gate_id | status | 签核人 | 日期 | 说明 |
|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 维护者（issue #23 m03064 夜间授权 + 08 设计终稿） | 2026-11-16 | P2a-T1 落卡：设计终稿 §7 T1 行为唯一范围真源；禁 freeze 帧/schema 触碰 · 禁图改动 · 禁新 DDL/依赖 |

## 背景

P2a 把面板视图数据查询封装为只读 capability 进默认面（08 §0）。本单是第一波：两枚列表工具（query_issues / query_pull_requests）落 lookups.py + manifest + supervisor allowlist，并落三件闸基——①span payload 补 tenant_id（R3 · graph_snapshot 全局放行的签收条件，本波先行）；②mock 两枚 description 收窄标 demo（R7 · 降语义竞争）；③catalog 总长断言与闸矩阵测试基座（§5）。

## 范围

1. `app/ops/capability/lookups.py`：加 `query_issues` / `query_pull_requests` 两 adapter——复用 `_tenant_from_ctx`；谓词集对齐面板端点（issues.py:30-92 / pulls.py:30-90：tenant 谓词 + state/scan_status/module_tag/label.contains / ci_status 等值 + updated_at desc 分页）；**adapter 显式校验** page≥1、1≤page_size≤20、state 词表（R1：schema_validate 不校验 enum/min/max），违规抛 LookupError 由 gateway 转 ok=False；裁剪/整形逻辑抽独立纯函数；返回剔 uuid `id`、不带 body。
2. `app/ops/capability/manifests/builtin.v1.yaml` +2 条：全字段（含 output_schema · tags=panel+域+readonly · additionalProperties:false）；args_schema **不写 per-prop description**（catalog ≤6000 体积红线 · 08 §5.5）；description 承载全部使用引导（R2）；禁「实时」字样。
3. `app/ops/capability/defaults.py`：`_DEFAULT_SPECS` 同步 +2（回退路径契约不漂移 · test_capability_manifest 对齐断言前提）。
4. `app/ops/strategy/config.py`：supervisor allowlist +2。
5. `app/ops/capability/gateway.py` `_write_span_metadata`：payload 补 tenant_id 一行（R3 · 元数据补全不动图）。
6. mock 两枚（mock_get_issue_status / mock_get_deploy_info）description 收窄标 demo（R7 · YAML 与 defaults.py 同步改）。
7. 测试：
   - `tests/test_capability_manifest.py`：`_BUILTIN_IDS` 5→7 · 计数 5→7 · 新条目全字段钉死断言；
   - 新增 `tests/test_capability_panel_tools.py`：闸矩阵（adapter 拒绝口径 page_size=0/21 · state 词表外 → LookupError → ok=False · additionalProperties 多余键 → args_schema_invalid · tenant_scope_missing 负样本×2 · 委派层默认 off）+ 双层范式（InMemory CI 恒跑 + 真 PG 双租户 seed：跨租户空集 · 分页 total/page 正确）+ catalog ≤6000 断言 + span payload tenant_id 实证；fixture 含 budget.reset()/circuit.reset()（08 §5.3）。
8. `docs/_tech_graph/l1/01_modules.md` capability 行备注 + HG-GRAPH-MODULES 签收行。

## 非范围

- 面板 UI/REST 端点改动（adapter 按同谓词集重写 ORM，不复用端点函数 · 08 §8.3）。
- get_overview / graph_snapshot（T2）；MCP 对齐评审（T3）；冒烟验收（T4）。
- adapter 白名单扩容（manifest.py:64-66 既有 defaults:/lookups: 两前缀够用）。
- 图（app/ops/lg_rag/）零改动 · nodes.py 零改动 · SSE 零新帧 · 零新 DDL/索引/依赖（08 §8）。
- when_not_to_use 填充（R2 空调杆 · loader 允许缺省）；mock 工具退役（仅 description 收窄，去留 P2b 评审）。
- budget/circuit 默认值调整（08 §8.13 登记观察）。

## 失败路径

- 非法 args（page/page_size 越界 · state 词表外）→ adapter 抛 LookupError → gateway `ok=False`（图不中断，承 lookup 先例）。
- ctx 缺租户 → Policy 层 + adapter `_tenant_from_ctx` 双保险 → `tenant_scope_missing` ok=False。
- 空结果（无匹配行）→ `items=[]` total=0 属正常成功（output_schema 不标 empty_is_suspicious）。
- 回退=manifest 两条目 enabled:false / allowlist 摘除即可，adapter 代码留存无行为面。

## 验收标准

- [ ] query_issues / query_pull_requests 注册进默认面（count 5→7）· 全字段钉死断言绿
- [ ] adapter 拒绝口径：page_size=0/21 · state 词表外 → LookupError → ok=False（断言 adapter 拒绝非 schema 拒绝 · R1）
- [ ] additionalProperties:false 多余键 → args_schema_invalid；tenant_scope_missing 负样本×2
- [ ] 真 PG 双租户 seed：A 租户查不到 B 租户行（空集）· 分页 total/page 正确
- [ ] catalog 总长断言 ≤6000 字符绿
- [ ] span payload tenant_id 实证用例绿
- [ ] 委派层默认 off 用例绿
- [ ] ruff 绿 · 全量 pytest 绿（含真 PG 层 CI 真跑）· graph-compile 绿

### 自检结论

（验收后勾验回填 · 40 波台账）

## 必读列表

- workspace 08-p2a-tools-design.md §0/§1.2/§1.3/§2/§5/§7/§8/§10（设计终稿唯一范围真源）
- `app/ops/capability/lookups.py`（既有两 adapter 范式 · _tenant_from_ctx:58-66）
- `app/ops/issues.py:30-92` · `app/ops/pulls.py:30-90`（面板谓词集）
- `app/ops/capability/manifest.py:288-328,517-645`（V10 校验 · when_to_use 必填 · 字段族）
- `tests/test_capability_lookups.py`（DB/双租户/tool_exec 测试范式）
- `tests/test_stage_w_write_expand.py:87-103`（_DB_MARK + autouse 复位 fixture 范式）

## 思考轮控制

- R0（勘察）：ci_status 词表**不可钉**（仓内无生产写入方——admin/sender/mapper.py:93 恒 None · 仅测试夹具虚构值）→ 按 §1.3 走 string 放行 + description 列已知值；loader 硬约束 when_to_use 必填非空（manifest.py:523-526）与 R2「不填」冲突 → 偏差裁定：新条目填与 description 一致的简短引导，when_not_to_use 不填；manifest 对齐测试要求 `_DEFAULT_SPECS` 同步 +2（否则 set(_BUILTIN_IDS)==hard_ids 破）。
- R1（审查）：设计终稿已经 platform/product 双向评审 7 项 blocking 裁定关闭（08 §0 R1-R7），本档照终稿执行。
- R2–R4：实施中按证补充（见 invokes 30/40 台账）。
- R5（组织人终裁）：维护者。

## 实现备忘

- ci_status 词表结论：**不可钉**——仓内无生产写入方（app/ops/admin/sender/mapper.py:93 恒 None · 面板 app/ops/pulls.py:58-59 自由串等值过滤 · 仅测试夹具虚构 "success"/"pending"）→ 按 §1.3 走 string 放行 + description 列已知值（GitHub check 惯例 success/failure/pending；现 sync 波恒 null，过滤当前命中空集）。
- 偏差登记：
  1. when_to_use loader 必填非空（manifest.py:523-526）与 R2「不填」冲突 → 新条目填与 description 一致简短引导；when_not_to_use 不填（loader 允许缺省）。
  2. manifest 对齐测试断言 set(_BUILTIN_IDS)==hard_ids → defaults.py _DEFAULT_SPECS 同步 +2（回退路径契约不漂移）。
  3. supervisor allowlist +2（设计 §7 明项）推进 tests/test_strategy_env_extra_candidates.py TC1① 对拍锚（master 静态五枚逐字节 → 七枚 · stripped 序同步 · 语义断言不动）。
  4. 主仓 .env 含 LG_RAG_DELEGATION_TOKEN_MODE=enforce → 委派默认 off 用例须 monkeypatch.delenv(dl.ENV_MODE)（首战翻车已修）。
- 既有基线实证：直接 import app.ops.strategy.config 触发循环 import（strategy.builder ↔ lg_rag.multi.nodes）为 master 基线既有（git stash 实证），与本单无关。

## 测试策略

双层范式：InMemory 层 CI 恒跑（闸矩阵 · catalog · span · 委派）+ 真 PG 层 `_DB_MARK`（双租户 seed · 隔离空集 · 分页）；fixture 含 budget.reset()/circuit.reset()/registry clear+ensure；capability 套件运行前 blank 四键 env（OPS_HITL_PERSISTENCE / OPS_CAPABILITY_ALLOW_WRITE / OPS_CAPABILITY_ALLOW_WRITE_TAGS / OPS_CAPABILITY_PERSISTENCE）防 .env 污染。

## 修订记录

- 2026-11-16：落卡过闸（HG-TASK-DRAFT approved · issue #23 m03064 夜间授权 + 08 设计终稿）。
- 2026-11-16：实施+测试波回填实现备忘（ci_status 结论 · 偏差四条 · registry 偏差二同步）。
- 2026-11-16：全量对拍（branch vs master+同 .env worktree）失败集恒等，余红皆 .env 环境污染（承 api-controlled-write-hitl 先例）；「builtin 五枚基线」count 锚另两处推进 5→7（test_capability_testing_write.py:329 · test_stage_w_write_expand.py:260 · registry 偏差三登记）。
