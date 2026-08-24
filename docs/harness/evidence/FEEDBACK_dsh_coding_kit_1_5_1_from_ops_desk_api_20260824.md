# FEEDBACK · dsh-coding-kit 1.5.1 · from ops-desk-api（harness→kit 过程轨迁移首单）

> **日期**：2026-08-24
> **业务仓**：`ops-desk-api`（FastAPI · WikiTrack 已启用 · G-L 试点）
> **git root**：`/Users/cyning/Desktop/Ops-desk/ops-desk-api`
> **起点**：manifest `2.24.0`（@cyning/harness 已 deprecate）→ 目标 `dsh-coding-kit@1.5.1`
> **对照**：kit README.zh-CN · lib/cli.js 源码实读 · 前波 FEEDBACK 2.24.0
> **分支**：`task/dsh-coding-kit-1-5-1`
> **执行**：30 子 agent · 禁 git commit（00 统一提交）

---

## 1. 结论（验收）

| 项 | 结果 |
|----|------|
| manifest | **1.5.1**（from_version=2.24.0 · preset 保留 fullstack-node-py · ide 保留） |
| 状态目录约定 | kit 沿用 `.cyning-harness/`（manifest 同路径 · 无新目录） |
| AGENTS/CLAUDE local 块 | **完整**（diff 仅 A1 一行/文件 · local 块零字节变化） |
| refresh-ide-blocks 幂等 | **PASS**（二刷 dry-run rewrites=0） |
| upgrade 幂等 | **PASS**（二跑 1.5.1→1.5.1 · from_version 保持 2.24.0） |
| `verify --task <本task>` | 严格态 BLOCKED（缺 R<n> · 缺 pre-30 invoke hat 10 · 均为序内缺口）；`--allow-no-review --allow-invoke-gap` 留痕豁免 **PASS exit 0** |
| graph-compile.sh（harness 面） | **exit 0**（未动 · 仍 npx @cyning/harness） |
| pytest tests -q | 3 failed / 242 passed = 既有基线（chat_ws/chat_router 缺表）· 无新增 |
| severity=block | **无** |

**判定**：harness→kit 1.5.1 过程轨迁移在本仓成立；local 块零手恢复；verify 语义变化（须 --task + R<n>/invoke 硬闸）为**预期收紧**，非不兼容。

---

## 2. kit 1.5.1 CLI 面探查结论（对 harness 2.24 命令记忆）

