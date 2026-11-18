# R1 审查文 · task_p4_t3_manifest_domain_tags

> **审查帽**：20-task-audit（R1）
> **task**：docs/tasks/active/task_p4_t3_manifest_domain_tags.md
> **日期**：2026-11-18
> **授权链**：issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间预授权）· 需求真源 workspace 18-p4-generalization-design.md §2.1（R6/R10）· 口径真源 19-p4-contracts.md §1/§2（commit e453a36 钉死）· 委派书 p4-t3-manifest-domain-tags

## 结论

**GO · PASS · 零阻塞** — task 档范围/非范围/验收/failure_paths/思考轮（R0-R5）齐备，与 19 契约 §1.2/§1.3/§2.1-§2.3 钉死口径逐条对齐，修法裁定「_parse_domain 词表+保留字校验 · 循环内注入并集去重 · 键缺失不注入 · oa 逐值一致哨兵 · 翻译层零改动」为契约内最小改动面（allowed_app_files 单件 = app/ops/capability/manifest.py），可进 30。

## 核对项

| 项 | 结论 | 依据 |
|----|------|------|
| 范围6条 ↔ 委派书/19 §1/§2 | 一致 | loader 消费 domain 键注入 tags 并集去重+mcp 拒载（§2.1+§1.3 R6）· 域 id 词表 [a-z0-9_]+ 禁互拼（§1.2 R5）· 保留字校验（§1.3）· oa 防双写逐值一致（§2.2 R10/N7）· 消费面回归（委派书第 4 条）· 测试+图谱+过闸 |
| 非范围 | 一致 | prompt 域机制 T2 已合 · RAG 域隔离 T4 · oa 资产 T5 · translator.py 零改动（§2.3）· baseline 词表不动 · types/registry 判序不动 · 五份存量 manifest 零变更 · 零新依赖 · alembic//scripts//.importlinter 禁入 |
| 验收标准 | 10 条全机判锚 | 注入 · 并集去重序 · mcp 拒载 · 词表五负例 · env 双态 · oa 逐值一致 · 消费面回归（可见不缩水+hr 不可见）· 既有电池回归+全量+ruff/mypy/import-linter/graph-compile · 图谱两件 · 过闸四件 |
| failure_paths | 9 条 | 词表互拼 · 保留字漂移 · env 渗入 · V13 交互 · 写豁免意外命中 · oa 漂移 · 翻译面伪造 · 并行冲突 · 脏树红常态 |
| 思考轮 | R0-R5 齐 · actual_last_round=R5 | 表头 `| 轮 | 结论 | early_stop |` 合规 |
| 人工闸表 | 三行 approved | HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES · issue #23 授权 |
| 体例 | 照 p4-t2/p4-t6 done 模板 | registry/invokes/图谱签收承 T2/T6 先例 |
| 仓规条款一 | 遵守 | 本审查文即 20-R1 路径 · 未用 --allow-no-review |

## 关键决策复核

