---
name: ops-desk-tech-graph
description: Ops Desk 子项目接入 cyning-harness、生成/维护技术图谱、并在代码变更后检查图谱完整性的标准流程。
triggers:
  - 新增子项目需要接入 harness
  - 新增路由、表、事件类型、LangGraph 节点
  - 修改 chat / auth / sync / issues / pulls / overview 模块
  - 需要检查图谱是否与代码同步
  - 用户提到 "图谱"、"tech graph"、"harness"、"01_struct"、"graph.yaml"
---

# Ops Desk 技术图谱维护流程

## 适用范围

Ops Desk 四仓库：

- `ops-desk-workspace`（总图）
- `ops-desk-api`（后端）
- `ops-desk-web`（前端）
- `ops-desk-ios`（iOS）

## 1. 新子项目首次接入

### 1.1 初始化 harness 骨架

在子项目根目录执行：

```bash
npx @cyning/harness init --preset harness-only --ide cursor,claude,agents --yes
```

### 1.2 创建项目级 settings.json 放开 npx 权限

`.claude/settings.json`：

```json
{
  "permissions": {
    "allow": [
      "Bash(npx @cyning/harness *)"
    ]
  }
}
```

### 1.3 创建/恢复真实图谱内容

必须存在且符合 `inform_graph.v3` schema 的文件：

- `docs/_tech_graph/00_main.graph.yaml` — 顶层总图
- `docs/_tech_graph/01_struct.md` — 模块边界表（人签真值）
- `docs/_tech_graph/02_version.md` — 版本时间线
- `docs/_tech_graph/99_mermaid_protocol.md` — Mermaid 约定
- 至少一条主 flow：`docs/_tech_graph/10_flow_*.graph.yaml`

### 1.4 配置编译脚本

`scripts/graph-compile.sh`：

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
npx @cyning/harness graph yaml compile --input docs/_tech_graph --all
python3 scripts/graph_yaml_to_json.py docs/_tech_graph
npx @cyning/harness graph yaml check --input docs/_tech_graph --all
```

`scripts/graph_yaml_to_json.py`：用于生成兼容 harness v2 check 的 `graph.json`。

### 1.5 首次编译并校验

```bash
./scripts/graph-compile.sh
```

输出应包含：

```text
OK: 00_main
OK: 10_flow_xxx
```

### 1.6 人签 HG-GRAPH-MODULES

在 `docs/_tech_graph/01_struct.md` 中填写一级模块表，维护者签核后将 `HG-GRAPH-MODULES` 状态改为 `approved`。

---

## 2. 代码变更后维护图谱

### 2.1 必须同步更新图谱的场景

每次新增/修改以下任意一项，都必须先改 `docs/_tech_graph/*.graph.yaml`，再改代码：

- REST Endpoint（路径、方法、请求/响应字段）
- SSE 事件类型或 payload
- 数据库表或关键字段
- LangGraph 节点、边、state 字段
- 模块间调用关系
- 外部依赖（LLM Provider、数据库、第三方 API）

### 2.2 增量维护步骤

1. 改 `.graph.yaml` 源文件（唯一人工编辑源）。
2. 运行 `./scripts/graph-compile.sh` 生成 `.md` + `graph.json`。
3. 确认 check 通过。
4. 提交 `.graph.yaml` + `.md` + `graph.json`。

### 2.3 禁止事项

- ❌ 直接手写生成的 `.md` 文件。
- ❌ 改代码后忘记改图谱。
- ❌ 在 `site-packages` 改依赖源码来规避图谱约束。

---

## 3. 图谱完整性检查

### 3.1 手动检查

```bash
./scripts/graph-compile.sh
```

### 3.2 CI 检查（推荐）

`.github/workflows/tech-graph.yml`：

```yaml
name: tech-graph

on:
  pull_request:
  push:
    branches: [main]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v5
        with:
          node-version: "24"
      - name: Check tech graph
        run: |
          npm install -g pyaml
          ./scripts/graph-compile.sh
```

### 3.3 自动 Hook 检查（可选）

`.claude/settings.json` 中添加 PostToolUse hook，在 Write/Edit 涉及代码或图谱后自动校验：

```json
{
  "permissions": {
    "allow": ["Bash(npx @cyning/harness *)"]
  },
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_response.filePath // .tool_input.file_path' | { read -r f; case \"$f\" in app/*|docs/_tech_graph/*|scripts/*) ./scripts/graph-compile.sh ;; esac; } 2>/dev/null || true",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

---

## 4. 子项目图谱职责

| 子项目 | 图谱重点 |
|---|---|
| `ops-desk-api` | FastAPI 路由、LangGraph、DB 表、SSE 事件契约 |
| `ops-desk-web` | 页面路由、组件、Pinia store、API client、SSE 事件处理 |
| `ops-desk-ios` | SwiftUI 页面、网络层、SSE 解析 |
| `ops-desk-workspace` | 四仓库关系、数据流、部署拓扑、跨端契约 |

---

## 5. 快速检查清单

在关账每个 task 前确认：

- [ ] 代码改动是否涉及路由/表/事件/节点？
- [ ] 对应的 `.graph.yaml` 是否已更新？
- [ ] `./scripts/graph-compile.sh` 是否通过？
- [ ] `01_struct.md` 模块边界是否需要调整？
- [ ] 是否生成了 invoke 落盘？
