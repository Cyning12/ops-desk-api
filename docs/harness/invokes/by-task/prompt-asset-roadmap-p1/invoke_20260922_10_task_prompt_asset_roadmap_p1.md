# invoke · 10 · prompt-asset-roadmap-p1 · task 落稿

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 10-task（维护者授权「授权00签收所有过程文档」承前令 · SPEC signed 后落稿 · 本棒由 00 委派 10-task 帽 Agent 执行） |
| **文件** | `docs/tasks/active/task_prompt_asset_roadmap_p1.md` |
| **上游** | `docs/spec/prompt-asset-roadmap/SPEC-prompt-asset-roadmap_v1.md`（signed · HG-SPEC-SIGNOFF=approved 2026-09-22 · 94b2e21） |
| **格式基准** | `docs/tasks/done/task_continuity_dedup.md`（真读对齐字段 · PR #153 已合） |

## 结论

**PASS（落稿）** · 范围 D1 渲染去转义（string.Template.substitute）/ D2 资产落盘（`app/ops/prompts/assets/` 9 模板 md + front-matter · 6 内联常量删改调）/ D3 审计形态（assets README + version bump 约定 · 加载器显式炸）/ D4 图谱零变更按实判同竖切（一次提交 · 渲染语法与变量 `$` 改写强耦合无先行切分空间）；非范围沿用 SPEC §3（阶段二三 · 文案优化 · 注入防护 · A/B + grader/answer/packs/chat 四特例 + fallback 话术）；验收 **20 条**全否定性断言化逐块映射 SPEC §6（人工闸 1 / D1×3 / D2×5 / D3×2 / 行为零变化×3 / 变异检验×3 / 工程×3）· 与 SPEC 实质差异**零**；failure_paths **15 条**（SPEC §5 十条翻四列 + 过程五）；R0–R5 全轮无 early_stop；`orchestration` 标「总轨三阶段：本 task = 阶段一」（参照 capability-gateway-p0~p3）。

## 实扫留痕（本帽真跑）

- `git branch --show-current` = `task/prompt-asset-roadmap` ✓（HEAD 94b2e21 SPEC 签收）
- `.format(` 全仓：`grep -rn --include='*.py' '\.format(' app/` = **3 处**（render.py:45 · answer.py:107 · fallback.py:326 · 与 SPEC 一致）→ 迁移后应 2 处（验收 D1 计数断言）
- `你是` 全仓：`grep -rn --include='*.py' '你是' app/` = **13 处**（templates ×3 · lg_rag/nodes ×3 :47,:57,:223 · multi/nodes ×2 :85,:94 · memory/extract :47 · grader ×2 :104,:115 · chat/nodes :30 · packs :133）→ 迁移后应 4 处特例命中（验收 D2 计数断言）；**口径细化留痕**：SPEC 写「搜 `你是 `（带空格）仅特例清单」，带空格口径实测 8 命中且 grader 两条（「你是检索结果评级器。」无空格）本就不命中 → task 采用不带空格 `你是` 口径 13→4，特例命中集合与 SPEC 语义一致
- 9 迁移源常量区 `$` 字符：templates.py + nodes.py 三常量 + multi/nodes.py 两常量 + memory/extract.py 各 **0 命中**（Template 元字符面清零 · SPEC「实扫零 `$`」复核成立）
- `app/ops/prompts/` 现仅 `__init__.py / packs.py / render.py / templates.py`（无 assets/）
- render 包外消费面：`app/ops/strategy/intent.py:57` · `app/ops/lg_rag/multi/nodes.py:120-137`（零 diff 钉死）；http_generic `_render` 为 capability 自渲染无关
- 6 内联常量消费点全在 app/（nodes.py:100,:245,:290 · multi/nodes.py:1041,:1512 · extract.py:116）· **tests 零直引**（grep 实证）
- pytest 基线真跑：`python -m pytest tests --collect-only -q` = **1176 collected**（与 continuity-dedup 40 核验后基线一致 · 本波无既有用例删除 · 新增守护测试数入 40 记录）
- B1 落盘 **21 行**（回归×11 · 改编×8 · 新增×1 · 删除×0 · 含辅扫 3 行）
- **SPEC 措辞偏差留痕两处**（范围语义零影响 · 不改 SPEC · 修措辞走 10-spec 修订轨）：
  ① SPEC「strategy/intent.py:57」实际路径 `app/ops/strategy/intent.py:57`（**不在** `app/ops/lg_rag/` 下 · 省前缀写法易误读；该文件 `import app.ops.prompts` 为既成事实 · 本 task 对其零 diff）
  ② SPEC「lg_rag/memory → prompts 依赖边已存在或同包内」——lg_rag 侧成立（multi/nodes.py:120-137 已 import render）· **memory 侧不成立**（`app/ops/memory/` 对 prompts 零 import · grep 实证）；30 改调 render 将新增 memory→prompts 物理 import，因 prompts 非独立 module_id（C2 裁定归属 lg_rag 行内部路径），按 llm-layer-hardening「依赖出边 +db」00 代录先例作 memory 行出边**备注级补充**，**不构成 SPEC 回炉**
- HG-GRAPH-MODULES 真值核验：**真读** `docs/_tech_graph/l1/01_modules.md` —— 模块表已建置 · lg_rag 行 C2 备注（2026-09-01 approved）「prompt 装配层 `app/ops/prompts/**` 归属本行」→ assets/ 为行内部路径延展 · 覆盖不变 → approved；零图谱变更 + **回炉补闸条款**（30 新增一级模块 / prompts 拆独立 module_id / 新增路由/表/事件 → 退 10-spec + 补闸）
- **既有图谱登记缺口留痕**（非本波义务 · 不回改）：lg_rag 行出边未列 memory（router.py:50 / sse_stream.py:49 / continuity.py:218 已 import `app.ops.memory`）· memory 行出边未列 structured_output（extract.py:30 已 import）

## 闸态

- `HG-TASK-DRAFT` = **pending**（00 验收代录 · 本帽不签）
- `HG-AUDIT-R1` = **pending**（blocks 30 · 20 审后 00 依维护者授权代录）→ **30 拒开工**
- `HG-GRAPH-MODULES` = approved（真读模块表 · 零图谱变更 + 回炉补闸条款 + 两点如实留痕）
- `HG-PILOT-OPSDESK-GLAYER` = n/a

## 下一棒

20-task-audit 书面审（对照 SPEC）→ 00 代录 HG-TASK-DRAFT + HG-AUDIT-R1 → 30（`task/prompt-asset-roadmap` · D1→D2→D3 一次提交 · 文案零改动 · 逐字节对拍 + 变异检验三条）。后续 20/30/40 invoke 由各棒落盘本目录（命名对齐 `invoke_<yyyymmdd>_<hat>_<verb>_prompt_asset_roadmap_p1.md`）。
