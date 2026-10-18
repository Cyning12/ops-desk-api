# CLOSE：ruff-baseline-cleanup（A1 · ruff 存量基线漂移收口）

> 关账日期：2026-10-18 · 关账人：00（维护者授权 m01131「合并」）
> 体例承 [close_hitl_resume_async_20261015.md](close_hitl_resume_async_20261015.md)

## 一、任务信息

| 项 | 值 |
|---|---|
| task | [task_ruff_baseline_cleanup.md](../done/task_ruff_baseline_cleanup.md)（已归档 done/） |
| 性质 | 代码质量基线收口（lint/format 机械修复 + 24 处人工裁定 · 含 CI 改动） |
| 上游 | 维护者 m01071「开始A1」· 2026-10-17 晨审计遗留（F811×4 → 扩散至 52 errors） |
| PR | [#274](https://github.com/Cyning12/ops-desk-api/pull/274) MERGED · squash `b73bb8a` · CI 4/4 绿 · 235 文件 +2635/−2920 |
| 审查 | R1 [task_ruff_baseline_cleanup_audit_R1_20261018.md](../../harness/reviews/task_ruff_baseline_cleanup_audit_R1_20261018.md) 签收零阻塞 nit×1 已顺手精化 |
| 闸 | HG-TASK-DRAFT/HG-AUDIT-R1 approved（维护者 m01101「全A」授权 00 代录 · 签注三项裁定）· HG-GRAPH-MODULES n/a |

## 二、交付清单（30 棒 · 7 commits）

| commit 组 | 内容 |
|---|---|
| docs 三件套 | 任务档+10/20 invoke+审查文归档 |
| F1 自动修 | `ruff check --fix` 28 处（I001×9/SIM117×7/SIM300×4/UP035×3/F401×2/UP045×2/UP034×1）逐类复核零语义变更 |
| F2 人工裁定 | 24 处：F811×9 裁定表（全 IDENTICAL 删先定义死码 262 行）· C408×7 · C401×1 · N814×1（去别名直接用 GenericHttpAdapter）· N818 noqa 留痕 · E402×5 分治 |
| F3 format 收口 | `710521c` 纯机器产物 223 文件一次收口（review 可整 commit 跳过）· `66a36eb` noqa 位移修正单列 |
| F4 CI 接闸 | pytest.yml Ruff 段生效 · 钉 `ruff==0.15.21`（消 R1 nit N1 · 禁 >=0.5,<1 漂移） |
| F5 留档 | [invoke_20261018_30_ruff_cleanup.md](../../harness/invokes/by-task/ruff-baseline-cleanup/invoke_20261018_30_ruff_cleanup.md)：statistics 前后对比+F811 裁定表 |

## 三、验收核验（TC-RC-1~8 全 PASS · 零假绿）

| 指标 | 前 | 后 |
|---|---|---|
| `ruff check app tests` | 52 errors（13 类） | **0 errors** |
| `ruff format --check` | 223 would reformat / 103 ok | **326 already formatted** |
| 本地 pytest | 19 failed / 1828 passed | 19 failed / 1828 passed（红集逐名全等 · 零新增红 · 1828=1828 证删的是从未运行的遮蔽死码） |
| CI | ruff 段注释未接闸 | 4/4 绿 · pytest 2m28s 含新 Ruff 步骤（装 ruff==0.15.21 实证） |

## 四、偏差与照登

1. worktree 初无 .env 曾跑 4 红（缺 SILICONFLOW_API_KEY · 纯环境差 · FP-6 按环境抖动路径关闭 · 拷入 .env 复刻基线后逐名全等）。
2. F3 format 连锁 noqa 位移 ×1（单列 commit 66a36eb 隔离）。
3. ruff 版本全程 0.15.21 未动（uv.lock:1831-1835 钉版遵守）。

## 五、遗留移交

| 项 | 去向 |
|---|---|
| N818 CircuitOpen 改名 | 公开异常名变更属 API 语义 · 本 task noqa 留痕 · 如需改名另立 task |
| CI ruff 闸已生效 | 后续 PR ruff 不过即红 · 存量面已清零，防回归闭环 |

## 六、维护者 checklist

- [x] 验收核验完毕（TC-RC-1~8 全 PASS 零假绿）
- [x] F811 九对逐字节比对 IDENTICAL · 裁定表留档
- [x] format 独立 commit 零手改混入
- [x] CI 接闸钉版 ruff==0.15.21 · PR 实证绿
- [x] PR 合并（squash b73bb8a）· 归档 done/ · README 登记 · 50 invoke 落盘
