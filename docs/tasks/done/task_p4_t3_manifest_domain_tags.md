---
title: task · P4-T3 · capability manifest domain 键消费（domain→tags 注入 · 词表校验 · 保留字拒载）
---

# task · P4-T3 · capability manifest domain 键消费（domain→tags 注入 · 词表校验 · 保留字拒载）

> **状态**：`active`（2026-11-18 落卡 · 夜间自动执行波）
> **来源**：workspace 18-p4-generalization-design.md §2.1（R6/R10）+ 19-p4-contracts.md §1/§2（commit e453a36 钉死口径真源）· 授权 issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间预授权 · 委派书 p4-t3-manifest-domain-tags）

## Harness 元信息

| 键 | 值 |
|----|----|
| **task_slug** | p4-t3-manifest-domain-tags |
| base | 297363bd |
| 关联 issue | issue Cyning12/ops-desk-workspace#23（授权真源）· workspace 18 文 §2.1 + 19 文 §1/§2（需求与口径真源 · commit e453a36） |
| 关联 PR | feat 本 PR · close chore PR（收口登记） |
| **wiki_delta** | `n/a` |
| **wiki_delta_note** | 本仓未启用 WikiTrack；本波为 capability manifest G-L1 面 + 图谱登记 |
| graph_change_layer | G-L1（01_modules.md capability 行 p4-t3 备注 + HG-GRAPH-MODULES 签收行） |
| review_hat | 20（R1 审查文已落盘 · GO） |

### 人工闸

| human_gate_id | status | blocks_hats | 说明 |
|---------------|--------|-------------|------|
| HG-TASK-DRAFT | approved | 30 | approved 2026-11-18 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03796（夜间预授权）+ 委派书 p4-t3-manifest-domain-tags 为唯一范围真源 |
| HG-AUDIT-R1 | approved | 30 | approved 2026-11-18 · 同上授权 + R1 审查文 docs/harness/reviews/task_p4_t3_manifest_domain_tags_audit_R1_20261118.md（GO） |
| HG-GRAPH-MODULES | approved | 30 | approved 2026-11-18 · 同上授权（capability 行 p4-t3 备注属图谱登记义务 · 随 30 交付回填） |

## 背景

domain-pack-v1 / P4 泛化为 capability catalog 引入「部署级业务域」键：oa.readonly.v1.yaml:22 已声明 `domain: oa`，但 manifest.py:450-479 `_parse_and_validate` 现状既不读也不拒该键（「第三状态」静默忽略）——domain 键等于写了没生效。19 契约 §1/§2（commit e453a36 钉死）定稿消费口径：§1.2 域 id 词表 `[a-z0-9_]+`（无点号 · 与 capability id 词表独立禁互拼 R5）· §1.3 保留字（撞 allow_tags_any/allow_write_tags_any 现存值或字面量 `mcp` → 拒载 · R6 · oa 为既有合法域不溯及）· §2.1 注入规则（domain 注入该 manifest 全部 capability tags 集合 · 与手写 tags 并集去重 · 键缺失不注入 = 存量零 diff · CapabilityFilter 判序不动）· §2.2 oa 防双写漂移（R10/N7 · 手写面保留 · 注入作兜底 · 验收钉逐值一致）· §2.3 MCP 翻译条目 domain 真源=server 配置侧（翻译层禁加域逻辑 · 远端 tools/list 不可信）。「域天然落在 tags 上」（types.py:160-162 注记 · baseline.py:1-19 模块 docstring）——本波只动 loader 一处，消费面（types/registry/baseline）零改。本波依赖 P4-T1（capability manifest 基座 · 已 merge）；T6（run 树 DDL）已先合 master（142723ee + CLOSE 297363bd），本波 base 随之定为 297363bd。

## 范围

