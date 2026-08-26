# Invoke：00 · agent-infra-upgrade（总轨统筹）

| 字段 | 值 |
|------|-----|
| hat_id | 00 |
| 总轨 slug | `agent-infra-upgrade` |
| 方案 | **A**：先合 docs 分层 PR，再开实现子分支 |
| 签收 | 2026-08-26 维护者：选 A · 签收子 task 清单 · 授权 00 代签全过程文档 · 开工 |
| 真值 | `docs/spec/agent-infra/01_upgrade_roadmap.md` |

---

## 派发计划表（顺序钉死）

| 序 | 波次 ID | 子 task slug | 状态 | 分支建议 | 备注 |
|---|---|---|---|---|---|
| 0 | docs-hierarchy | `agent-infra-spec-hierarchy` | **CLOSE PASS**（[#65](https://github.com/Cyning12/ops-desk-api/pull/65)） | `docs/agent-infra-spec-hierarchy` | 已归档 done/ |
| 1 | cap-portable-core | `cap-portable-core` | **00 机械验收 PASS · 待 push/PR** | `task/cap-portable-core` | U1+U2；本地 `ba29598` |
| 2 | so-schema-hygiene | `so-schema-hygiene` | **验收 PASS · 开 PR** | 可同 PR 穿插或紧随 | H1；不得抢先大改 SO |
| 3 | cap-mcp-real | `cap-mcp-real` | 排队 | `task/cap-mcp-real` | 另开；CI 默认不外网 |
| 4 | so-complete-adopt | — | **默认跳过** | — | 须维护者再授权 |
| 收官+ | repo hygiene | `repo-branch-task-hygiene`（拟） | 登记待办 | 另开 | 全轨验收后清理分支/陈旧 task（DEF-002） |

**穿插规则**：2 可与 1 同 PR 穿插，但须 1 闸过且不得颠倒主序。  
**硬禁**：改 `app/ops/chat/graph.py`；Agently 运行时；Host 校验变可选 Capability；默认动态 `compile`；混入其他 active task。

---

## 波次 1 · 00 机械验收（2026-08-26）

| 检查项 | 结果 |
|---|---|
| pytest `test_capability_gateway` + `test_lg_rag_multi` | **30 passed** |
| ruff `app/ops/capability` + 相关 tests | **PASS** |
| `rg langgraph app/ops/capability` | 仅 `extras/langchain.py` |
| 默认导出无 `as_tool_node` / `as_structured_tools` | **PASS** |
| `app/ops/chat/graph.py` vs master | **零 diff** |
| `dsh-coding-kit verify --task …cap_portable_core` | **PASS** |
| graph-compile | **exit 0**（时间戳噪声已丢弃） |
| Agently | 无 |

结论：**波次 1 实现可合入**；不升 SPEC v1。本地 ahead 1（`ba29598`）**未 push**。

---

## 本回合动作

1. ~~波次 0 docs PR~~ **DONE** · [#65](https://github.com/Cyning12/ops-desk-api/pull/65) MERGED · CLOSE PASS  
2. ~~rebase + 派 30~~ **DONE**  
3. ~~00 机械验收~~ **PASS**  
4. **阻塞/待维护者**：是否 push `task/cap-portable-core` 并开 PR；是否立即开波次 2 `so-schema-hygiene`

---

## 下一棒

- 维护者授权 → push + 开 PR（波次 1）  
- 然后起草/派发 `so-schema-hygiene`  
- 收官后 `repo-branch-task-hygiene`（DEF-002）

| 2026-08-26 | 00 签收开工 · 方案 A |
| 2026-08-26 | #65 MERGED · 波次 0 CLOSE PASS · 派 30 |
| 2026-08-26 | 30 落地 · 00 机械验收 PASS · 待 push/PR |

| 2026-08-26 | #66 MERGED · 波次2 验收 PASS · PR 推进 |
