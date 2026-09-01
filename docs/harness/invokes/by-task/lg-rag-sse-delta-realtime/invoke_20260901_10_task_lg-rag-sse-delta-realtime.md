# Invoke：10-task · lg-rag-sse-delta-realtime

| 字段 | 值 |
|---|---|
| hat_id | 10-task |
| task_slug | `lg-rag-sse-delta-realtime` |
| task_paths | `docs/tasks/active/task_lg_rag_sse_delta_realtime.md` |
| git_branch | `task/lg-rag-sse-delta-realtime` |
| created_utc_or_local | 2026-09-01 |

## 裁决

- 落实 §10.4.1：主修 **persist 不阻塞 yield**；默认不攒批；协议零变。  
- 验收锚 = mock 慢 chunk（节点结束前可见 delta）+ T5 不回归。  
- 本帽不签发 HG-AUDIT-R1。

## 交付

- task 结构齐全（验收 / failure_paths / 非范围 / wiki_delta）  
- 下一棒：**20-task-audit**

## 签收栏

（待 20 审查）
