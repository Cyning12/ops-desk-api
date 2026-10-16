# Invoke：arch_browser_eng_graph_mermaid · 30 追溯实现与 hunk 切分（2026-10-16）

- **task**：docs/tasks/active/task_arch_browser_eng_graph_mermaid.md（追溯建档 · 同批落盘）
- **分支**：task/arch-browser-eng-graph-mermaid（开工时 == main 2a5878c · 无独立提交）
- **提交**（rebase 后）：0a91268（mermaid 面 7 文件 +965/−155）· b34af17（lockfile 卫生）· e736f4f（追溯档）
- **rebase 记录（2026-10-16）**：master 已并 demo 面（PR #255 squash 370cee4，维护者另窗独立实现）→ 本分支 rebase 到 e00b414。冲突 web/app.js + dist/app.js，以「mermaid-only 版 + 维护者 demo 编辑集（6 hunk 41 行 · 与本窗 demo 实现逐字相同的子集）」手术合并，双向 diff 校验：vs master 差异全属 mermaid 域 / vs mermaid-only 差异 == 维护者 demo 编辑集。rebase 后 0a91268 diff 纯 mermaid 面（demo 已在 base）。master 与本窗 demo 实现差异：维护者版无 ENG_L0_DEMO_HIDDEN/LABEL（L0 演示过滤全在 build 层）、build_site.py 为维护者独立实现（+69 行 vs 本窗 +171 行）、eng_l0 无 agent_desk id 别名；本窗 demo 版 build_site.py 已弃。rebase 前 hash：95a9f4e/5b63f29/edba447。

## 背景

10-15 在飞的 mermaid 组件工作未提交、零 Harness 档案，且与 demo_agent_host_surface 的 app.js 改动混在同文件 14 个 hunk。维护者 2026-10-16 裁定：追溯建档 + hunk 切分 + mermaid 独立 PR。

## 切分方法（混合 hunk 不可 git apply 子集）

1. 全量备份 /tmp/egm_backup/（tracked_full.patch 3143 行 · web_app_full.js · dist_app_full.js · demo task/invoke）
2. app.js 14 hunk 逐一分类 MERMAID/DEMO（H3/H5/H7/H12 为混合）
3. 逆向手术：从全量文件删 demo 编辑集（DEMO 常量段 / note-box / display 消费 / 演示过滤改名共 13 处替换 + 1 段行删除），每处断言恰好命中 1 次
4. 双向校验：
   - mermaid-only 文件 demo 关键词零命中（ENG_DEMO|DEMO_TEXT|demoText|ENG_L0_DEMO|disp\.|m\.display = 0）
   - mermaid-only ↔ 全量 64 行差异逐行过目共分类，全属 demo 域
   - mermaid-only ↔ HEAD 457 行差异全属 mermaid 域（组件/缩放/工程图谱改名/chip 备用）
5. node --check 通过；web/app.js == dist/app.js

## 衍生刷新剔除

build 重建 dist 时 site-data.json 出现 3 行真值衍生刷新（generated_at / graph_generated_at 06:43:36→10:05:54 / hitl 模块 note 补 hitl-resume-async 段，均来自已提交真值），裁定剔出 mermaid 提交（git checkout HEAD -- dist/site-data.json），保持纯展示面。

## 验收证据

- TC-1 node --check OK · diff -q web/dist app.js 一致
- TC-2 见上双向校验
- TC-3 build_site.py EXIT=0（freeze 20261014_V1 · host_modules=34 graphs=9）
- TC-4 5b63f29 · .pnpm-store 3.7M 已删
- 提交后工作树仅剩 demo 面（SPEC/catalog×2/build_site.py/app.js 全量版/dist 全量）+ demo task/invoke 未跟踪档

## 经验

- 混合 hunk 场景「全量 − 已知编辑集」逆向手术优于 git apply -p 子集：编辑集封闭可断言（每处命中 1 次）+ 双向 diff 可机器校验
- dist 为纯衍生物：重建即带上真值新内容，提交切分时须显式决定是否纳入
- 在飞工作先落 task/invoke 再动手——本次追溯成本（侦察+手术+校验）远高于事前建档