1. **loader 消费 domain 键**（19 §2.1）：`app/ops/capability/manifest.py`——`_parse_and_validate` 读顶层 `domain` 键（`_parse_domain`），注入该 manifest 全部 capability 的 tags：手写 tags ∪ {domain 值} **并集去重**（手写在前 · domain 兜底追加）；键缺失 = 不注入（builtin/ops.schedule/ops.write/testing 四份零 diff）；**domain=mcp 拒载**（R6 · 与 allow_tags_any 冲突裁定 · 19 §1.3/§2）；注入点选在循环内 `_entry_from_raw` 调用之前（spec 与 adapter——GenericHttpAdapter 持 spec 引用 manifest.py:689——同见最终 tags）；注入后 tags 参与 V1-V13 同源校验。
2. **域 id 词表校验**（19 §1.2 · R5）：新增 `_DOMAIN_ID_RE = [a-z0-9_]+` fullmatch（**不复用** :85 `_CAPABILITY_ID_RE` 点分词表 · 两词表独立禁止互拼）；domain 非 str 或词表外 → `ManifestError` 整文件拒载（承 :444-447 加载期强校验先例 · 不半套注册）。
3. **保留字校验**（19 §1.3 · R6）：新增 `_domain_reserved_words()` = (`DOMAIN_ALLOW_TAGS` − {"oa"}) ∪ {"mcp"} ∪ `OPS_CAPABILITY_ALLOW_WRITE_TAGS` env 逗分值（import baseline 公开名 `DOMAIN_ALLOW_TAGS`/`ENV_ALLOW_WRITE_TAGS` · baseline 只 import types 无环）；**仅在 domain 键存在时**才校验（存量五 manifest 零红结构性成立 · 默认 env 空零 diff）；oa 为既有合法域不溯及。
4. **oa 防双写漂移约定**（19 §2.2 · R10/N7）：oa manifest 手写 tags **保留不动**（:29 [oa,doc,readonly] · :96 [oa,org,readonly] · :157 [oa,todo,readonly,personal]）；注入恒 no-op（手写已含 oa → 不追加）；测试钉死「注入并集去重后 tags 集合 = 现状手写面**逐值一致**」作漂移哨兵。
5. **Policy/配额/allowlist 消费面回归**（委派书第 4 条 · platform 评审点）：测试断言 domain tag 注入后 strategy allowlist（baseline `DOMAIN_ALLOW_TAGS`）/ `OPS_CAPABILITY_EXTRA_MANIFESTS` / `OPS_CAPABILITY_ALLOW_WRITE_TAGS` 既有面**不被意外命中**——oa manifest 经 `baseline_filter(node_role)` 可见 ids ⊇ {oa.doc.search, oa.org.whois, oa.todo.mine} 不缩水；domain=hr 的临时 manifest 在默认 baseline 下**不可见**（hr 不在放行词表）；ops.write manifest 无 domain 键 → 零注入（既有电池守）。
6. **测试 + 图谱 + 过闸落盘**：新增 `tests/test_capability_manifest_domain.py`（autouse `_restore_defaults` + `_write_yaml` 承 test_capability_manifest.py 形态 · 真 PG 五键 blank 前缀）；`docs/_tech_graph/l1/01_modules.md` capability 行补 p4-t3 备注 + HG-GRAPH-MODULES 签收行（承 :48/:49 先例）；registry entry（status=active → close 波 closed 钉 wave_tip）· invokes by-task/p4-t3-manifest-domain-tags/{10,30,40,50} · R1 审查文 · task 档 active→done。

## 非范围

- 不动 prompt loader / 模板域机制（P4-T2 已合 6b2c7934）；不动 RAG 检索域隔离（P4-T4 并行）；不做 oa 域资产包落地（P4-T5）。
- 不动 `app/ops/capability/mcp/translator.py`（19 §2.3 · 翻译层禁加任何域逻辑 · 远端 tools/list 声明不可信 · MCP 翻译条目 domain 真源=server 配置侧 · translator 走 `_commit` 伪源 `mcp://<server_key>` 绕过 `_parse_and_validate` 天然零波及）。
- 不动 `baseline.py` `DOMAIN_ALLOW_TAGS` 词表（加域 = 后继波另行评审）；不动 `types.py`/`registry.py` 判序与 `CapabilityFilter` 消费面（§2.1 钉死「判序不动」）。
- 不改五份存量 manifest（builtin/oa/ops.schedule/ops.write/testing 零 bump 零内容变更——oa 手写面保留不动 · 本波只让 loader 读懂 domain 键）。
- 零新外部依赖（19 契约红线）；不碰 `alembic/` · `scripts/` · `.importlinter`（manifest→baseline 为 capability 行内路径 · 零新边）。

