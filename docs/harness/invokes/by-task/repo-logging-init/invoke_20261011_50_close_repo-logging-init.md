---
hat: 50
task_slug: repo-logging-init
date: 2026-10-11
---

# invoke · 50+CLOSE · repo-logging-init（仓级 logging 初始化 · SPEC §9 序2）

## 收口结论

- 链路全通：10 落稿（`73b79e6` · 00 代笔 · 授权 m01606）→ 20 R1（`32f5d18` 骨架 → `2ffdd29` 定稿 · PASS-WITH-NITS · N-1~N-6 · 锚点 12 组核真）→ 三闸代录（`a31d471`）→ 30（`445ce28` 红测先行 3 红 → `b329aec` feat → `ed69292` invoke+图谱 :27 回写）→ 40（`6bd4cec`/`268e46c`/`642a4d0` · PASS-WITH-NITS · TC2 坑位1 反转实证 · TC4 4请求4行 · TC5 基线对拍零新增红）→ 自检回填 `2a6ffe3` → CI 修复 `2d686f0`/`5e07040` → PR [#227](https://github.com/Cyning12/ops-desk-api/pull/227) CI 绿 → squash merge `e5b5c3d`（2026-10-11 09:39 CST）。
- 闸链：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 approved（维护者授权 · 00 代录 2026-10-11）· HG-PILOT-OPSDESK-GLAYER n/a。
- 归档：task → done/（状态行回填 done（CLOSED 2026-10-11 …）· 修订表 CLOSE 行 · git mv 保留全文）；active/done 双侧 README 补登；CLOSE 文档 `docs/tasks/close/close_repo_logging_init_20261011.md`（九节）落盘。

## 交付摘要

| 项 | 内容 |
|---|---|
| **产出** | `app/main.py` +28：import 期 `_init_logging()`（D1=A）· `OPS_LOG_LEVEL` 默认 INFO 非法 fail-closed（D2=A）· 格式 `%(asctime)s %(name)s %(levelname)s %(message)s` 钉死（D3）· uvicorn logger 不动（D4） |
| **验收** | TC1 红测先行三组（裸 python 子进程断言）· TC2 裸 uvicorn live 坑位1 反转（after INFO 钉死格式可见 / before wrapper grep 空 · access 仍 3）· TC3 compose 零 diff 照登 · TC4 4 请求 4 access 行零双行 · TC5 master 基线对拍零新增红 |
| **红线** | 55 处 getLogger 调用点零 diff · 零新依赖 · 台账键字面零改 · scripts/evals/alembic 三面零 diff · ruff 触及面零新增 · graph-compile EXIT=0 |

## 钉案登记（详见 CLOSE 文档第四/七节）

1. **N-40-1 import 窗口裸格式**：`app/main.py:9-12` import 链先于 `:38` `_init_logging()`，窗口内 WARNING+ 走 lastResort 裸格式、INFO 被吞；验收三键请求期发射不受影响 → nit 级，修法候选=初始化挪 import 链之前，留后续 task 裁定。
2. 仓级 verify done/ 遗留档缺口基线（承前两 CLOSE 钉案 · 第三次照登）。
3. spec-wave 版本钉法：3.2.0 发布漂移断 check/tech-graph 实证（`5e07040` GRAPH_CLI 钉 3.0.1）——npx 调用面统一钉版建议。

## 质量钉（CLOSE 机械闸复跑 · REAL_EXIT 取证）

- **task lint**（`npx spec-wave task lint --file docs/tasks/done/task_repo_logging_init.md`）：REAL_EXIT=2 · E3 缺 `## 验收标准`（该档系 `## 5. 验收标准` 编号节轻量格式）· E4 缺失败路径节 · E5 缺自检结论节（W2/W4 提醒级）。**3.0.1 与 3.2.0 对拍同结果**——系归档档轻量格式固有，本 CLOSE 依「保留全文」不重构归档档，照登。状态 token 已对齐仓内词表（`done（CLOSED 2026-10-11 …）`，W1 消除）。
- **verify**（`npx spec-wave@3.2.0 verify --target . --task docs/tasks/done/task_repo_logging_init.md`）：REAL_EXIT=2 · BLOCKED「HG-AUDIT-R1 pending」——该档人工闸记于 Harness 元信息表行（`HG-AUDIT-R1 = approved` 在案），spec-wave 闸解析要求 `### 人工闸` 节 → 判 `?`。3.0.1 对拍同结果。三闸人签事实以 task 档 + `a31d471` + R1 审查文为准；task 已 merge 归档，30 闸判定属历史回放非现行门槛，照登。
- **graph-compile**：本 CLOSE 无图谱变更（`01_modules.md:27` 回写已随 PR #227 入 master）· n/a。

## 移交

- worktree `t-repo-logging-init` 与分支 `task/repo-logging-init`（已 merge）、`close/repo-logging-init` **移交 00 统一清理**（本棒父令「勿删任何东西」）；active/ 目录无在途 task。
- 本 CLOSE 的 PR 由 00 统一 merge（本棒不 merge）。
