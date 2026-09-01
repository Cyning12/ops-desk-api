# 草稿：Host · 沟通 Agent 嵌套 coding-kit（实现方案 · 供审）

> **状态**：draft · **暂缓开 C0**（2026-08-31 维护者：主线 Spec/能力仍不足；**先 chat 废弃 + lg-rag 迁移联调**，再议本方案）  
> **上游**：[`02_agent_host_plan_v0.md`](../spec/agent-infra/02_agent_host_plan_v0.md)（H1–H5 CLOSE）· kit FEEDBACK hat-identity  
> **产品入口（草稿）**：web `/obs` 现为 harness status fixture；演进为「沟通 Agent」控制台候选  
> **非目标本波**：改 Cursor/AGENTS 当 Host；业务 Chat 每轮跑完整 10→30 · **不挡 T2 联调**

---

## 0. 一句话

**一套 Process Kernel（coding-kit）+ Host PromptAssembly 多 Pack**；沟通 Agent **全嵌套**闸/task/verify；业务 lg-rag/Chat **只借鉴**角色与策略，不全嵌套。

---

## 1. 模块切分

```text
Host Runtime
├── PromptAssembly（H4 已有方向）
│   ├── pack=product   → lg-rag / 业务答
│   └── pack=comms     → 沟通：澄清 → 起草 task/SPEC → 提示人闸
├── CapabilityGateway + Policy（H2）
│   ├── harness.verify      → npx dsh-coding-kit@pin verify …
│   ├── harness.task_lint   → task lint / lint-wiki-delta
│   └── harness.status      →（可选）status/timeline JSON → obs 投影
├── SessionContinuity（H3）
│   └── comms thread 与 product thread 隔离（勿混业务答与立项）
└── SkillRegistry（H5）
    └── 可选加载 harness delegate-only / re-anchor（短 Skill）
        ≠ 替代 verify
```

---

## 2. 分波实现（建议）

| 波 | slug（建议） | 内容 | 依赖 |
|---|---|---|---|
| **C0** | `host-comms-boundary-spec` | SPEC：comms vs product 意图路由、产物路径（`docs/tasks/`）、禁代签闸 | 文档 only · **暂缓** |
| **C1** | `host-harness-cli-capability` | Capability `harness.verify` / `task_lint`；Policy 默认关；env 钉 `DSH_CODING_KIT_VERSION` | H2 ✓ |
| **C2** | `host-comms-prompt-pack` | PromptAssembly `pack=comms`：槽位 = kit FRAGMENT_00_delegate + task 模板字段清单 + 对话策略 | H4 + kit 1.10+ FRAGMENT |
| **C3** | `host-comms-task-writer` | 受控写盘：仅允许写 `docs/tasks/active|draft` 与 invoke 草稿；dry-run 默认；人确认后落盘 | C1+C2 |
| **C4** | `host-obs-comms-ui` | `/obs`：fixture → 真 status +「发起沟通」入口（web 另 task） | C1 status |

**顺序**：C0 → C1 → C2 → C3；C4 可与 C3 尾并行（跨仓 web）。**当前主线优先**：T2 联调 → chat 废弃迁移，**不开 C0**。

---

## 3. 关键要点（C1）

```text
register("harness.verify", risk=high, policy_default=block)
invoke args: { task_path?, target? }
impl: subprocess
  npx --yes dsh-coding-kit@${OPS_KIT_PIN} verify --target . --task <path> --json
return: CapabilityResult(ok, data=parsed json, error=policy_blocked|cli_failed)
```

- **禁止**通用 shell Capability 代替本白名单。  
- CI / 本地单测：mock subprocess，不断网装 npm（可 fixture 固定 JSON）。

---

## 4. Prompt 工程（C2）· 不是第二套 PE

| 层 | 内容 |
|---|---|
| System 短 | kit `FRAGMENT_hat_reanchor` + `FRAGMENT_00_delegate_only`（待 1.10） |
| 换阶段 | 加载 10-task / 00 全文（按需），不 always |
| 工具结果 | verify JSON 注入「当前 may_start_30 / 缺哪闸」 |
| 业务 Pack | 与 comms **分 session**；共用 Gateway，不共用 system |

→ **一套内核 · 两套 Pack**，不是两套互不共享的 Prompt 仓库。

---

## 5. 与业务 Chat / lg-rag

| | 沟通 Pack | 产品 Pack |
|---|---|---|
| 目标 | 立项 / 写 task | 答业务 / 跑 agent |
| kit | 全嵌套过程对象 + CLI | 不跑 HG 链 |
| 写仓 | 仅文档 task（C3） | 不写 harness 文档 |

意图路由（C0）：关键词或显式「立项/开 task」→ comms；默认 product。

---

## 6. 风险与闸

| 风险 | 缓解 |
|---|---|
| 模型代签 approved | Prompt 禁令 + 写盘前人确认；闸真值仍在 task 表 |
| 任意 npx/shell | 仅白名单 Capability + Policy |
| Skills 误以为够用 | SPEC 写明 Skills≠verify；C1 必做 |
| 00 亲自改 app | Host comms **无**写 `app/` 工具；写盘 allowlist 仅 docs/tasks |

---

## 7. 验收草图

- C1：policy 关 → `policy_blocked`；开 → mock verify JSON 回传  
- C2：comms 会话输出含 task 字段清单 / 委派或待人签提示，无「已代签」  
- C3：dry-run 出 diff；确认后文件落盘且 `task lint` 可跑  
- 联调：kit ≥1.10 FRAGMENT sync 到仓后，Host 槽位读同一文件

---

## 8. 待你拍板

1. ~~C0 SPEC 是否现在开 task？~~ → **暂不开**（先 T2–T6 chat 弃用迁移）  
2. 沟通写盘落点：仅 api 仓 `docs/tasks/`，还是 workspace 统筹？（延后）  
3. `/obs` 是否定为 comms UI 主入口，还是独立路由？（延后）

---

## 修订记录

| 日期 | 说明 |
|---|---|
| 2026-08-31 | 初稿供审 · 未开 task |
| 2026-08-31 | 维护者：暂缓 C0；主线先完成 chat→lg-rag 迁移联调 |
