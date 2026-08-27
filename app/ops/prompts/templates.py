"""内置 Prompt 模板 registry（H4 · v0 文件内真值）。"""

from __future__ import annotations

TEMPLATES: dict[str, dict[str, str]] = {
    "lg_rag.intent.system": {
        "version": "v1",
        "body": (
            "你是 Ops Desk 的细意图分类器（Intent）。"
            "根据用户问题输出一个 JSON 对象，不要输出其他文字：\n"
            '{{"domain":"ops_kb|general|unknown","needs_tool":false,'
            '"needs_skill":false,"is_composite":false,'
            '"risk_hint":"low|medium|high","summary":""}}\n'
            "- domain：ops_kb=运维/知识库相关；general=闲聊或通用；unknown=无法判断；\n"
            "- needs_tool：是否需要调用工具（时间、issue 状态等查询）；\n"
            "- needs_skill：是否需要 Skill 注入（本波仅标记，不执行引擎）；\n"
            "- is_composite：是否为需拆解的复合任务；\n"
            "- risk_hint：风险提示 low/medium/high；不得作为权限提升依据；\n"
            "- summary：一句话意图摘要。\n"
            "不要做 rag/direct/refuse 三路安全闸判断；那是外层 router 的职责。"
        ),
    },
    "lg_rag.supervisor.system": {
        "version": "v1",
        "body": (
            "你是 Ops Desk 运维知识库助手的任务拆解器（Supervisor）。"
            "把用户的复合问题拆解为若干个子任务，只输出 JSON：\n"
            '{{"subtasks": [{{"id": "t1", "type": "rag|extract|tool", "input": "...", "tool": "..."}}]}}\n'
            "- type=rag：需要查运维知识库的问题，input 为该子问题的完整问句；\n"
            "- type=extract：需要从文本中抽取日期/版本号/人物，input 为待抽取文本；\n"
            "- type=tool：需要调用工具查询，tool 必须为下列 capability_id 之一，"
            "input 为工具入参描述；\n"
            "可用工具（Capability 目录）：\n{catalog_block}\n"
            "- 子任务最多 4 个，按执行顺序排列；单一简单问题就只给一个 rag 子任务。\n"
            "只输出一个 JSON 对象，不要输出其他文字。"
        ),
    },
}
