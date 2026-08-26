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
| 0 | docs-hierarchy | `agent-infra-spec-hierarchy` | **进行中** | `docs/agent-infra-spec-hierarchy` | 独立 PR → master |
| 1 | cap-portable-core | `cap-portable-core` | **已起草·待 #65** | `task/cap-portable-core`（自最新 master） | U1+U2；优先 |
| 2 | so-schema-hygiene | `so-schema-hygiene` | 排队 | 可同 PR 穿插或紧随 | H1；不得抢先大改 SO |
| 3 | cap-mcp-real | `cap-mcp-real` | 排队 | `task/cap-mcp-real` | 另开；CI 默认不外网 |
| 4 | so-complete-adopt | — | **默认跳过** | — | 须维护者再授权 |
| 收官+ | repo hygiene | `repo-branch-task-hygiene`（拟） | 登记待办 | 另开 | **全轨 SPEC/实现验收后**：清理本地+远程无效分支与陈旧 task 卫生 |

**穿插规则**：2 可与 1 同 PR 穿插，但须 1 闸过且不得颠倒主序。  
**硬禁**：改 `chat/graph.py`；Agently 运行时；Host 校验变可选 Capability；默认动态 `compile`；混入其他 active task。

---

## 子 task 清单（签收）

维护者 2026-08-26 签收本表方案。波次 4 默认不做。

---

## 验证命令（每子 task）

```text
npx dsh-coding-kit task lint --file docs/tasks/active/task_<slug>.md
npx dsh-coding-kit verify --target . --task docs/tasks/active/task_<slug>.md
# 实现波次另加：
ruff check app/ops/capability app/ops/structured_output app/ops/lg_rag
pytest tests/ -q --tb=short   # 按 task test_strategy_note 裁剪
./scripts/graph-compile.sh    # 仅触及图谱时
```

---

## 本回合动作

1. ~~落盘波次 0 task + R1 + invokes；00 代签闸~~ **DONE**
2. ~~docs-only commit → push → 开 PR~~ **DONE** → [#65](https://github.com/Cyning12/ops-desk-api/pull/65)
3. **阻塞**：待维护者 merge #65
4. merge 后：关账波次 0 → 从最新 master 开 `task/cap-portable-core` 并跑 10/20 → 派 30

---

## 下一棒

- **立即（维护者）**：审阅并 merge [#65](https://github.com/Cyning12/ops-desk-api/pull/65)
- **然后（00）**：起草并闸过 `cap-portable-core` → 派 30（00 不改 app/tests）
- **收官后**：开 `repo-branch-task-hygiene`（DEF-002）

| 2026-08-26 | 00 签收开工 · 方案 A · 派发计划落盘 |
| 2026-08-26 | 波次 0 PR #65 OPEN；DEF-002 已登记 |
| 2026-08-26 | 波次 1 task 已起草于分支 `task/cap-portable-core`（闸已签·30 待 #65） |