## 失败路径

- **词表互拼（R5）**：domain 词表无点号与 capability id 词表（manifest.py:85 允许点分）各自独立——实现上禁复用 `_CAPABILITY_ID_RE`；测试钉「domain 带点号/大写/连字符/空串/非 str」五负例拒载。
- **保留字漂移**：allow_write_tags_any env 面运行时变 → `_domain_reserved_words()` 在**加载期**读取 env 固化（与 baseline_filter 调用时读 env 同纪律 · 禁依赖 import 顺序巧合）；env 值带空白 strip 对齐 :46-50 语义。
- **env 渗入面失控**：`OPS_CAPABILITY_ALLOW_WRITE_TAGS` 仅在 domain 键存在时参与保留字校验 → 存量五 manifest（四份无 domain 键 + oa 合法）零红结构性成立；默认空 env 时保留字集 = {"mcp"} 最小面。
- **注入与 V13 mock 谓词交互**：domain=testing 的 manifest 会让其条目 tags 命中 `_MOCK_TAG_PREDICATE`——但 V13 tenant_scoped 豁免特例按 id 钉死（`_MOCK_TENANT_SCOPED_EXCEPTIONS` = {"testing.write.echo"} · :89）不扩面；裁定「注入后 tags 参与 V1-V13 同源校验」为契约语义（注入后 tags 即 spec 真源）。
- **ALLOW_WRITE_TAGS 意外命中写豁免**：若某 domain 与 env 放行值同值，注入会白捡 deny_write 豁免 → 保留字校验拒载同值 domain（纵深防御 · 见范围 3）；测试钉 env=hr 时 domain=hr 拒载。
- **oa 双写漂移（R10/N7）**：手写面与 domain 键未来可能不一致（如手写漏 oa）→ 注入作兜底补齐；逐值一致断言作漂移哨兵——断言红即说明手写面动了，强制同步评审。
- **翻译面域伪造（§2.3）**：远端 tools/list 不可信 → translator 零域逻辑；manifest 文件内 kind=mcp 条目注入自动覆盖（_build_adapter mcp 分支 :690-701 持 spec 引用同见注入后 tags）。
- **并行 agent 撞 registry.yaml / 01_modules.md 同区冲突**（T4 并行波）→ rebase origin/master 保留双方 entry 手动解，冲突块如实登记；PR CONFLICTING 时 CI 不触发须重推。
- **脏树期 wave_gate 红**为结构性常态（委派书钉明）；merge 与 pull 分开跑。

## 验收标准

