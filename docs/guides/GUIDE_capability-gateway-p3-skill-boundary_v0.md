# GUIDE：Capability Gateway · P3 skill 边界（provide / invoke）

> **状态**：active · **SPEC**：`SPEC-capability-gateway_v0.md` §4 P3  
> **范围**：`kind=skill` 接口预留 + 与 `docs/skills/` 划界；**禁止**完整 Skill 执行引擎

## 两套「Skill」勿混用

| 层 | 路径 / 符号 | 读者 | 做什么 |
|---|---|---|---|
| **仓内人读 Skill** | `docs/skills/*/SKILL.md`（如 `s-l0-project-map`） | 人 / IDE Agent / harness | Markdown 操作说明与读序；**不**经 Gateway 执行 |
| **Capability `kind=skill`** | `app/ops/capability/` · `SkillStubAdapter` | LangGraph 节点 / 运行时 | 注册表条目；`provide` 注入上下文 vs `invoke` 可执行步骤 |

同名「Skill」分属 **文档/流程层** 与 **运行时能力层**。P3 stub 可用 `skill_ref` 元数据指向 `docs/skills/...`，**不**自动加载、解析或执行 `SKILL.md`。

## provide vs invoke

```text
provide(capability_id, *, ctx)  →  注入上下文（说明 / 片段 / 占位）
invoke(capability_id, args, *, ctx)  →  跑可执行步骤（完整引擎 · P3 未实现）
```

| 表面 | P3 stub 行为 |
|---|---|
| `provide` | `ok=True`，返回占位 `context`（`engine=stub`） |
| `invoke` | adapter 抛 `NotImplementedError` → Gateway `ok=False`（不垮调用方） |

## 默认关闭

`ensure_default_capabilities()` **只**注册 `local_fn` mock。  
skill stub **不**写入 defaults。

```python
from app.ops.capability import provide, invoke, register_skill_stub

register_skill_stub(enabled=True)
r = provide("stub_skill_s_l0_project_map", ctx={"node_role": "tool_exec"})
assert r.ok and r.output["mode"] == "provide"

inv = invoke("stub_skill_s_l0_project_map", None)
assert inv.ok is False  # NotImplementedError → ok=False
```

| capability_id | kind | adapter |
|---|---|---|
| `stub_skill_s_l0_project_map` | `skill` | `SkillStubAdapter`（`skill_ref=docs/skills/s-l0-project-map`） |

## 非范围（打回）

- 完整 Skill 执行引擎 / 逐步解释器  
- 改 `app/ops/chat/graph.py`  
- Agently 运行时依赖  
- 真外网 / 真 MCP（属 P2；本波无关）
