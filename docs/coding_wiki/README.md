# coding_wiki · ops-desk-api 入口（WikiTrack 已启用）

> **单份真值**：正文仍在 `docs/standards/`、`docs/deployment/`、`docs/_tech_graph/` 等原路径。  
> **本目录**：LLM / Obsidian 读序与互链入口，**不复制**业务正文。  
> **Obsidian**：Open folder as vault → 仓内 `docs/`（推荐）或仅本目录。

| 文件 | 层 | 说明 |
|------|-----|------|
| [[stable]] | stable | 会话短摘要 · 编码底线 · IDE |
| [[context]] | context | 项目级指针（规范 / 图谱 / 部署） |
| [[volatile]] | volatile | 当前 active task 必读 |

## 关账约定（v2.18+）

1. 新 task 填 **`wiki_delta`**：`path`（改了入口或某份真值文档）/ `none`+note / **勿再默认 `n/a`**（本仓已启用）。  
2. `experience_capture=required` 且 `wiki_delta=path` → 经验节含 `Wiki:` / `wiki_promoted:` / `coding_wiki` 路径。  
3. 导出：`npx @cyning/harness wiki export --json --target .`

## 验证

```bash
npx @cyning/harness@2.18.1 wiki export --json --target .
# 期望：nodes≥4 且 edges>0（stable/context/volatile/README 互链）
```