- [x] domain→tags 注入：声明 domain 的 manifest 其全部 capability `spec.tags` 含 domain 值；capability 无 tags 键 → `tags == (domain,)`（tests/test_capability_manifest_domain.py::test_domain_injected_into_all_kinds 四 kind 断言绿）
- [x] 并集去重：手写 tags 已含 domain → 不重复追加（tags tuple 逐值等）；手写在前 domain 兜底追加序（手写 [a,b] + domain c → `("a","b","c")`）（test_domain_union_dedupe 断言绿）
- [x] domain=mcp 拒载：`ManifestError`（R6 · 19 §1.3/§2 钉死）（test_domain_reserved_mcp 断言绿 · 含不半套注册断言）
- [x] 非法 domain 词表拒载：大写 / 连字符 / 点号 / 空串（test_domain_invalid_vocabulary 参数化 4）+ 非 str（test_domain_non_string）五负例 → `ManifestError`（断言绿）
- [x] 保留字 env 面：`OPS_CAPABILITY_ALLOW_WRITE_TAGS=hr` 时 domain=hr → `ManifestError`；env 空时 domain=hr 合法注入（test_domain_reserved_from_env monkeypatch 双态断言绿）
- [x] oa 逐值一致（R10/N7）：真实 oa.readonly.v1.yaml 加载后三能力 tags tuple == (oa,doc,readonly) / (oa,org,readonly) / (oa,todo,readonly,personal)——注入恒 no-op 实证零 diff（test_oa_manifest_handwritten_tags_preserved 断言绿 · domain=oa 不拒载 test_domain_oa_existing_allowed 绿）
- [x] 消费面回归：oa manifest 经 `baseline_filter(node_role="t")` 可见 ids ⊇ {oa.doc.search, oa.org.whois, oa.todo.mine} 不缩水；domain=hr 临时 manifest 默认 baseline 下不可见（test_baseline_visibility_not_widened 断言绿）
- [x] 既有 manifest 电池回归零红：目标三文件 45 passed（真 PG opsdesk_test · 五键 blank）· capability 电池 673 passed/5 failed 与 master 同路径基线同 5 零新增；`ruff check app tests` All checks passed（0.15.21）；mypy manifest.py 2 errors 与 master 同 2（行号位移 · 零新增）；lint-imports 12 kept 0 broken；graph-compile.sh done OK；全量 pytest 以 CI 终裁（本地 solo 对照 36 vs 32 · 差 5 实证孤儿进程污染 dualproc 双侧重跑均 9 passed · 31 共有失败环境性既有）
- [x] 图谱：01_modules.md capability 行 p4-t3 备注 + HG-GRAPH-MODULES 签收行（已落盘 · graph-compile done OK）
- [x] 过闸四件：registry entry active · invokes {10,30,40}（50 待 CLOSE 波）· R1 审查文 GO · spec-wave task lint PASS

### 自检结论

验收十条全绿：①-⑦机制断言落 tests/test_capability_manifest_domain.py 14 用例全 passed（注入四 kind · 并集去重保序手写在前 domain 兜底 · domain=mcp 拒载不半套注册 · 词表五负例 · env 保留字双态 · oa 不溯及 R6 · oa 逐值哨兵 R10/N7）⑧oa/ops.write 两实仓件逐值钉死（oa 三能力手写面逐字一致 · ops.write tags==("ops","run_note","write") 零注入）⑨目标三文件 45 passed（真 PG opsdesk_test · 五键 blank）· capability 电池 673 passed/5 failed 与干净 master 同 5（顺序依赖既有 · 单跑均过）· 全量 solo 对照 36 vs 32 差 5 实证孤儿 pytest(pid 3801) dualproc 交叉污染（杀后双侧 9 passed · 31 共有=本地环境性既有）⑩ registry closed+wave_tip 钉版 · invokes 10/30/40/50 四件 · R1 审查文 GO · task lint PASS · graph-compile done OK · lint-imports 12 kept 0 broken · ruff All checks passed（0.15.21）· mypy 2 errors 与 master 同 2 零新增。feat PR #448 squash a87503d4 已合入 master（CI 四绿：check 18s ✓ · import-linter 10s ✓ · lint-wiki-delta 14s ✓ · pytest 2m20s ✓）。

## 必读列表

