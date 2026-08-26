# doc-health · 试点镜像（ops-desk-api）

> **角色**：本仓为 **dsh-coding-kit「文档健康度 + CLOSE 强绑定」** 的 **试点 / FEEDBACK** 落点。  
> **契约真值**：不在本夹维护全文 —— 真值在 kit：  
> `dsh-coding-kit/docs/spec/doc-health/`（本机常见：`Desktop/Projects/dsh-coding-kit/docs/spec/doc-health/`）。  
> **状态**：kit **1.7.1 已 npm 发版** · SPEC 已签收（本夹镜像对齐 1.7.0 CLOSE 闸 + 1.7.1 Starter `00-orchestrator.md`）。  
> **Open Folder**：日常 CLOSE / 升级 dogfood → 本仓；改闸实现 → kit。本夹 **不**授权改 `app/`。

---

## 一句话

在 api 关账、升级 kit 时：按本夹 `process/` 执行 W0 纪律；把摩擦与缺陷写入 `feedback/`，方便与 kit 维护者对齐新版本验证。

---

## 读序

1. 本文件（试点边界）  
2. [`process/agent_close_discipline.md`](./process/agent_close_discipline.md) — CLOSE 同棒清单（仓内可执行）  
3. kit 真值包（签收 / 波次 / DoD）：打开上述 kit 路径 README  
4. 验版反馈：[`feedback/README.md`](./feedback/README.md)

---

## 目录

```text
docs/spec/doc-health/
├── README.md                          # 本文件 · POINTER
├── process/
│   └── agent_close_discipline.md      # W0 纪律（本仓可执行副本）
└── feedback/
    ├── README.md                      # FEEDBACK 轨说明
    └── _TEMPLATE.md                   # 单条反馈模板
```

---

## 与 kit 1.7.1 拍板对齐（摘要）

| 项 | 口径 |
|----|------|
| dry-run（无 `--yes`） | **`CLOSE: READY`**（不是完成态） |
| `--yes` 成功 | **`CLOSE: PASS`**（仅此时可写关账完成） |
| PR | 默认 `close_pr_merged`：须 PR **MERGED**；豁免 `close_pr_policy=exempt` + note 或 `--allow-no-pr-merge` |
| Hub | **默认开**（本仓已有 `docs/tasks/done/README.md`）；关账前 Hub 须含本 task 文件名；仓级关闸：`.cyning-harness/local.json` `close_hub_gate: false` 或 `--allow-no-hub` |
| 裸 SPEC warn | `check` 对 `docs/spec/SPEC-*.md` 打 WARN（不挡）；见 [`../README.md`](../README.md) 历史债表 |
| 1.7.1 Starter | `docs/harness/prompts/00-orchestrator.md`（00 默认行为；**不**进默认 Skills） |

---

## 非范围

- 不在本夹复制 kit 全文（防双源漂移）；契约变更只改 kit，本 README 可补一行 POINTER 修订。  
- 不签发 `HG-SPEC-SIGNOFF`。  
- 不改生产 `app/`。  
- 不搬迁根级历史裸 SPEC（仅 WARN / 索引表）。

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-08-26 | 立试点镜像 · POINTER + process + FEEDBACK |
| 2026-08-26 | 对齐 kit **1.7.1 已发版** · SPEC 已签 · READY/PASS / Hub / PR |
