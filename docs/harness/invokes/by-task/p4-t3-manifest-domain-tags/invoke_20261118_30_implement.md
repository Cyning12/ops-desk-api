# invoke · 30 阶段 · p4-t3-manifest-domain-tags

> task_slug: p4-t3-manifest-domain-tags
> 日期: 2026-11-18
> 授权: 人工闸 HG-AUDIT-R1 / HG-GRAPH-MODULES / HG-PILOT-OPSDESK-GLAYER 全 approved（task 人工闸表 · VERIFY: PASS 放行）

## 内容

1. app/ops/capability/manifest.py docstring 增「域键消费」段（19 契约 §1/§2 · MCP 翻译条目 domain 真源 server 配置侧 §2.3 不经本 loader）。
2. import 增 DOMAIN_ALLOW_TAGS / ENV_ALLOW_WRITE_TAGS（from app.ops.capability.baseline · 置于 adapters.local_fn 与 errors 之间 · ruff I 序合规 · baseline 仅 import types 无环）。
3. _DOMAIN_ID_RE = re.compile(r"^[a-z0-9_]+$")（注释钉 R5：与 _CAPABILITY_ID_RE 点分词表独立禁互拼）。
4. _domain_reserved_words() -> frozenset[str]：加载期读 env（承 baseline 调用时读取纪律）· 返回 (DOMAIN_ALLOW_TAGS − {"oa"}) | {"mcp"} | env_tags · 仅 domain 键存在时调用。
5. _parse_domain(data, *, path) -> str | None：键缺失→None（零注入）· 非 str 或词表外→ManifestError「manifest.domain 非法（词表 [a-z0-9_]+ · 与 capability id 词表独立禁互拼）」· 撞保留字→ManifestError「manifest.domain 撞保留字（…19 契约 §1.3 R6）」。
6. _inject_domain_tag(raw, *, domain)：tags 键缺失→{**raw, "tags": [domain]} · 非 list→原样（留给 _entry_from_raw 报型错）· domain 已含→原样（oa 恒 no-op）· 否则末尾追加 {**raw, "tags": [*tags_raw, domain]}。接线 _parse_and_validate：root _reject_secret_keys 后解析一次 · 循环内 spec/adapter 同源注入。
7. tests/test_capability_manifest_domain.py 新落（297 行 · 14 用例）：四 kind 注入/并集去重/键缺失零注入/词表参数化 4/非 str/保留字 mcp/env 双例（拒+放）/oa 不溯及 R6/oa 逐值三元组哨兵 R10+N7/ops.write 零注入/baseline 可见性双向（oa http 不缩水 · 新域 hr http 不白捡）。
8. 图谱回写 docs/_tech_graph/l1/01_modules.md：capability 行末追加 P4-T3 叙事段（词表独立 R5 · 保留字算法 · oa 不溯及 · 并集去重 · MCP §2.3）+ HG-GRAPH-MODULES 签收行（承 :48 先例 · 零新路由/表/SSE/迁移 · .importlinter 零改动 · l0 未触及）。

## 验证台账

| 检查 | 结果 |
| --- | --- |
| pytest tests/test_capability_manifest_domain.py | 14 passed（0.20s） |
| ruff check app tests（CI 钉版 0.15.21） | All checks passed! |
| ruff format --check app tests | green |
| pytest -k capability 对照（worktree vs 干净 master 主 checkout） | 13 failed / 665 passed vs 13 failed / 651 passed · 同 13 个既有顺序依赖失败 · 差值 14 = 新文件用例数 · 零新增 |
| 全量电池 solo 对照（worktree vs master 各自单跑） | 36 failed vs 32 failed · 差 5 全为 test_multi_replica_dualproc.py——系孤儿 pytest 进程（pid 3801）交叉污染，杀后双侧重跑该文件均 9 passed · 31 个共有失败为本地环境既有（DB 型 · CI 用 pgvector:pg16 service 判定）· 零新增可归因 |
| git 守卫（post-commit 在途面清空后） | tests/test_wave_gate_registry.py + tests/test_lg_rag_write_replay_guard.py 22 passed |

## 偏差

- 无新增（base=297363bd 修正已于 task 档登记为偏差 1）。

## 结果

30 实现完成（提交 769f7126）· 进 40 验证波。
