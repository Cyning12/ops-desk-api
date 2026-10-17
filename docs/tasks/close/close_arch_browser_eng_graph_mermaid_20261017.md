# CLOSE：arch-browser-eng-graph-mermaid（工程图谱默认 Mermaid 组件 · 缩放/平移/复制源码 · 追溯建档）（2026-10-17）

> **task**：[../done/task_arch_browser_eng_graph_mermaid.md](../done/task_arch_browser_eng_graph_mermaid.md)（已归档 done/ · 状态行 CLOSED 回写）
> **类型**：arch-browser 工程图谱展示增强（纯 web 展示层 · 零业务码 · 追溯建档档）
> **关账日期**：2026-10-17 · 帽位：CLOSE（50 · 批量关账 close/active-batch-20261017 之一）

---

## 一 · 任务信息

| 项 | 值 |
|----|----|
| task_slug | `arch_browser_eng_graph_mermaid` |
| 背景 | 工程图谱展示面升级：默认 Mermaid 组件（缩放/平移/复制源码）全站替换静态图；实际工作 2026-10-15 在飞未提交、先于任何档案，2026-10-16 维护者裁定（ask_user_question · 选项「追溯建档 + hunk 切分 + mermaid 独立 PR」）补档 |
| 分支 | `task/arch-browser-eng-graph-mermaid`（2026-10-16 rebase 到 master `e00b414`） |
| 帽链 | 追溯建档（10 缺省 · 维护者裁定即人审面）→ 双闸 approved（追溯）→ 30 追溯（invoke `invoke_20261016_30_retro.md` · hunk 切分证据落盘）→ PR #257 → **CLOSE（本档 · 批量关账）** |
| 追溯诚实记录 | 开工时人工闸缺失为既成事实；R1 审查实质 = hunk 切分正确性 + 演示面零混入复核（证据在 30 invoke），**无独立 20 审查文**（豁免见 §四.2） |

## 二 · 交付

| 环节 | 实证 |
|------|------|
| PR | [#257](https://github.com/Cyning12/ops-desk-api/pull/257) · **MERGED 2026-10-17T03:25:13Z · squash commit `833f605`** |
| 提交链 | `0a91268` feat mermaid 面 → `b34af17` chore(deps) lockfile 卫生（uv.lock=import-linter 合法同步 · pnpm-lock.yaml=spec-wave 3.3.0 锁 · .pnpm-store 删除）→ `965e97e` 追溯建档+30 invoke → `2b34d08` eng_l0 管线回补（00 CLOSE 档裁定纠偏）→ `5044ce7` 裁定纠偏落档（rebase 后新 hash · rebase 前 95a9f4e/5b63f29/edba447） |
| 范围落地 | S1 `web/app.js` `mermaidPanelHtml`（±/1:1/适应/复制源码 · 滚轮缩放 · 空白拖拽平移 · `parseMermaidClicks` click 指令）· S2 「工程 G-L0」→「工程图谱」改名 + renderEngL0 重写（节点/边列表折叠 chip 备用）· S3 `normalizeMermaidSvg`/`attachMermaidZoom`/`bindMermaidNodeNav` · S4 `web/style.css` +96 · cache-buster `v=20261015-mz3` · S5 dist 重建（site-data.json 保持 HEAD 版剔除） |
| 切分纪律 | app.js 按 hunk 切两任务：本 PR 只含 mermaid 面；demo_agent_host_surface 演示面（DEMO_* 常量/display 字段消费）hunk 切出零混入，由 demo task 独立 PR 闭环（api PR #255 / CLOSE PR #256 · 维护者另窗） |
| invokes | `docs/harness/invokes/by-task/arch_browser_eng_graph_mermaid/invoke_20261016_30_retro.md`（追溯 30 · hunk 切分证据）· 本 CLOSE 补 50 于批量目录 `close_active_batch_20261017/` |

## 三 · 核验结论（验收终态摘要 · TC-1–TC-6 全绿）

| 验收项 | 结果 | 实证 |
|--------|------|------|
| TC-1 语法+一致性 | ✅ | `node --check web/app.js` 通过 · `web/app.js` == `dist/app.js` |
| TC-2 零 demo 混入 | ✅ | `git diff HEAD~2 -- web/app.js` 关键词零命中（ENG_DEMO/DEMO_TEXT/demoText/ENG_L0_DEMO/disp./m.display 全 0）· 手术反向校验 64 行差异全属 demo 域 |
| TC-3 dist 重建 | ✅ | build_site.py EXIT=0 · dist/site-data.json 与 HEAD 一致（纯衍生刷新剔除） |
| TC-4 hygiene 独立提交 | ✅ | uv.lock / pnpm-lock.yaml 锁卫生 · .pnpm-store 已删 |
| TC-5 demo 面闭环 | ✅ | 维护者另窗闭环（api PR #255 / CLOSE PR #256 · demo task 归档 done/）· 原表述作废照登 |
| TC-6 eng_l0 管线回补 | ✅ | `2b34d08`：00 CLOSE 档裁定「_ENG_L0_DEMO_* 只服务 eng_l0 管线 → 判 eng」· 首切误归 demo 面切除 → 本 PR 纠正回补（build_site.py +171 · app.js ENG_L0_DEMO_* 过滤改名 · dist eng_l0_mermaid 键 2603ch） |

## 四 · 偏差与钉案（如实照登）

1. **追溯建档性质**：交付先于档案（2026-10-15 在飞）· 维护者 2026-10-16 裁定追溯建档为本任务人审面 · 本 CLOSE 不追咎、只照登。
2. **无独立 20 R1 审查文**：R1 实质 = hunk 切分正确性复核（证据在 30 invoke）· 归档后 verify 若 EXIT=2（missing R<n> review），按 PR #245 扩列纪律走 `docs/harness/legacy-gate-exempt.yaml` 新增一枚（四字段齐 · 本批量关账 PR 即人审面）。
3. **FP-1 混合 hunk 手术**：H3/H5/H7/H12 不可 git apply 子集 → 采「全量文件 − demo 编辑」逆向手术 + 双向 diff 校验（已执行 · TC-2 闸佐证）。
4. **FP-2 衍生刷新剔除**：dist/site-data.json 重建带来的 generated_at 等真值衍生刷新不进 mermaid 提交（保持纯展示面）。
5. **TC-6 首切误判纠正**：`_ENG_L0_DEMO_*` 常量命名含 DEMO 但只服务 eng_l0 管线 → 首切误切除 → R3 复核回补 `2b34d08` 纠正闭环（命名误导教训照登）。

## 五 · 维护者验收 checklist（00 代录 · 批量关账授权）

- [x] PR #257 MERGED · squash `833f605` 在 master
- [x] TC-1–TC-6 验收终态全绿（§三）
- [x] demo 面零混入切分纪律成立（TC-2 · 双向 diff 证据在 30 invoke）
- [x] task 档归档 done/ · 状态行 CLOSED + 修订记录 CLOSED 行
- [x] active README 登记表补登
- [x] 本 CLOSE 档 + 50 invoke 落盘
- [x] 分支 `task/arch-browser-eng-graph-mermaid` 移交 00 统一清理（本 CLOSE 不删任何东西）
