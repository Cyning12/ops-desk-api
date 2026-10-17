# R-5 Demo 证据表模板（rag-knowledge-golden-eval · 路线 §P1-RAG R-5）

> 用途：HG-EVAL-LIVE-RUN approved 后的真跑演示留证。
> 要求：≥4 条记录，四象限（zh2en / zh2zh / en2en / negative）每象限 ≥1 条，
> 且 negative 象限至少 1 条完整拒答演示。
> 每条证据必须可复现（给出复现命令）；贴图/日志放 reports/ 或本文件内联摘要。

## 记录 1 · `<象限 zh2en>`

- **版本 / commit**：`<git 短哈希 + 分支>`
- **输入 query**：`<用户问题原文>`
- **结果摘要**：`<gate_action=answer/answer_partial/refuse；回答要点 1-2 句>`
- **引用**：`<[source_type/source_id/title] 列表，每条 relevance 档级>`
- **错误与降级**：`<无 / 超时 / provider 降级 / 部分证据提示等>`
- **复现命令**：`.venv/bin/python evals/golden/run_eval.py --only <G-id> --report reports/<run>.yaml`

## 记录 2 · `<象限 zh2zh>`

- **版本 / commit**：`…`
- **输入 query**：`…`
- **结果摘要**：`…`
- **引用**：`…`
- **错误与降级**：`…`
- **复现命令**：`…`

## 记录 3 · `<象限 en2en>`

- **版本 / commit**：`…`
- **输入 query**：`…`
- **结果摘要**：`…`
- **引用**：`…`
- **错误与降级**：`…`
- **复现命令**：`…`

## 记录 4 · `<象限 negative · 拒答演示>`

- **版本 / commit**：`…`
- **输入 query**：`<语料外问题>`
- **结果摘要**：gate_action=refuse；拒答文案须与契约 4c 完全一致：
  「未查询到相关内容，无法针对此问题进行回答」
- **引用**：无（拒答不出引用卡）
- **错误与降级**：`…`
- **复现命令**：`…`

---

## 填表纪律

- 证据来自真跑（run_eval.py 或 chat SSE 实际调用），不得编造；无实证处写「照登：无实证」。
- 与结案报告交叉引用：每条记录注明对应 `reports/r4_final_<run>.yaml` 中的 case id。
- 若演示中发现新漂移/缺陷 → 记录于结案报告「契约漂移」或「未达成项」，走 FP-5 上抛，不在本表内顺手修。