| harness 旧命令 | kit 1.5.1 对应 | 差异 |
|---|---|---|
| `npx @cyning/harness check` | `npx dsh-coding-kit check` | 同语义；注意版本比较是 semver 数值比较，manifest=2.24.0 vs 包 1.5.1 会报「manifest 版本高于包版本（可能为降级安装）」——**跨产品线迁移时 check 输出误导**，以 `upgrade` 结果为准 |
| `upgrade --target . --yes` | 同名 | **大幅变轻**：只重写 manifest（version/preset/ide/from_version/upgraded_at），**不再全量 cp prompts、不改 AGENTS/CLAUDE/mdc**；无 S5 脏树闸；内嵌 IDE 旧字面 dry-run 提示 |
| （harness upgrade 内嵌 IDE 块替换） | `refresh-ide-blocks [--dry-run|--yes]` | **独立子命令**（R-07）：默认 dry-run 零写入；--yes 有 preflight（git 脏树含 untracked → fail-fast exit 2）；发现面冻结为仓根 AGENTS.md/CLAUDE.md/.cursor/rules/*.mdc 的 product marker 块体内；local 块永不改写；写前备份到 `.cyning-harness/backups/refresh-ide-blocks/<ts>/`（留 5 代） |
| `verify --target . --task FILE` | 同名 | **--task 变为必填**（exit 1「verify 须指定 --task FILE」）；新增硬闸：缺 R<n> review → BLOCKED exit 2（`--allow-no-review` 留痕豁免）；缺 pre-30 invoke hats → BLOCKED（`--allow-invoke-gap` 留痕豁免）；D5 测试制品探测（test_strategy=required 时，tests/ 目录命中即过） |
| `gate-check` / `audit` / `task lint` / `task lint-wiki-delta` / `task close` | 同名 | 存在（未全量复验 · 仅 --help） |
| `graph yaml compile/check/export` | **kit 自带** `graph yaml compile|check|export` + `graph ingest|snapshot|axioms` | 参数面同形（--graph-id/--target/--input/--output/--all/--no-recursive/--graph-json）；**命令面切换可行性前置满足**，留 probe task 做行为等价验证 |
| init | `init --preset harness-only` | preset 词表当前唯一合法值 `harness-only`；fullstack-node-py 等 harness preset 在 kit 不再出现（存量 manifest 原样保留） |
| skills / wiki / timeline / lifecycle / discipline / sync index | 同名或新增 | 未复验 |

---

## 3. 升级实录（命令 · 退出码）

| # | 命令 | exit | 说明 |
|---|------|------|------|
| 1 | `npx dsh-coding-kit@1.5.1 check --target .` | 0 | 报「manifest 高于包版本」（见 §2 check 差异行） |
| 2 | `refresh-ide-blocks --dry-run` | 0 | AGENTS A1×1（local 块跳过×1）· CLAUDE A1×1 · mdc 块 0 |
| 3 | `pytest tests -q`（基线）/ `graph-compile.sh`（基线） | 3failed/242passed · 0 | 基线留证；graph 产物 diff 仅 generated_at 时间戳 → `git checkout --` 还原 |
| 4 | `git stash push -u`（untracked task 文件）→ `refresh-ide-blocks --yes` | 0 | preflight 对 untracked 也算 dirty，须 stash；写入 AGENTS/CLAUDE 各 1 行，备份落 `.cyning-harness/backups/refresh-ide-blocks/2026-08-24T15-29-58-404Z/` |
| 5 | `git stash pop` + diff | — | AGENTS/CLAUDE diff **仅** A1 一行；local 块不在 diff 中 = 零字节变化 |
| 6 | `upgrade --target . --yes` | 0 | manifest 2.24.0→1.5.1 · from_version=2.24.0 |
| 7 | `upgrade` 二跑 + refresh 二刷 dry-run | 0 | 幂等（§1） |
| 8 | `verify --task <本task>` | 2 | BLOCKED：missing R<n> review（20 帽序内未审） |
| 9 | `verify --task <本task> --allow-no-review --allow-invoke-gap` | **0** | 留痕豁免 · PASS（同时暴露 pre-30 invoke 缺 hat 10） |
| 10 | `pytest tests -q` / `graph-compile.sh`（升级后） | 3failed/242passed · **0** | 与基线一致 |

所有 npx 均带 `npm_config_cache=/tmp/npm-cache-lg`（本机 npm 缓存权限坑，无异常）。

---

## 4. local 块零手恢复证据

`git diff AGENTS.md CLAUDE.md`（升级后 vs HEAD）全文仅两处：

```diff
-   - 运行 `npx @cyning/harness verify --target . --task docs/tasks/active/task_*.md`
+   - 运行 `npx dsh-coding-kit verify --target . --task docs/tasks/active/task_*.md`
```

（AGENTS.md、CLAUDE.md 各一处，均在 `cyning-harness:begin/end` 产品块体内。）
`cyning-harness-local:begin/end` 块（pre-30 invoke 拒改码 / HG-PILOT-OPSDESK-GLAYER / G-L0 / graph_modules_path 图谱闸路径）**未出现在 diff 中**，内容完整，零手恢复。kit refresh 报告自述「跳过 local 块: 1」（AGENTS）。

---

## 5. 记录不动项（按 task 纪律）

| 位置 | 内容 | 处置 |
|---|---|---|
| `.github/workflows/lint-wiki-delta.yml` L3/33/37 | `npx --yes @cyning/harness@2.22.0 task lint-wiki-delta`（kit 有同名子命令） | **只记录不改**（切换另案） |
| `scripts/graph-compile.sh` L39/52 | `npx @cyning/harness graph yaml compile/check` | **不动**（probe task + SPEC 前置） |
| `.cursor/rules/05-harness-starter.mdc` L19 | `npx @cyning/harness verify` 字面 | refresh 发现面只认 product marker 块，该文件**无 marker（块 0）故不刷写**；为 harness 时代全量 cp 产物，升级是否改写属 kit 后续 wizard 面，本波记录不动 |
| `docs/harness/prompts/` 等 S2/模板 | kit upgrade 不再 cp 资产 | 保持 harness 2.24 时代内容（FRAGMENT_30_gate_verify 等指针仍有效） |

---

## 6. 剩余缺口与 severity

| ID | 现象 | severity | 说明 |
|----|------|----------|------|
| K1 | `check` 对 2.24.0→1.5.1 报「可能为降级安装」 | **P3** | 跨产品线版本号不可比；建议 kit check 识别 from_version 或 deprecate 链 |
| K2 | refresh-ide-blocks preflight 把 untracked 文件计入脏树 | info | `git status --porcelain` 语义；本波 stash -u 解决，符合 README 指引 |
| K3 | verify 硬闸 R<n>/pre-30 invoke 收紧 | info（预期） | 20 帽审查与 10 invoke 为 00 序内补件；豁免旗标留痕合规 |
| K4 | mdc 文件无 marker 不刷写 | **P3** | 存量仓 mdc 多为无 marker 拷贝，旧字面滞留；建议 kit 提供 mdc 无 marker 形态的发现/报告（B 组仅报告即可） |
| K5 | `.cyning-harness/backups/` 新增 untracked | info | 待 00 决定入库或 gitignore |
| K6 | kit preset 词表仅 `harness-only` | info | 存量 manifest preset=fullstack-node-py 原样保留，无影响 |

---

## 7. 对 probe task（graph 命令面切换）的前置结论

kit 1.5.1 **自带 graph 子命令面**：

```
graph yaml compile --graph-id ID [--target] [--input DIR] [--output FILE]
graph yaml compile --all [--target] [--input DIR] [--no-recursive]
graph yaml check  --graph-id ID [--target] [--input DIR] [--graph-json FILE]
graph yaml export --input DIR [--out FILE] [--no-recursive]
graph ingest [--target] [--actor ACTOR] [--dry-run]
graph snapshot [--target]
graph axioms check [--target] [--json]
```

`graph-compile.sh` 现行两行 `npx @cyning/harness graph yaml compile --input DIR --all` / `check --input DIR --all --graph-json FILE` 的参数面在 kit 同形存在；切换=替换命令头 + 行为等价回归（mermaid normalize 为本仓自脚本段，不受影响）。**切换执行属 probe task**，本 task 未动。

---

## 8. 验收清单

- [x] manifest = 1.5.1（from 2.24.0 · `.cyning-harness/` 约定不变）
- [x] AGENTS/CLAUDE local 块完整（diff 证明 · §4）
- [x] refresh-ide-blocks --yes 落盘 + 幂等复检
- [x] `verify --task` 跑通（豁免留痕 PASS · 严格态缺口为序内 20/10 补件）
- [x] graph-compile.sh exit 0（harness 面未动）
- [x] pytest 无新增失败（3/242 = 基线）
- [x] kit graph 子命令面结论记录（§7）
- [ ] 00：补 10 invoke 快照 · 20 R<n> 审查 · `.cyning-harness/backups/` 入库决策 · 统一 commit
