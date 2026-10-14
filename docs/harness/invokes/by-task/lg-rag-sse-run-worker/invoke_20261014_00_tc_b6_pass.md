# invoke · 00 · TC-B6 PASS 收口 · lg-rag-sse-run-worker

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-14 |
| **帽** | 00（delegate-only · 未改实现码 · 未 commit · 未 CLOSE） |
| **前置** | [40](775d4b5c-0c56-4bed-8382-7a2163ac2576) · `invoke_20261014_40_verify.md` |

## 阶段结论

| 项 | 状态 |
|----|------|
| TC-B6 live | **PASS**（断连→worker 续跑→replay 200 普通 `done` · 主样本 `71d3cdfb…` max_seq=445） |
| 409 保护区 | **PASS** |
| pytest / verify | 92 passed · VERIFY PASS |
| 旧 disconnect task | 正文未改 · **待 co-CLOSE**（TC5 known-gap / 随 B 语义同批） |
| D3 web | **未开**（须另仓 task：部分回复 +「继续回复」CTA） |
| TC-B3/B5 | 30 未全勾 · 可另薄棒或 CLOSE 前补 |
| git | **未 commit** · 分支 `task/lg-rag-sse-run-worker` |

## 待维护者一句

1. **commit + 开 PR**（api Wave B）  
2. **开 web D3 task**（CTA）  
3. **同批 CLOSE** 旧 `disconnect_completion` + 本 task（TC5 标 known-gap）  
4. 是否补 **TC-B3/B5** 薄 30  

本窗未改实现码 · 待派：等维护者令
