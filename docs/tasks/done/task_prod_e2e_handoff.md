# Task：生产联调移交修复（F2 model 空串 + Nginx index no-cache）

> **状态**：completed  
> **类型**：紧急修复（fix/ 分支）  
> **关联**：`app/config.py` · `ops-desk-workspace/deploy/docker-compose.prod.yml` · `ops-desk-web/docs/acceptance/prod-e2e-2026-07-25.md`

---

## Harness 元信息

| 字段 | 值 |
|---|---|
| **task_slug** | `prod-e2e-handoff` |
| **test_strategy** | `required` |
| **test_strategy_note** | 单测：`OPS_LLM_MODEL=""` 空串回退默认模型 |
| **code_quality_bar** | `L2_backend` |
| **orchestration** | 单 task |
| **git_branch** | `fix/prod-e2e-handoff` |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---|---|---|---|
| **HG-GRAPH-MODULES** | approved | **30** | 配置默认值修复，不涉及模块边界 |
| **HG-AUDIT-R1** | approved | **30** | 生产联调终报移交缺陷，用户指示处理（2026-07-25） |

---

## 背景与目标

Web 生产联调终报移交：

- **F2**：Chat `done` 事件 `model: ""` —— 生产 compose 注入 `OPS_LLM_MODEL=`（空串），pydantic 校验器只认 `None`，空串绕过默认值回退。修复：校验器改为 falsy 判断；compose 移除该行。
- **Nginx 观察项**：`location /` 补 `index.html` no-cache（当前无 Cache-Control，SPA 入口可能被缓存）。
- **F1（核查结论，不改码）**：`module_matrix` 44 条源快照全 NULL，属历史数据真空，前端空态已覆盖。

**完成态**：

- [x] config 空串回退 + 单测
- [x] compose 移除 `OPS_LLM_MODEL` 行
- [x] Nginx conf 补 index no-cache + 重载
- [x] 重新部署 api + 验证 done.model 非空
- [x] invoke 落盘 + `harness task close` 归档

---

## 验收标准

- [x] `pytest tests` 通过（含空串单测）
- [x] 生产 Chat `done` 事件 model 为实际模型名
- [x] `https://www.cynaya.cn/index.html` 响应带 no-cache 头

---

### 自检结论（执行者）

- `pytest tests` 87 passed（新增 `test_settings_empty_model_falls_back_to_default`）。
- 生产验证：`done` 事件 `model: deepseek-ai/DeepSeek-V4-Pro` ✅；index.html `Cache-Control: no-cache` ✅。
- F1 核查：`module_matrix` 全 44 条 NULL（源数据真空），不改码。

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-07-25 | 生产联调终报移交 F2 + Nginx 观察项修复 |
| 2026-07-25 | 接手补 invoke/R1 review，harness task close 归档 |