- **注入位选定成立（spec/adapter 同源）**：注入点在 _parse_and_validate 循环内 _entry_from_raw 调用之前改写 raw（不可变拷贝 `{**raw, "tags": merged}`）——GenericHttpAdapter（manifest.py:689）与 McpAdapter（:701）均持 spec 引用，after-the-fact 改写 spec 会造成 spec/adapter 视图分裂；循环内改写使 spec 构造（:643 tags=tuple(str(t) for t in tags_raw)）与 adapter 同源见最终 tags。tags 非 list 非法形态不在注入层拦（留给 :537-539 既有型错），不掩盖错误面。
- **词表纪律成立（R5 禁互拼）**：新增 _DOMAIN_ID_RE=[a-z0-9_]+ fullmatch，不复用 :85 _CAPABILITY_ID_RE（允许点分域）——domain 只作 tags 注入值不进 capability id 拼接面；测试钉「带点号/大写/连字符/空串/非 str」五负例拒载，非法形态整文件 ManifestError（承 :444-447 加载期强校验先例 · 不半套注册）。
- **保留字集构成成立（§1.3 R6）**：(DOMAIN_ALLOW_TAGS − {"oa"}) ∪ {"mcp"} ∪ env OPS_CAPABILITY_ALLOW_WRITE_TAGS 值——DOMAIN_ALLOW_TAGS 现值 {"oa","mcp"}（baseline.py:35）实得 {"mcp"}；oa 显式排除（「oa 为既有合法域不溯及」· 拒载 oa 会破坏 §2.2 钉死的 oa manifest 消费面）；env 值纳入忠实「allow_write_tags_any 现存值」字面，防「domain 与写放行值同值白捡 deny_write 豁免」意外命中（纵深防御 · 测试钉 env=hr 时 domain=hr 拒载）；import baseline 公开名 DOMAIN_ALLOW_TAGS/ENV_ALLOW_WRITE_TAGS（baseline 只 import types · 包内互导无环 · .importlinter 零新边）；**仅 domain 键存在时**才校验 → 存量五 manifest（四份无 domain 键 + oa=oa 合法）零红结构性成立 · 默认空 env 时保留字集={"mcp"} 最小面零 diff。
- **加载期 env 读取纪律成立**：_domain_reserved_words() 在 _parse_and_validate 调用栈内读 env（load 时机固化），与 baseline.py:40-42 钉死的「baseline_filter() 调用时读取 · 禁依赖 import 顺序巧合」同族纪律；测试用 monkeypatch 双态断言。
- **并集去重语义成立（§2.1）**：手写在前保持手写序稳定（oa 三面手写已含 oa → 集合判定命中 → 原样返回 → 注入恒 no-op → 零 diff 结构性成立）；domain 兜底追加仅手写缺失时发生；去重判定用 str(t) 对齐 :643 构造语义。
- **oa 逐值一致哨兵成立（§2.2 R10/N7）**：验收钉「tags tuple == 现状手写面逐值一致」而非「含 oa」弱断言——手写面任何漂移（漏值/改序）即红，强制同步评审；oa manifest 三面保留不动（本波零内容变更）。
- **翻译层零改动成立（§2.3）**：translator.py:372 翻译条目经 _commit 伪源 mcp://<server_key> 绕过 _parse_and_validate → 天然不被注入（与「domain 真源=server 配置侧 · 远端 tools/list 不可信」自洽）；manifest 文件内 kind=mcp 条目走正常解析被注入覆盖（_build_adapter mcp 分支持 spec 引用同见注入后 tags）。
- **消费面回归裁定成立（委派书第 4 条 platform 评审点）**：注入只加 tags 不动 CapabilityFilter 判序（types.py:147-181 零改 · §2.1 钉死）；「域天然落在 tags 上」（types.py:160-162）使 baseline DOMAIN_ALLOW_TAGS 豁免自然承接 oa 域——测试断言 oa 可见 ids 不缩水 + domain=hr 临时 manifest 默认 baseline 不可见（不被意外命中）双向钉死。
- **V13 交互裁定成立**：注入后 tags 参与 V1-V13 同源校验（注入即真源）；V13 mock 特例按 id 钉死（_MOCK_TENANT_SCOPED_EXCEPTIONS={"testing.write.echo"} · :89）——domain=testing 注入只让 tags 命中谓词，特例不扩面。

## 偏差确认

一项（已入 task 档 R0 + 偏差登记 1）：base 修正 370a137a → 297363bd——委派书钉 master 尖 370a137a（T2 已合），fetch 核实 T6 feat PR #444（142723ee）+ CLOSE PR #446（297363bd）已先合；委派书本钉「git fetch 核实实际尖 · T6 并行波可能先合——rebase 纪律」，属委派书内裁定非范围变化。其余无偏差：委派书六条全覆盖无裁剪。

## 机读通过词

PASS（spec-wave task lint 命令：`npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_p4_t3_manifest_domain_tags.md`）
