# invoke · 40 核验 · prompt-asset-roadmap-p1

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-22 |
| **帽** | 40 核验（只写过程文档 · 不改实现码 · 不签任何人闸） |
| **task** | `docs/tasks/active/task_prompt_asset_roadmap_p1.md` |
| **交付 commit** | `17ce562`（实现）+ `9856c1c`（30 invoke + 图谱备注） |
| **分支** | `task/prompt-asset-roadmap`（commit 前 `git branch --show-current` 核验 · 未 push） |
| **对照基准** | 验收 20 条 + B1 21 行（task）· SPEC §6 |

## 总判定

**PASS · 验收 20/20 通过 · 30 自称全数复核属实（一处对拍方法学差异已亲跑修正后仍 9/9 identical）**。

## 核验记录（全真跑）

### 1 · pytest 全量 + 基线红对照

- 当前树：`3 failed / 1206 passed / 1 skipped`（15.05s 真跑）。
- 基线对照：`git worktree add /tmp/ops-desk-baseline c48398f`（= origin/master）+ 拷贝同 `.env` + `PYTHONPATH` 前置覆盖 path 型 editable 安装（已实证 `app.__file__` 指向 worktree）→ `3 failed / 1172 passed / 1 skipped`。
- 两侧失败集**逐名相同**：`test_chat_ws.py::test_ws_message_streams_events` · `test_ws_second_message_while_active_rejected` · `test_capability_http_adapter.py::test_urllib_transport_honors_explicit_capability_proxy`（环境性基线红 · 非本波引入）。
- 增量 1206−1172 = **+34** = `tests/test_prompt_assets.py` collect 恰 34 用例（亲跑 `--collect-only`）· **零既有用例删除**。
- memory_backfill flaky：两跑均未复现，无需复跑区分。

### 2 · 计数断言（亲跑 grep 复核）

