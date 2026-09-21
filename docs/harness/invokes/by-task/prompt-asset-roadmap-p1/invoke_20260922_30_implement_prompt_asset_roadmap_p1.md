# invoke · 30 实现 · prompt-asset-roadmap-p1

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 30 实现（改码 · 不签任何人闸） |
| **task** | `docs/tasks/active/task_prompt_asset_roadmap_p1.md`（signed · HG-TASK-DRAFT/HG-AUDIT-R1=approved · HG-GRAPH-MODULES=approved 真读核验） |
| **对照基准** | `docs/spec/prompt-asset-roadmap/SPEC-prompt-asset-roadmap_v1.md`（signed 94b2e21） |
| **分支** | `task/prompt-asset-roadmap`（每次 commit 前 `git branch --show-current` 核验 · 未 push） |

## GATE_VERIFY（30 开工首输出）

| human_gate_id | status | blocks | 判定 |
|---|---|---|---|
| HG-TASK-DRAFT | approved | 20-R1, 30 | 过 |
| HG-AUDIT-R1 | approved | 30 | 过 |
| HG-GRAPH-MODULES | approved | 30 | 过（零图谱变更按实判 · 回炉条款未触发：未新增一级模块/未拆 prompts 独立 module_id/零新路由/表/事件） |
| HG-PILOT-OPSDESK-GLAYER | n/a | — | — |

## 实现摘要（D1–D4 一次提交 · 文案零改动）

- **D1**：`render()` 改 `string.Template.substitute`（缺键 KeyError 包装点名 template_id 沿用 render.py:46-47 模式 · slots 语义与签名一字不动）。
- **D2**：新建 `app/ops/prompts/assets/` 9 个 md（front-matter `template_id`/`version` · 版本承原值 registry 3 + 新增 6 自 v1）+ `loader.py`（显式炸 · front-matter 手写解析 ≤30 行零新依赖 · `functools.cache` + `clear_asset_cache()`）+ `templates.py` 内联 body 清零改由加载器喂（`TEMPLATES` 键集合语义存续）；6 处内联常量删除改调 `render()`（lg_rag/nodes.py ×3 · multi/nodes.py ×2 · memory/extract.py ×1）。
- **D3**：`assets/README.md` 写明非开发操作路径（改 body → bump version → PR → CI 锚点断言 → 合入上线）+ version bump 约定 + 变量集合契约表；加载器校验单测钉死。
- **D4**：`01_modules.md` memory 行备注级更新（extract 改调 prompts 加载器 · 出边 +`prompts` · 00 代录人签行 · 对齐 llm-layer-hardening 先例）；graph-compile 绿。

## 实测记录（真跑）

- **逐字节对拍**：迁移前基线落盘 `/tmp/prompt_asset_baseline.json`（str.format 期渲染成品 9 条）→ 迁移后 `render()` 重渲 9 条全量 diff：**9/9 identical（含 supervisor 带 catalog_block · suffix 带三变量成品串）**。
- **计数断言**：`.format(` 全仓 3→**2**（answer.py:107 · fallback.py:326 特例）；`你是` 13→**4**（grader.py:104,115 · chat/nodes.py:30 · packs.py:133 恰特例清单）；assets body `{{`/`}}` **零命中**；9 模板 body 游离 `$` **零命中**（声明变量 `$catalog_block`/`$prefix_block`/`$suffix_cap` 除外）；prompts/ 下 `.format(` 零残留。
- **调用方零 diff**：`git diff master -- app/ops/strategy/intent.py` 为空；multi/nodes.py render 两调用行（supervisor/suffix）逐字未动，diff 仅含常量删除与 import 调整。
- **变异检验**（各做完即还原复绿）：① supervisor 调用去 `catalog_block` → 18 红（KeyError）→ 还原 34 绿；② 改名 `lg_rag.router.system.md` → import 即 `PromptAssetError` 点名路径+template_id → 还原 39 绿；③ router 资产注入 `{{"route"` → 锚点/grep 断言 2 挂 → 还原 34 绿 + grep 零命中。
- **pytest**：基线 3 failed/1172 passed/1 skipped（chat_ws×2+proxy×1 环境性）→ 本波 **3 failed（同三项环境性）/1206 passed/1 skipped**（+34 新增守护用例 · 无既有用例删除 · memory_backfill 本波未复现 flaky）；`import app.main` 冒烟过。
- **ruff**：`ruff check app tests` = **57**（与基线一致 · 零新增）。
- **graph-compile**：`./scripts/graph-compile.sh` 绿（图谱备注更新后复跑绿）。

## B1 21 行处置回填

回归×11（#1-7 prompt/packs/slots/grader/chat 测试与调用方零改动全绿 · #18/#19/#20 辅扫计数吻合）· 改编×8（#10-15 六常量消费点删常量改调 render · #16 templates.py 内联 body 清零 · #17 render.py 改 Template · #18/#19 计数行随迁移达成）· 新增×1（#21 `tests/test_prompt_assets.py` 34 用例：加载器显式炸×7 · 锚点×6 · 缺键×1 · 缓存清重读×1 · 资产形态/零残留 parametrized）· 删除×0。

## 下一棒

40 核验：逐字节对拍复做 · 变异三条复做 · 验收 20 条逐条核 → 回填 task「自检结论」。
