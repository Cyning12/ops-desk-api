# CLOSE：lg-rag-capability-output-schema（capability manifest 补 output_fields——planner 契约声明从「猜」变「从清单选」）

> 关账日期：2026-10-28 · 关账人：00（delegate-only · 维护者会话签收 HG-AUDIT-R1 + 验收 1-4 签收（m00376）+ 验收 5 live 闭合后「后端签收归档」（m00729））
> 体例承 [close_supervisor_replan_error_feedback_20261027.md](close_supervisor_replan_error_feedback_20261027.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_lg_rag_capability_output_schema.md](../done/task_lg_rag_capability_output_schema.md)（已归档 done/） |
| 性质 | feature · 00 delegate-only 单窗多棒（20 R1 → 回填 → 30 → 40 live）· 00 本窗零实现码 |
| 由来 | run d3a49/cb2548 双实证：planner produces 猜 ['title','body','status']（实际 state）；PR #293 B 层反哺只能事后纠错且修不动锁定前缀——源头消猜须 manifest 声明输出字段 |
| PR | [#294](https://github.com/Cyning12/ops-desk-api/pull/294) MERGED · squash `bfed4cd` · CI 4/4 绿 |
| 审查 | R1 [task_lg_rag_capability_output_schema_audit_R1_20261027.md](../../harness/reviews/task_lg_rag_capability_output_schema_audit_R1_20261027.md) **BLOCKED（B1 漏 builtin.v1.yaml 主加载面）→ 六处回填 → 通过**；非阻塞 N1（与既有 output_schema 分工注明）/N2（catalog 原仅渲染 id/描述/risk）/N3/N4（全裁空视同空=不校验） |
| 闸 | HG-AUDIT-R1 approved（维护者 2026-10-27 m00272「签收A，消除猜测」· 00 转录）· HG-GRAPH-MODULES n/a |

## 二、交付清单

| 产物 | 说明 |
|---|---|
| `app/ops/capability/types.py:118-122` | `CapabilitySpec.output_fields: tuple[str,...]=()`（空=不校验；与 P0-1 output_schema 运行期契约分工注释） |
| `app/ops/capability/manifest.py:533-537,641` | YAML 加载面解析校验 + spec 构造传入 |
| 三加载面回填 | `builtin.v1.yaml`（五能力真实字段清单）· `testing.v1.yaml:44` [tool,input,written,note] · `defaults.py:103-157` 硬编码回退面 |
| `nodes.py:104-120,577-640,726-728` | catalog 渲染 output_fields（getattr 宽容兼容旧测 SimpleNamespace）· 计划期裁剪 `_trim_fields_by_output_fields`（只裁字段不拒 plan · 全裁空 pop 键视同空）· span 留痕 `capability_output_fields_trimmed` |
| `tests/test_capability_output_fields.py` | 375 行 12 测 + test_capability_manifest.py:79-81；含运行期生效注册表对拍（ensure_default_capabilities 主路径 + PG 夹具 lookup + 硬编码回退面三钉，R1 B1'） |

## 三、验收核验（5 条全 PASS）

| 验收 | 结果 |
|---|---|
| ① catalog 含清单 + 未声明能力逐字节零 diff | PASS（单测） |
| ② 清单外字段裁剪+留痕 / 清单内零 diff | PASS（单测） |
| ③ 运行期注册表对拍防漂移 | PASS · builtin.v1.yaml get_issue_by_number output_fields 与 lookups.py:69-89 逐键一致 |
| ④ ruff 钉版绿 + 全量零新红 | PASS · 28F/1938P/3s（=1926+12 计账闭合 · junitxml 红单对拍新红 0） |
| ⑤ 40 live 复跑 #2140 query | PASS · run 1039c1a9 seq3 t1 produces=[number,title,state,html_url,updated_at,labels,body] 完全收敛真实字段；t2 执行+done{resumed} 经两个下游独立 bug 修复（PR #295/#296）后同 run 闭合；维护者 m00729 签收 |

## 四、偏差与照登

1. **R1 BLOCKED 照登**：B1 漏 builtin.v1.yaml 主加载面（defaults.py:159-173 ensure_default_capabilities 优先 YAML，_DEFAULT_SPECS 仅回退）→ task 六处回填（8cd8584）后通过；范围未实质扩大无需重签。
2. **Docker daemon 停摆插曲**：隔夜全量 46F/1738P 假红失真，根因 daemon 停止致 DB 缺失；拉起后复跑 28F/1938P 与基线对齐。教训：全量对账前先核 docker 容器水位。
3. **验收 5 首跑撞两个独立下游 bug**：NO_PROXY 小写键漏洗（→ fix PR #295）与 HITL 审批单 thread_id 空（→ fix PR #296），均另立 fix task 闭合，本 task 不背锅不越界。
4. **SSH 推送 transient**：ssh.github.com:443 经 Clash fake-ip 被 reset，fallback HTTPS+gh token 成功；次日链路自愈。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| task B（闸判定3 produces 收窄+重发前驱步逃生口） | `docs/tasks/active/task_lg_rag_gate_produces_unfulfilled.md` 草案仍 pending，维护者裁决 |
| MCP/远端能力无法静态声明 | 空=不校验退回现状（task failure_paths 已声明） |
| manifest output_schema 语义 | 与 output_fields 分工已在 types.py 注释注明 |

## 六、维护者 checklist

- [x] 验收 5 条核验完毕（①-④ 单测/对账 · ⑤ live 维护者签收）
- [x] 00 delegate-only 纪律核验（本窗零实现码 · 20/30 全委派）
- [x] 闸真值落闸表（HG-AUDIT-R1 维护者签收 00 转录）
- [x] R1 审查文随分支入库（8cd8584）
- [x] CI 4/4 绿 · PR #294 合并（squash bfed4cd）
- [x] 归档 done/ · README 登记 · 50 invoke 落盘