- 需求真源：`../ops-desk-workspace/docs/01-scope/03-general-agent/18-p4-generalization-design.md` §2.1（R6/R10）+ `19-p4-contracts.md` §1.2/§1.3/§2.1/§2.2/§2.3（commit e453a36 钉死口径）
- 代码锚：`app/ops/capability/manifest.py:85`（_CAPABILITY_ID_RE 点分词表 · 勿复用）· `:89-90`（V13 mock 特例按 id 钉死）· `:131`（ManifestError）· `:450-479`（_parse_and_validate 循环与注入位）· `:523-682`（_entry_from_raw · tags=tuple(str(t) for t in tags_raw) :643）· `:685-703`（_build_adapter 持 spec 引用 · mcp 分支）· `app/ops/capability/baseline.py:35`（DOMAIN_ALLOW_TAGS={"oa","mcp"}）· `:43-50`（ENV_ALLOW_WRITE_TAGS + env 读法先例）· `app/ops/capability/types.py:147-181`（CapabilityFilter 判序 · :160-162「域天然落在 tags 上」）· `app/ops/capability/registry.py:115/121`（allow_tags_any/allow_write_tags_any 交集谓词）
- manifest 面：`app/ops/capability/manifests/oa.readonly.v1.yaml:22`（domain: oa）· `:29/:96/:157`（手写 tags 三面）；builtin/ops.schedule/ops.write/testing 四份无 domain 键
- 翻译面：`app/ops/capability/mcp/translator.py:372`（翻译条目 tags=["mcp", server_key] · 零域逻辑保持）
- 测试先例：`tests/test_capability_manifest.py`（autouse `_restore_defaults` · `_write_yaml` · `_MIN_DECL` · ManifestError 拒载断言形态）· `tests/test_capability_domain_allowlist.py`（_OA_MANIFEST · baseline_filter ids 断言 · builder/supervisor 同 baseline 断言）
- 体例先例：`docs/tasks/done/task_p4_t2_prompt_domain_loader.md` · `docs/tasks/done/task_p4_t6_run_tree_ddl.md` · registry `docs/harness/audit_gates/registry.yaml`

## 思考轮

| 轮 | 结论 | early_stop |
|----|------|-----------|
| R0 | 范围对账（委派书六条 vs 19 契约 §1/§2 vs 18 §2.1 vs 代码锚）done | false |
| R1 | 失败路径推演（词表互拼 · 保留字漂移 · env 渗入 · V13 交互 · 写豁免意外命中 · oa 漂移 · 翻译面伪造 · 并行冲突 · 脏树红）done | false |
| R2 | 非范围边界（T2 prompt · T4 RAG · T5 oa 资产 · translator 零改动 · baseline 词表不动 · 判序不动 · 存量 manifest 零变更 · 零新依赖）done | false |
| R3 | 关键决策记录（注入位选定 · 保留字集构成 · oa 不溯及 · 注入参与 V1-V13 · 逐值一致哨兵）done | false |
| R4 | 体例对账（T2/T6 done 模板 · registry/invokes/审查文/图谱登记 · 仓规条款一）done | false |
| R5 | 收尾复核（验收 10 条全锚定 · base=297363bd 修正登记）done | false |

actual_last_round: R5

### R0 · 范围对账

委派书六条与 19 契约 §1/§2 + 18 §2.1 逐条对齐：loader 消费 domain 键注入 tags 并集去重 + domain=mcp 拒载（§2.1 + §1.3 R6）· 域 id 词表 [a-z0-9_]+ 校验禁互拼（§1.2 R5）· oa 防双写逐值一致（§2.2 R10/N7）· MCP 翻译条目 domain 真源=server 配置侧翻译层零改动（§2.3）· Policy/配额/allowlist 消费面回归（委派书第 4 条 platform 评审点）· 测试+图谱。勘察已定位全部锚点（manifest.py:85/:89-90/:131/:450-479/:523-682/:685-703 · baseline.py:35/:43-50 · types.py:147-181 · registry.py:115/121 · oa manifest :22/:29/:96/:157 · translator.py:372）。importlinter 核对：manifest.py → baseline.py 为 app.ops.capability 包内互导（capability 行内路径 · 零新边）；注入逻辑零新 import（os/re 已在 :27-28）。base 修正：委派书钉 370a137a，fetch 核实 T6 feat（142723ee）+ CLOSE（297363bd）已先合 → base=297363bd（委派书「git fetch 核实实际尖 · rebase 纪律」内裁定 · 偏差登记 1）。

### R1 · 失败路径推演

见「失败路径」节。推演增补：注入位必须在 `_entry_from_raw` 之前而非之后改写 spec——GenericHttpAdapter(:689)/McpAdapter(:701) 均持 spec 引用，after-the-fact 改写会造成 spec/adapter 视图分裂；循环内改写 raw（`raw = {**raw, "tags": merged}`）使两者同源。tags 非 list 的非法形态不在注入层拦（留给 :537-539 既有型错），避免掩盖错误面。`_commit` 伪源路径（translator :372 走 `mcp://<server_key>`）绕过 `_parse_and_validate` → 翻译条目天然不被注入，与 §2.3「domain 真源=server 配置侧」自洽；manifest 文件内 kind=mcp 条目则走正常解析被注入覆盖。

