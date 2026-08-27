# Invoke · 00 统筹 · agent-host-plan（H1–H5 拆 task）

> **日期**：2026-08-27  
> **帽**：00  
> **规划**：`docs/spec/agent-infra/02_agent_host_plan_v0.md`（HG-SPEC-SIGNOFF=**approved**）

---

## 派发计划

| 序 | 波次 | task | 分支 | 前置 | 00 动作 |
|---|---|---|---|---|---|
| 1 | H1 | `task_lg_rag_supervisor_capability_catalog.md` | `task/lg-rag-supervisor-capability-catalog` | — | **当前棒**：HG 已签 · 00 统筹中 → 30 |
| 2 | H2 | `task_capability_policy_sandbox.md` | `task/capability-policy-sandbox` | H1 CLOSE | 待 H1 关账 |
| 3 | H3 | `task_chat_session_continuity.md` | `task/chat-session-continuity` | H2 推荐 | 待 |
| 4 | H4 | `task_prompt_assembly_p1.md` | `task/prompt-assembly-p1` | H1 CLOSE 后可并行 | 待 |
| 5 | H5 | `task_skill_registry_p0.md` | `task/skill-registry-p0` | H4 CLOSE | 待 |

---

## 颗粒度说明

- **五 task 一轨**：与 capability-gateway P0–P4 切分方式一致；每棒独立分支 + CLOSE。  
- **H3 未再拆**：H3-a–d 同属 Session 连续性，单 task 内验收；若消息表迁移过大，00 可再拆 H3a/H3b。  
- **H4 未再拆**：首包 `app/ops/prompts/` + 1–2 节点迁移为一棒；全仓 prompt 迁移留后续。  
- **H5 依赖 H4**：provide 需 Prompt slot。

---

## 硬约束（写入各 30 Prompt）

见 `02_agent_host_plan_v0.md` §4。

---

## 验证（合并前每棒）

```bash
ruff check <触及路径>
pytest tests/test_lg_rag_multi.py tests/test_capability*.py ...  # 按棒裁剪
./scripts/graph-compile.sh   # 若触图谱
npx dsh-coding-kit verify --target . --task docs/tasks/active/task_<slug>.md
```

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-27 | SPEC 签收；拆 H1–H5 active task |
