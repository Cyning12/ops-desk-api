# FRAGMENT · 图谱先读（graph-first · 条件触发）

> 嵌入 00 / 10 / 20 / 30 各帽条文。**条件触发**：仅当仓 profile 声明
> `graph_modules_path` 且路径可达时本节生效；无图谱仓整条跳过，
> 不输出任何图谱指引。无 skill frontmatter（嵌入片段，不入 skills 分发）。

## 生效条件（伪代码）

```text
IF profile(.coding-kit/profile.json → legacy .cyning-harness/profile.json)
   .graph_modules_path 为非空字符串
   AND resolve(仓根, 该值) 是可达目录:
    图谱入口 = <graph_modules_path>/{00_main, 01_struct} + 与本任务相关的 10_flow_*
ELSE:
    本节全部条款不适用；禁止在产物中虚构图谱路径或图谱指引。
```

## 各帽义务（生效时）

- 00（委派）：委派任务书必含「先读图谱」必备条款（图谱路径 + 必读文件清单 + 对拍要求；落点 `FRAGMENT_00_delegate_only_v1_zh.md`）；缺该条款的任务书不得派发。`<GRAPH_MODULES_PATH>` / `<FLOW_FILES>` **禁止留空占位符派发**。
- 10（起草）：SPEC/task 的「必读列表」含图谱入口；验收标准 / failure_paths 涉及图谱声明模块（`01_struct` 模块表）时，标注对应图谱锚点（节点/边 ID 或图谱文件路径）。
- 20（审查）：审查文核对上述图谱引用的真实性（锚点在图谱语料中存在 · grep 级）；缺引用 → 写入阻塞清单退回 10。
- 30（执行）：开工必读列表含图谱入口（沿用既有 30 必读纪律，条件化；task 必读列表 / `AGENTS.md` / L2 涉码强度不降）；涉图谱模块的改动在 invoke/自检中引用图谱锚点对拍。

## verify 行为（以 W2 已测锁为准）

条文描述 verify 时服从已测锁语义，不另造句式：

- 无声明（无 profile，或 `graph_modules_path` 不是非空字符串）：检查步跳过；**零新增输出、零新增 JSON 键**。
- 声明但路径不可达，或词表空：检查步跳过且不挡；inform/warn **显含**「图谱锚点检查未生效（已跳过）」。
- 声明且可达，task 涉图谱模块但 task 文（面A）或 invoke/审查文（面B）缺锚点引用：`VERIFY: BLOCKED · missing graph anchor reference`（点名面A/面B · exit 2）。
- 豁免仅 `--allow-no-graph-anchor`（`waived[]` 留痕）。不新增其他绕过参数。