### R2 · 非范围边界

T2 prompt 模板域机制（已合 6b2c7934 · 部署级单域与本波 manifest 域键正交 · 19 §3 真源）；T4 RAG 检索域隔离（19 §4/§5 · 并行波）；T5 oa 域资产包落地（oa 覆盖件 7+4 份均为 T5）；translator.py 零改动（§2.3 钉死）；baseline.py DOMAIN_ALLOW_TAGS 词表不动（加域=后继评审）；types.py/registry.py 判序不动（§2.1「CapabilityFilter 判序不动」）；五份存量 manifest 零变更（本波只让 loader 读懂键 · oa 手写面保留）；零新外部依赖（红线）；alembic//scripts//.importlinter 禁入。

### R3 · 关键决策记录

- **注入位 = 循环内 `_entry_from_raw` 调用前改写 raw**：spec 与 adapter 同源见最终 tags（R1 推演）；改写为不可变拷贝 `{**raw, "tags": merged}` 不原地变异（raw_caps 来自 yaml.safe_load 虽为局部对象，保持函数式风格与 _decode 面一致）。
- **并集去重语义**：手写在前保持手写序稳定（oa 面零 diff 结构性成立——手写已含 oa → 集合判定命中 → 原样返回不追加）；domain 兜底追加仅在手写缺失时发生；去重判定用 `str(t)` 对齐 :643 tags 构造语义（非 str 元素先 str 化再比对）。
- **保留字集构成**：(DOMAIN_ALLOW_TAGS − {"oa"}) ∪ {"mcp"} ∪ env OPS_CAPABILITY_ALLOW_WRITE_TAGS 值。DOMAIN_ALLOW_TAGS 现值 {"oa","mcp"} → 实得 {"mcp"}；oa 显式排除（R6 「oa 不溯及」——oa 是既有合法域，拒载会破坏 19 §2.2 钉死的 oa manifest 消费面）；env 值纳入忠实 §1.3「allow_write_tags_any 现存值」（防写豁免意外命中 · 失败路径第五条）；仅 domain 键存在时调用（存量零红）。
- **加载期 env 读取纪律**：`_domain_reserved_words()` 在 `_parse_and_validate` 调用栈内读 env（load 时机固化 · 与 baseline.py:40-42 钉死的「调用时读取」同族纪律）；测试用 monkeypatch 双态（env=hr 拒 · env 空放行）。
- **注入参与 V1-V13 同源校验**：注入发生在 spec 构造前，校验面（含 V13 mock 谓词 :90）看到的即最终 tags——契约语义「注入后 tags 即真源」；V13 特例按 id 钉死不扩面（:89）。
- **逐值一致断言作漂移哨兵**：R10 验收不写成「注入后含 oa」（弱断言恒绿无哨兵价值），写成「tags tuple == 现状手写面逐值一致」——手写面任何漂移（漏值/改序）都会红，强制评审同步。

### R4 · 体例对账

照 task_p4_t2_prompt_domain_loader / task_p4_t6_run_tree_ddl done 模板：task 档结构（元信息表/人工闸表/背景/范围/非范围/失败路径/验收/自检/必读/思考轮/测试策略/修订记录）· registry entry（base=297363bd · allowed_app_files=[app/ops/capability/manifest.py] 单件 · allowed_tree_files 含测试/图谱/registry/task/review · allowed_tree_prefixes invokes 目录 · banned_prefixes=[alembic/, scripts/]）· invokes by-task 四件 {10,30,40,50} · R1 审查文 GO 机读词 · spec-wave@3.5.0 task lint PASS 为闸；图谱签收承 01_modules.md :48/:49 先例。仓规条款一遵守（走 20-R1 审查文非 --allow-no-review）。

### R5 · 收尾复核

