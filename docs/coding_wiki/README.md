# coding_wiki · ops-desk-api 入口（WikiTrack 已启用）

> **单份真值**：正文仍在 `docs/standards/`、`docs/deployment/`、`docs/_tech_graph/` 等原路径。  
> **本目录**：LLM / Obsidian 读序与互链入口，**不复制**业务正文。  
> **目录约定**：v2.18.2 **recommended** 两层（根读序 + 三件套 + `topics/`）；**不是** close 硬闸。  
> **Obsidian**：Open folder as vault → **`docs/coding_wiki/`**（推荐）。勿开上级 `docs/`（tasks/invokes/reviews 会刷出大量孤点）。

## 默认两层

```text
docs/coding_wiki/
  README.md · _index.md · stable.md · context.md · volatile.md
  topics/          # 主题薄页（指针 docs/**）
```

| 文件 | 层 | 说明 |
|------|-----|------|
| [[_index]] | 索引 | 主题→页 |
| [[stable]] | stable | 会话短摘要 · 编码底线 · IDE |
| [[context]] | context | 项目级指针（规范 / 图谱 / 部署） |
| [[volatile]] | volatile | 当前 active task 必读 |
| [[topics/wiki_layout]] | 主题 | 两层目录约定（本仓） |
| [[topics/wikilinks_export]] | 主题 | wikilink / export |

**原则**：根禁主题长文；勿按日期/PR/task_slug 建目录；`wiki export` 不依赖深度。加深阈值（md≥15 / 难扫 / 单页>~80 行 / 连续 3 task 同前缀）见 [[topics/wiki_layout]]。

## 关账约定（v2.18+）

1. 新 task 填 **`wiki_delta`**：`path` / `none`+note / **勿再默认 `n/a`**。  
2. `experience_capture=required` 且 `wiki_delta=path` → 经验节含 `Wiki:` / `wiki_promoted:` / `coding_wiki`。  
3. 目录形状本身 **不**挡 close（recommended）。

## 验证

```bash
npx dsh-coding-kit wiki export --json --target .
#（原钉 @cyning/harness@2.19.0；dsh-coding-kit ≥1.6.1 wiki 子命令参数面兼容，2026-08-25 实证 exit 0）
# 期望：nodes≥6 且 edges>0
```
