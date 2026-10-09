# PROMPT · 交还发现者 00：签发审批消费回路 → 接续下一阶段研发

> 用途：复制本文件全文到**发现该缺口的 00 窗口**（D2 testing-write-capability 统筹窗）首发。
> 生成：2026-10-09 · 讨论窗 00 · 维护者令原话：「D2的任务交由发现的agent来完成，生成Prompt，在他完成签发审批消费回路后，拿到最新的spec大纲，然后再开始下一步任务研发，授权其签收之后所有过程文档」

---

你是发现「签发审批消费回路」缺口的 00（delegate-only：只委派不亲改实现码）。Open Folder = `ops-desk-api` 仓根。维护者已授权你**签收本 Prompt 覆盖的全部后续过程文档**（SPEC/审查文/invoke/CLOSE 记录的 00 代录签录链）。

## 第一棒：签发审批消费回路（你发现并留转的缺口）

**缺口真值**（你自己 40 实录的留档，`docs/tasks/done/task_testing_write_capability.md:144/249/259`）：

- 委派令牌闸「签发审批」目前只有**半回路**：能拦（`hitl.waiting` · `blocked_by=delegation_issue_hitl_required`）、能批（decide 200），但**批准没有被图消费**——`resume` 409，因为审批单 `unlock_subtask_id` 为空（`app/ops/hitl/router.py:404-410`），被拦子任务不知道该解锁谁，run 无法真正续跑。
- 你留转的候选方向：并入 strategy 候选映射 env 口作为第四道门（维护者已知悉，具体方案由 SPEC 裁定上抛）。
- 你窗已有后续 SPEC 在起草（CLOSE 留转 ② 实录）——继续完成它。

**链路**：10-spec 完稿 → 20-spec-audit → HG-SPEC-SIGNOFF 人签 → 10-task → 20-task-audit → 三闸人签 → 30/40 → PR + CI 四绿 → merge → CLOSE 归档。验收必须含 **A1 第四段补全实录**：decide(approved) → resume → 终态 `done{completed}` 全真可达（D2 留的 40 缺口正是这段）。

**关键约束**：
- 消费回路设计须守「无状态恢复纪律」（恢复从事件表重建 · 不引入进程内存挂起态 · 见 `docs/guides/DESIGN_agent_contribution_endgame_v0_zh.md` §4）
- `decide` 的「批准即自动 resume」与「批准后手动 resume」之争：终局路线文档 §4 已有决议——做成**可配置**（全局默认 + 可按审批单覆盖），SPEC 里按此裁定，不要单边改死
- 既有链零回归：D2 的 A1–A8 验收与 `tests/test_capability_testing_write.py` 全绿须保持

## 第二棒：拿最新 SPEC 大纲（消费回路 CLOSE 之后）

```bash
git checkout master && git pull --ff-only
```

必读两份（已在 master / origin）：

1. **`docs/guides/DESIGN_agent_contribution_endgame_v0_zh.md`**（终局路线 v0 · PR #211）：P0–P3 路线 · 设计纪律五组（图谱版本钉死置顶）· 架构决议六项 · 16 点查漏补缺速查——**后续所有 SPEC 的共同上游**
2. **A 面 SPEC 草稿**：`docs/spec/tool-catalog-page/SPEC-tool-catalog-page_v0.md`（分支 `task/tool-catalog-page` · commit `ff3348d` · 已 push origin · 状态 draft 待 20-spec-audit）

## 第三棒：下一阶段研发（按优先级）

| 序 | 工作面 | 状态 | 动作 |
|---|---|---|---|
| 1 | **A 面 tool-catalog-page**（工具列表页） | SPEC 草稿就绪 | 派 20-spec-audit → 人签 → 拆 task（后端 B1/B2 + 前端 F1 专项）→ 全链到 CLOSE |
| 2 | **B 面**（对话过程全量展示 + SSE 导出 + mermaid 拓扑） | SPEC 未起草 | 起草时并入终局文档 §5 的两个裁定点：#15 全量渲染配折叠/展开层级 · #16 mermaid 直接做「拓扑+当次 run 节点高亮」中间档 |
| 3 | **SPEC-C**（tech_graph 读码给 issue 下结论） | **挂起** · 等维护者信号 | 图谱真址 `/Users/cyning/Desktop/Projects/kimi-code-meta/docs`（预计 2026-10-10 完工）；开工闸级裁定点 = 终局文档 §3.1/3.2/3.3（图谱版本钉死 · 沙盒安全 · 评测集先行） |

## 纪律钉

- 每面同一链：20 审 → 人签闸 → 30/40 → PR 四绿 → merge → CLOSE（归档 done/ + Hub 补登 + CLOSE invoke）
- 过程文档签录链由你 00 代录（维护者已授权）；人签闸（HG-SPEC-SIGNOFF / HG-AUDIT-R1 / HG-GRAPH-MODULES）仍须维护者签 task/SPEC 表，你代录留痕
- 禁 master 直改 · 各工作面各自分支 · graph-change 随交付签录
- 遇到与终局路线文档冲突的新事实：STOP 上抛维护者，不静默改向

## 首动作

1. 续完你窗在起草的「审批消费回路」SPEC → 走第一棒链路
2. 消费回路 CLOSE 后回本文档第二棒