验收 10 条逐条锚：注入/去重序/mcp 拒载/词表五负例/env 双态/oa 逐值一致/消费面回归（全新断言落 tests/test_capability_manifest_domain.py）+ 既有电池回归+全量+ruff/mypy/import-linter/graph-compile + 图谱两件 + 过闸四件。回退 = revert manifest.py 单件 + 删新测试文件 + revert 图谱/registry（零存量测试迁移面 · 零存量 manifest 变更面）。

## 实现备忘

### 偏差登记

1. **base 修正 370a137a → 297363bd**（R0 裁定）：委派书钉 master 尖 370a137a（T2 已合），fetch 核实 T6 feat PR #444（142723ee）+ CLOSE PR #446（297363bd）已先合——委派书本钉「git fetch 核实实际尖 · T6 并行波可能先合——rebase 纪律」，按实修正。T6 已合文件与本波零 app 面重叠（T6 触 models.py/run_store.py/runs_router.py/alembic · 本波触 capability/manifest.py 单件）；仅 registry.yaml 与 01_modules.md 同区追加位顺延。

2. **T4 先合 rebase**（40 波后 · PR #448 CONFLICTING 裁定）：feat PR 开出后 T4 feat PR #447 先合 master（e29f6a34）→ 本分支 rebase origin/master；01_modules.md 两冲突块按 task 档失败路径预案手动解——capability/lg_rag 行各保留双方叙事段 · HG-GRAPH-MODULES 签收表 T4/T3 两行并存；registry.yaml 自动合入双方 entry 零冲突。rebase 后复闸全绿（git 守卫 22 · 目标 45 · capability 电池 673 passed/5 failed 同基线同 5 · ruff/graph-compile/spec-wave verify）。CI 因 CONFLICTING 未触发，rebase 重推后触发（失败路径预案原文）。

### 限制登记

1. oa 域资产包落地归 P4-T5（委派书钉明 · 本波仅 loader 机制面 · oa manifest 内容零变更）。
2. prompt 域机制归 P4-T2（已合）；RAG 域隔离归 P4-T4（19 契约 §4/§5 真源 · 并行波）。
3. MCP 翻译条目 domain 真源=server 配置侧（19 §2.3）；翻译层本波零改动，server 配置侧 domain 注入属 MCP 配置面后继波。
4. 全量 pytest 环境性红（若有）与 base 297363bd 同路径基线对照登记，CI 终裁。

## 测试策略

pytest tests（CI 终裁 · 真 PG postgresql+asyncpg://ops:ops_password@localhost:5432/opsdesk_test · 五键 blank 前缀 OPS_HITL_PERSISTENCE= OPS_CAPABILITY_ALLOW_WRITE= OPS_CAPABILITY_ALLOW_WRITE_TAGS= OPS_CAPABILITY_PERSISTENCE= OPS_CAPABILITY_EXTRA_MANIFESTS=）；新增 tests/test_capability_manifest_domain.py 全绿；目标回归 tests/test_capability_manifest.py / tests/test_capability_domain_allowlist.py + capability 相关面全绿；全量回归环境性红与 base 297363bd 同路径基线逐签对照；ruff check app tests 绿（CI 钉版 0.15.21）；mypy app/ops/capability/manifest.py 绿；lint-imports 0 broken；scripts/graph-compile.sh done OK；allowed_app_files 单件机判。

## 修订记录

| 日期 | 修订 |
|------|------|
| 2026-11-18 | 落卡（夜间自动执行波 · 授权 issue Cyning12/ops-desk-workspace#23 m03064/m03796 · 来源 18 设计文 §2.1 + 19 契约 §1/§2 commit e453a36 · 委派书 p4-t3-manifest-domain-tags） |
| 2026-11-18 | 40 验证收口（验收 10 条全 [x] 逐条锚定 · 自检结论回填 · 目标 45 passed/电池 673+5 同基线/lint 四面绿/图谱 done OK · invoke_40 登记） |
| 2026-11-18 | CLOSE（feat PR #448 squash a87503d4 已合入 · CI 四绿 · registry 钉 wave_tip a87503d4+closed · task 迁 done · invoke_50 登记） |
