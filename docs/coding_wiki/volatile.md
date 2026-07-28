# coding_wiki · volatile

> **层**：volatile · **当前 active task** 专属；关账后清空或归档要点

## 相关页

- 稳定层：[[stable]]
- 项目层：[[context]]

## 本波 active

（关账后清空）无 active · 上一波已 CLOSE：`harness-upgrade-2-18-migrate` · `wikitrack-enable-p0` · `harness-upgrade-2.19.0`（PR #22）

## 执行帽速链

- Active tasks：`../tasks/active/`
- WikiTrack RUNBOOK：[`../harness/RUNBOOK_wikitrack_enable_obsidian_v1_zh.md`](../harness/RUNBOOK_wikitrack_enable_obsidian_v1_zh.md)

## 关账后

- 可复用条目 → 晋升 [[context]] / [[stable]]（仍只写指针，不双份正文）
- 本表清空，避免下一 task 读到 stale volatile
