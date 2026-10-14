# invoke · 00 · 阶段收口（api Wave B + web D3）

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 00（delegate-only · 未 commit · 未 CLOSE） |

## 双仓状态

| 仓 / task | 验收 | git |
|-----------|------|-----|
| api `task_lg_rag_sse_run_worker` | B1–B6 + B3/B5 **PASS**（TC-B6 live PASS） | 分支 `task/lg-rag-sse-run-worker` · **未 commit** |
| web `task_web_lg_rag_sse_continue_reply` | TC-W1–W7 **PASS**（[40](1f8e4eb3-ada4-4d8b-a30c-a2da101d628b)） | 分支 `task/web-lg-rag-sse-continue-reply` · **未 commit** |
| api 旧 `task_lg_rag_sse_disconnect_completion` | 正文未改 · TC5 known-gap · **待 co-CLOSE** | 另分支脏树 |

## 仍等维护者令

1. **commit + PR**（api / web 可分 PR）  
2. **同批 CLOSE** 旧 disconnect + run_worker（+ web D3 可同波或紧随）  
3. 可选：跨仓 **joint-check**（非 D3 本身；两边交付后另开）

本窗未改实现码 · 待派：无 · 阻塞：维护者令
