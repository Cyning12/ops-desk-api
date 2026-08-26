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
| 1 | cap-portable-core | `cap-portable-core` | **派 30 中** | `task/cap-portable-core` | U1+U2；优先 |
| 2 | so-schema-hygiene | `so-schema-hygiene` | 排队 | 可同 PR 穿插或紧随 | H1；不得抢先大改 SO |
| 3 | cap-mcp-real | `cap-mcp-real` | 排队 | `task/cap-mcp-real` | 另开；CI 默认不外网 |
| 4 | so-complete-adopt | — | **默认跳过** | — | 须维护者再授权 |
| 收官+ | repo hygiene | `repo-branch-task-hygiene`（拟） | 登记待办 | 另开 | 全轨验收后清理分支/陈旧 task（DEF-002） |

**穿插规则**：2 可与 1 同 PR 穿插，但须 1 闸过且不得颠倒主序。  
**硬禁**：改 `app/ops/chat/graph.py`；Agently 运行时；Host 校验变可选 Capability；默认动态 `compile`；混入其他 active task。

---

## 验证命令（每子 task）

```text
npx dsh-coding-kit task lint --file docs/tasks/active/task_<slug>.md
npx dsh-coding-kit verify --target . --task docs/tasks/active/task_<slug>.md
ruff check app/ops/capability
pytest tests/test_capability_gateway.py tests/test_lg_rag_multi.py -q --tb=short
./scripts/graph-compile.sh   # 仅触及图谱时
```

---

## 本回合动作

1. ~~波次 0 docs PR~~ **DONE** · [#65](https://github.com/Cyning12/ops-desk-api/pull/65) MERGED · CLOSE PASS  
2. ~~rebase `task/cap-portable-core`~~ **DONE**  
3. **进行中**：GATE_VERIFY PASS → 派 30（U1+U2）

---

## 下一棒

- 30 完成 → 00 机械验收 → 开实现 PR  
- 然后 `so-schema-hygiene`  
- 收官后 `repo-branch-task-hygiene`（DEF-002）

| 2026-08-26 | 00 签收开工 · 方案 A |
| 2026-08-26 | #65 MERGED · 波次 0 CLOSE PASS · 派 30 |
