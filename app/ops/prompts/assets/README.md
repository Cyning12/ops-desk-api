<!-- prompt 资产目录 · task prompt-asset-roadmap-p1 · SPEC prompt-asset-roadmap §2 D3 -->
# Prompt 资产（app/ops/prompts/assets/）

产品面 LLM prompt 的真值目录：每模板一个 `<template_id>.md`，front-matter 载
`template_id` / `version`（`v<N>` 格式），正文即 body。运行时由
`app/ops/prompts/loader.py` 读取，缺文件 / 缺字段 / 空 body / version 格式非法
**显式炸不静默降级**。

## 非开发改文案操作路径

1. 只改目标模板的 `<template_id>.md` **正文**（渲染语法 `string.Template`：
   变量写 `$name`，JSON 示例**裸写**花括号，禁止双写花括号转义与新增 `$`）；
2. **同 PR bump front-matter `version`**（v1 → v2…）：body 变更必须伴随
   version bump，否则版本号成为假信号（阶段二「看得见」归因依赖）；
3. 提 PR —— diff 到单个 md 即文案变更的机械审计证据；
4. CI 锚点断言兜底（结构锚点存在 + 零转义残留 + 零游离 `$`），非全文快照，
   正常改文案不挂 CI，改变量名 / 留转义必挂；
5. 合入即上线（运行时读文件，随包分发）。

## 变量集合（一字不改 · 调用方契约）

| template_id | version（迁移起点） | 变量 |
|---|---|---|
| lg_rag.intent.system | v1 | 无 |
| lg_rag.supervisor.system | v2 | `$catalog_block` |
| lg_rag.supervisor.suffix.system | v1 | `$catalog_block` `$prefix_block` `$suffix_cap` |
| lg_rag.router.system | v1 | 无 |
| lg_rag.direct.system | v1 | 无 |
| lg_rag.rewrite.system | v1 | 无 |
| lg_rag.extract.system | v1 | 无 |
| lg_rag.aggregator.system | v1 | 无 |
| memory.extract.system | v4 | 无 |
| session.summary.system | v1 | 无 |

新增变量 = 改调用方代码，属开发变更，不走本目录文案路径。
特例（本目录不覆盖 · SPEC 设计纪律 3）：`rag/grader.py`（env 切版实验面）·
`lc_evidence_chain/answer.py`（外置 yaml）· `prompts/packs.py`（harness 纪律 SoT）·
`chat/nodes.py`（legacy 已 410）。