| 断言 | 口径 | 结果 |
|------|------|------|
| `.format(` 3→2 | `grep -rn --include='*.py' '\.format(' app/` | **2**：answer.py:107 · fallback.py:326（恰特例清单）✓ |
| prompts/ 包内零 `.format(` | 同上限定 `app/ops/prompts/` | 零命中 ✓ |
| `你是` 13→4 | `grep -rn --include='*.py' '你是' app/` | **4**：grader.py:104,115 · chat/nodes.py:30 · packs.py:133（恰特例清单 · answer 经 yaml 零 .py 命中）✓ |
| assets `{{`/`}}` 零命中 | `grep -rn` assets/*.md | 零命中 ✓ |
| assets 游离 `$` 零命中 | 排除声明变量 `$catalog_block/$prefix_block/$suffix_cap` | body 零命中（README.md 两处为纪律说明文字 · 非模板 body）✓ |

### 3 · 逐字节对拍（亲核 · 非轻信）

30 的 `/tmp/prompt_asset_baseline.json` 已不存在，40 **独立重做对拍**：AST 抽取 `c48398f` 四文件旧常量（templates.py AnnAssign ×3 · lg_rag/nodes.py ×3 · multi/nodes.py ×2 · memory/extract.py ×1），按旧 render 语义 `body.format(**vars)` 重渲（**40 修正一处方法学**：无变量模板旧代码同样走 `.format(**{})` 会折叠 `{{`→`{`，首跑 intent.system 假差异即此 · 修正后口径与旧 render.py:45 真实行为一致），与当前树 `render()` 输出（含 supervisor 带 catalog_block · suffix 带三变量成品串）逐条 == 断言：

```
IDENTICAL lg_rag.intent.system (468) · supervisor.system (648) · supervisor.suffix.system (664)
IDENTICAL router (293) · direct (87) · rewrite (185) · extract (205) · aggregator (227) · memory.extract (346)
RESULT: 9/9 BYTE-IDENTICAL
```

守护测试 `test_prompt_assets.py` 非空转确认：锚点断言为参数化真断言（渲染输出含裸 `{"domain"`/`{"route"`/`{"facts"` 等 + 零 `{{`），加载器显式炸用例走 `tmp_path` monkeypatch 隔离（不动真资产 · 形态正确）。

### 4 · 变异检验复做（② 缺文件显式）

- `mv assets/lg_rag.router.system.md{,.mutbak}` → `import app.ops.prompts.templates` 即炸：`PromptAssetError: prompt 资产缺失或不可读: .../assets/lg_rag.router.system.md (template_id=lg_rag.router.system)`（**点名路径+template_id · 非静默空串**）✓
- 还原 → `test_prompt_assets.py + test_prompt_assembly.py + test_prompt_packs.py` 86 passed → `git status` 工作树净 ✓
- ① 缺键 / ③ 转义残留：30 invoke 留痕（18 红→还原 34 绿 · 锚点/grep 2 挂→还原全绿），且两条均被常驻守护测试钉死（`test_render_missing_key_names_template_id` · `test_asset_zero_escape_residue` + 锚点参数化）——非一次性动作，40 采信。

### 5 · ruff / graph-compile

- `ruff check app tests`：当前 **57** = 基线 **57**（worktree 亲跑）；违规多重集（规则码+文件，抹掉行号）**逐条 identical**（4 处行号差全在 multi/nodes.py · −20 恰为删常量行数）→ **零新增** ✓
- `./scripts/graph-compile.sh`：绿（EXIT=0）；复跑产生的 graph.json `generated_at` 漂移已 `git checkout` 还原，**不混入本提交** ✓
- `import app.main` 冒烟 OK ✓

### 6 · 生产路径 diff 白名单（`git diff origin/master...HEAD`）

app/ 改动恰为：prompts/ 模块（render.py 3 行 · templates.py 清零改加载器喂 · loader.py 新增 · assets/ 9 md + README 新增）+ 6 常量删除点（lg_rag/nodes.py · multi/nodes.py · memory/extract.py · 各含必要 import 行）。**`strategy/intent.py` 零 diff**（不在 diff 名单）；multi/nodes.py 的 render 两调用行（supervisor/suffix）逐字未动 ✓。**特例四例零触碰**：grader.py · lc_evidence_chain/answer.py · packs.py · chat/ 整目录 diff 为空（亲跑 diff --stat 空输出）✓。图谱 01_modules.md 恰 memory 行备注 + 闸表代录行；graph.json 仅 `generated_at`（编译产物 · prompts 非 module_id 故无边变化 · 与零变更裁定一致）✓

### 7 · B1 抽查（实核 9 条）

| # | 处置声称 | 40 实核 |
|---|---------|---------|
| 1 test_prompt_assembly.py 回归零改动 | 零 diff（diff 名单无此文件）+ 用例全绿 ✓ |
| 2/3 test_prompt_packs.py 子集/render 断言 | 零 diff + 全绿 ✓（`set(TEMPLATES)` 语义存续） |
| 5 test_skill_registry.py slots | 全绿（21 passed 批次含）✓ |
| 6 test_rag_grader_prompt.py 特例回归 | 全绿 + grader.py 零 diff ✓ |
| 7 test_chat_nodes.py 非范围回归 | 全绿 + chat/ 零 diff ✓ |
| 8 intent.py 零 diff 钉死 | diff 名单无此文件 ✓ |
| 15 memory/extract.py 改编 | 常量删除改调 `render("memory.extract.system")` + 新增 `from app.ops.prompts import render`（闸表留痕的 memory→prompts 边如实落地）✓ |
| 18/19 计数行 | 见 §2 亲跑 ✓ |
| 21 新增守护 34 用例 | collect 恰 34（显式炸×7 · 锚点×6 · 缺键×1 · 缓存清重读×1 · 形态/零残留参数化 19 · registry 1 · 变量代入 1）✓ |

回归×11 / 改编×8 / 新增×1 / 删除×0 声称与实核一致。

## 验收 20 条逐条判定

人工闸（1）✓ · D1（3）✓✓✓ · D2（5）✓✓✓✓✓ · D3（2）✓✓ · 行为零变化（3）✓✓✓ · 变异检验（3）✓✓✓ · 工程（3）✓✓✓ = **20/20**。

## WARN / 问题清单

1. **（记录非阻塞）** 30 的对拍基线文件 `/tmp/prompt_asset_baseline.json` 未留存，40 以 AST 抽取 + 旧语义重渲独立重建基线，结论一致——后续 task 一次性对拍产物建议落 `/tmp` 外或写入 invoke 摘要哈希。
2. **（记录非阻塞）** 30 交付的 graph.json 含 `generated_at` 时间戳前进（编译产物）；本帽已核验其无边变化并确认本波提交不新增漂移。
3. **（承 task R5 残余 · 非本波问题）** version 忘 bump 无机械闸；图谱既有登记缺口两处（lg_rag 出边缺 memory · memory 出边缺 structured_output）留痕待图谱维护波次。

## 结论

30 交付（`17ce562` + `9856c1c`）满足验收 20 条全项，B1 21 行处置全数属实，计数断言/对拍/变异/基线红/ruff/graph-compile 全部亲跑复核通过。**40 核验 PASS**，可进 CLOSE。
