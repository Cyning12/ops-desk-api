# Task：临时 health 探针（部署可辨）

> **状态**：ready  
> **类型**：临时探针（docs + 极小 API 面）  
> **关联**：生产 `./deploy.sh --skip-web` 冒烟 · 验完须回滚去掉 probe 字段

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `health-temp-probe` |
| **git_branch** | `fix/health-temp-probe` |
| **graph_change_layer** | `none` |
| **review_hat** | `20` |
| **thinking_profile** | `shortest` |
| **invoke_retention_profile** | `minimal` |
| **required_invoke_hats** | `30` |
| **test_strategy** | `required` |
| **test_strategy_note** | `pytest tests/test_health.py` |
| **code_quality_bar** | `L2_backend` |
| **orchestration** | 单 task；维护者当面指示临时探针 |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 维护者当面：仅 `/health` 增字段；不改模块边界 |
| HG-TASK-DRAFT | approved | 22-R1 | 维护者 2026-07-28：先来做个临时探针 |
| **HG-AUDIT-R1** | approved | **30** | 维护者当面：临时可辨探针；验完回滚 |

---

## 背景与目标

生产部署后 `/health` 仅 `{"status":"ok"}`，无法确认镜像是否更新。临时在响应中增加可辨字段。

**完成态**：

- [x] `GET /health` 含固定 `probe` 字段（如 `20260728-a`）
- [x] `tests/test_health.py` 更新
- [ ] commit → push → PR（部署与回滚由维护者执行）

**不做**：GHA 自动部署、正式 version/sha 方案、改其它业务接口

---

## 失败路径

| 触发 | 行为 | 可重试 |
|---|---|---|
| 探针合入后忘记回滚 | 开 follow-up 去掉 `probe` | 是 |

---

## 验收标准

- [x] `GET /health` → `status=ok` 且含约定 `probe`
- [x] `pytest tests/test_health.py` 绿
- [x] 未改 `app/ops/**` 业务路由

---

### 自检结论（执行者）

| 项 | 内容 |
|---|---|
| **日期** | 2026-07-28 |
| **probe** | `20260728-a` |
| **pytest** | `tests/test_health.py` 1 passed |
| **verify** | PASS |
| **下一棒** | PR → `deploy.sh --skip-web` → curl → 回滚删 probe |
