---
name: langgraph-chinese-pitfall
description: 检查项目 LangGraph 使用方式是否可能触发内置英文提示词导致中文输出被带偏，并给出修复建议。
triggers:
  - 用户提到 langgraph 中文输出问题
  - 用户提到 create_react_agent / ToolNode / AgentExecutor
  - 新增或重构 chat / agent 模块
  - 引入 langgraph.prebuilt 或 langchain.agents
---

# LangGraph 中文提示词防坑检查

## 检查清单

在修改 chat / agent 相关代码后，执行以下检查：

1. **是否引入了高层 API？**
   - `from langgraph.prebuilt import create_react_agent`
   - `from langgraph.prebuilt import ToolNode, tools_condition`
   - `from langchain.agents import AgentExecutor` 或 ReAct 系列

2. **当前项目状态**
   - 若仅使用 `from langgraph.graph import END, START, StateGraph`，且节点为纯业务函数，则**不受影响**。
   - 若出现上述高层 API，继续下一步。

3. **是否显式覆盖中文 prompt？**
   - `create_react_agent(model, tools, prompt="你是一名乐于助人的助手，所有回答必须使用简体中文。")`
   - 若同时用 `response_format`，prompt 必须以元组传入：
     ```python
     create_react_agent(llm, tools, response_format=("请用中文回答", JsonOutput))
     ```

4. **工具名/描述是否保持英文？**
   - 工具名、工具描述建议英文，避免工具调用解析不稳定。
   - 在中文 system prompt 里说明何时调用哪些工具。

5. **是否直接修改了 site-packages 中的 LangGraph 源码？**
   - 如果有，改为以下可持续方案之一：
     - 优先使用 `StateGraph` 自定义工作流（推荐）。
     - 次选 fork LangGraph 后用 editable install（`pip install -e .`），但需承担合并上游更新成本。

## 修复模板

```python
from langgraph.prebuilt import create_react_agent

CHAT_PROMPT = """
你是一名乐于助人的智能助手，擅长根据用户问题选择合适工具查询信息并回答。
所有回答必须使用简体中文，条理清晰、简洁友好。
"""

graph = create_react_agent(
    model=model,
    tools=tools,
    prompt=CHAT_PROMPT,
)
```

## 常见误区

- ❌ 直接修改 `site-packages/langgraph/*` 源码。
- ❌ 在 `response_format` 场景下直接传字符串 prompt。
- ❌ 工具名/描述用中文，导致 tool calling 不稳定。

## 延伸阅读

- 项目 memory: [[langgraph-chinese-prompt-pitfall]]
- [你好，ReAct特工！——LangGraph的create_react_agent终极生存手册](https://juejin.cn/post/7537588523088822299)
