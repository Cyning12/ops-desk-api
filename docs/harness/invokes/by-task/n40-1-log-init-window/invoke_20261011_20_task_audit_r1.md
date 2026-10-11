---
hat: 20
task_slug: n40-1-log-init-window
date: 2026-10-11
---

# invoke · 20-task-audit R1 审查 · n40-1-log-init-window（logging 初始化窗口收口）

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 20 |
| task_slug | `n40-1-log-init-window` |
| freeze_id | 无 |
| task_paths | `docs/tasks/active/task_n40_1_log_init_window.md`（commit 17bfaf8） |
| related_review_or_none | `docs/harness/reviews/task_n40_1_log_init_window_audit_R1_20261011.md`（址A · 本棒落盘） |
| git_branch | `task/n40-1-log-init-window`（base master `286d825`） |
| worktree_root | `../ops-desk-api-worktrees/t-n40-1-log-init-window` |
| created_utc_or_local | 2026-10-11 |
| notes | required_invoke_hats=10,20,30,40 含 20 → 本 invoke 必落 |

## 可复制 Prompt 快照

```text
你是 ops-desk-api 仓的 20-task-audit 审查棒（R1）。任务：书面审查 task 草稿
docs/tasks/active/task_n40_1_log_init_window.md。

对照真值：序2 repo-logging-init 的 close 档 N-40-1 原文与后续建议 ·
代码锚点 app/main.py:9-12 import 链 / :18-35 _init_logging 定义 / :38 调用 ·
发射链 app/ops/capability/__init__.py:112 → persistence.py:65-68 WARNING / :48 INFO（亲读复核）。
核对面：范围/非范围/验收标准 TC1–TC4 可机断性（TC1 子进程 import 探针红测先行是核心）/
失败路径四列表/思考轮 R0–R5/闸表契约（4 列 · status 纯 pending）·
graph_change_layer=n/a 的条件触发表述是否自洽（方向 B 抽 logging_config.py 时触发 G-L2 判定）。
10 棒留下的审查要点（逐条过）：A/B 修法裁定倾向是否开放得当 ·
窗口发射点全集排查是否完备（亲 grep 复核 import 期 logging 调用）· 探针 PYTHONPATH 纪律。
纪律：不改 task 实质内容（实质问题 BLOCKED 退回 10-task）；不代签 human_gate。
产出：审查文落盘 docs/harness/reviews/task_n40_1_log_init_window_audit_R1_20261011.md（址A 硬步骤）·
20 invoke 落 docs/harness/invokes/by-task/n40-1-log-init-window/ · commit（docs(review): 前缀）不 push。
```

## 交付摘要（本帽结束时填）

- **裁定**：**PASS-WITH-NITS**（零内容阻塞 · N-1~N-4 非阻塞照登 · 三闸 pending 未代签 · 审查文文末为维护者签闸清单 · 未附 30 Prompt）
- **验证命令 + 退出码**（本帽亲跑 · PYTHONPATH=$PWD · 主仓 venv python · base 码面）：
  - 显式清 `OPS_CAPABILITY_PERSISTENCE` 裸 `python -c "import app.main"` → EXIT=0 · stderr 裸格式 WARNING 一行（**TC1 红前提实证**）
  - `OPS_CAPABILITY_PERSISTENCE=db` 同探针 → EXIT=0 · stderr 空（**TC2 红前提实证** · db 探针无需真库）
  - `OPS_CAPABILITY_PERSISTENCE=memory` → EXIT=0 · 裸格式 WARNING（persistence.py:54）
  - `OPS_LOG_LEVEL=BOGUS` → EXIT=0 · 格式化 ERROR 告警行存续（TC3 前提实证）
  - 全集排查（root+lastResort 降 DEBUG 复跑 unset/db · app/ grep 零裸模块级 logger 调用）→ 默认 env 面发射点仅 persistence 一处；另钉 env 门控第二发射点 `manifest.py:218` ERROR（`OPS_CAPABILITY_EXTRA_MANIFESTS` 坏文件实证裸发）与理论可达 `manifest.py:827/:840`（REVERSIBILITY_MODE observe/enforce · 当前不发射）——登记审查文 N-2 · 修法发射点无关全覆盖
- **变更路径**：`docs/harness/reviews/task_n40_1_log_init_window_audit_R1_20261011.md`（新增 · 址A）· 本 invoke（新增）
- **下一棒**：交还维护者签 HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 → 30（红测先行 · A/B 裁定留痕 · 图谱按实判回写）
