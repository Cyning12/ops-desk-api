# invoke · 10 起草 · p4-t3-manifest-domain-tags

> **task_slug**：p4-t3-manifest-domain-tags
> **日期**：2026-11-18
> **授权**：issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间预授权 · 委派书 p4-t3-manifest-domain-tags）

## 内容

1. 落卡 docs/tasks/active/task_p4_t3_manifest_domain_tags.md（体例照 docs/tasks/done/task_p4_t2_prompt_domain_loader.md / task_p4_t6_run_tree_ddl.md）：Harness 元信息表（task_slug/base=297363bd/关联 issue/wiki_delta n/a/graph_change_layer G-L1/review_hat 20）· 人工闸表三行 approved · 背景（oa manifest :22 domain 键现状静默忽略「第三状态」· 19 契约 §1/§2 commit e453a36 钉死口径）· 范围 6 条 · 非范围 5 条 · 失败路径 9 条 · 验收标准 10 条 · 必读列表 · 思考轮 R0-R5（actual_last_round=R5）。
2. 勘察结论入档：manifest.py:85 _CAPABILITY_ID_RE 点分词表（勿复用 · R5 禁互拼）· :89-90 V13 mock 特例按 id 钉死 · :131 ManifestError · :450-479 _parse_and_validate 循环（注入位 = _entry_from_raw 调用前）· :523-682 _entry_from_raw（tags=tuple(str(t) for t in tags_raw) :643 · tags 型错面 :537-539）· :685-703 _build_adapter（GenericHttpAdapter/McpAdapter 均持 spec 引用 → 注入必须先于构造）；baseline.py:35 DOMAIN_ALLOW_TAGS={"oa","mcp"} · :43-50 ENV_ALLOW_WRITE_TAGS + env 读法先例；types.py:147-181 CapabilityFilter 判序（:160-162「域天然落在 tags 上」）；registry.py:115/121 交集谓词；oa manifest :22 domain: oa + :29/:96/:157 手写 tags 三面；builtin/ops.schedule/ops.write/testing 四份无 domain 键；mcp/translator.py:372 翻译条目走 _commit 伪源绕过解析面。
3. 口径定稿（19 §1.2/§1.3/§2.1-§2.3 · commit e453a36）：域 id 词表 [a-z0-9_]+ fullmatch 非法拒载 · 保留字 (DOMAIN_ALLOW_TAGS-{"oa"})∪{"mcp"}∪env 值（仅 domain 键存在时校验 · oa 不溯及 · domain=mcp 拒载）· 注入=手写 ∪ {domain} 并集去重兜底追加（键缺失不注入 · 判序不动）· oa 逐值一致哨兵（R10/N7）· 翻译层零改动。
4. 裁定登记（R3）：注入位 = 循环内 _entry_from_raw 前不可变拷贝改写 raw（spec/adapter 同源）；tags 非 list 非法形态不在注入层拦（留给 :537-539 既有型错）；保留字加载期读 env（承 baseline 调用时读 env 纪律）；注入参与 V1-V13 同源校验（注入后 tags 即真源）；逐值一致断言作漂移哨兵（非弱断言）。
5. base 修正登记（偏差 1）：委派书钉 370a137a · fetch 核实 T6 feat（142723ee）+ CLOSE（297363bd）已先合 → base=297363bd（委派书「git fetch 核实实际尖 · rebase 纪律」内裁定）。
6. registry entry（status=active · base=297363bd · allowed_app_files=[app/ops/capability/manifest.py] 单件 · banned_prefixes=[alembic/, scripts/]）。

## 验证台账

| 检查 | 结果 |
|------|------|
| npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p4_t3_manifest_domain_tags.md | PASS |
| npx spec-wave verify --target . --task docs/tasks/active/task_p4_t3_manifest_domain_tags.md | 人工闸三行 approved（30 放行依据） |

## 偏差

1. base 修正 370a137a → 297363bd（T6 先合 · 委派书 rebase 纪律内裁定）。

## 结果

10 起草完成 · 进 20-R1 审查文。
