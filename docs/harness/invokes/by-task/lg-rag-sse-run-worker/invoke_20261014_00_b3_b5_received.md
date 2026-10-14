# invoke · 00 · 收 B3/B5 薄棒

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 00 |
| **前置** | [30 B3/B5](895dccf6-bfd1-4a01-b9c9-e45c878979e6) · `invoke_20261014_30_b3_b5.md` |

## 收口

| TC | 结论 |
|----|------|
| B3 | **PASS**（continue_from 新 stream · 零 resume） |
| B5 | **PASS**（orphan 补偿 `done{disconnected}` · 活跃 worker 跳过） |
| B6 | 已 PASS（前棒） |
| B10 co-CLOSE | 仍 open |
| D3 web | 实现 task 起草中/待跟 · **非联调** |
| commit | 未 |

补偿扫描须显式调用（未挂 lifespan）— 记残差，不阻塞本棒收口。

## 跟进

- api B3/B5：**已收 PASS**（无须再派 40；测面已钉）
- web D3：前棒 10 仅切分支未落稿 → **00 重派 web-10** 完成 `task_web_lg_rag_sse_continue_reply`

本窗未改实现码 · 已派/待派：web-10 · 其余等令（commit·PR / co-CLOSE）
