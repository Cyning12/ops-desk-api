# 20-spec-audit R1 书面审：SPEC-stage-w-write-expand v0

> **hat_id**：20-spec-audit（R1 · 书面审 · 不改 SPEC 实质 · **不代签** HG-SPEC-SIGNOFF）
> **审查对象**：`docs/spec/stage-w-write-expand/SPEC-stage-w-write-expand_v0.md`（分支 `spec/stage-w-write-expand` · commit `7c83186` · 182 行逐行 · v0 初稿 · HG-SPEC-SIGNOFF=pending）
> **审查日期**：2026-11-05 · **审查人**：Harness 20-spec-audit
> **结论**：**fail（退回 10-spec 修订 1 项）** · 六项核对 5 项全绿、第 5 项（验收与开放裁定自洽性）发现 **1 个内容阻塞 B1**（Q4 加载期断言与 `testing.write.echo` mock 特例的豁免口径未裁决，按字面实现将与 A2/A5 自相矛盾）· 非阻塞观察 4 项 · **HG-SPEC-SIGNOFF 建议维持 pending，待 B1 修订后维护者人签**
> **对照真值（全部实读）**：SPEC 全文（182 行 · `7c83186`）· issue #323（待办与关键约束）· 上游 task `docs/tasks/done/task_api_controlled_write_hitl.md`（HG-STAGE-W-DESIGN 闸表先例 :42）· workspace 租户契约 `docs/contracts/api-v1-tenant-readonly-context-draft.md`（F1–F6 · freeze）
> **实证锚点复核（本帽亲读 · 分支工作区 @7c83186）**：
> - `app/ops/capability/manifests/*.yaml` 全量 grep：**全仓唯一 `side_effect: write` = `testing.write.echo`**（testing.v1.yaml:28；builtin.v1.yaml / oa.readonly.v1.yaml 全 read）→ R0「唯一写能力=mock」实证 ✅；该 manifest `tenant_scoped: false` / `hitl.required: true` / 顶层 `idempotency_key` / tags `[testing, mock, write]` 逐字段在册 ✅
> - `app/ops/capability/registry.py:118-120`：deny 判序实证 `deny_high_risk`（:118）在 `deny_write`（:120）前，docstring :110「只豁免 deny_write 一层 · deny_high_risk 永不豁免」✅（注：20261009 R1 审查引 :126/:128，master 演进致行号漂移，语义不变）
> - `app/ops/capability/policy.py:95`：闸序注释「危险程度 → 副作用 → 危险形态 → 输入完整性」在册 ✅
> - `app/ops/lg_rag/multi/nodes.py`：`:314 _BLOCKED_BY_CAPABILITY_WRITE = "capability_write_hitl_required"` · `tool_exec_node` :1857 · 台账 :507/:524 `capability_write_approval_consumed` ✅
> - `app/ops/hitl/router.py:493`：`_execute_decided_resume` 唯一定义 ✅；`auto_resume.py:225-227` 同源惰性 import 复用（禁第二实现实证）✅
> - `app/ops/capability/gateway.py:1318`：span `approval_id`（「写路径 HITL 预留（本波可空）」逐行在册 · SPEC §8 锚点省略 `capability/` 路径段，行号内容正确）
> - `app/ops/capability/manifest.py:552`：顶层 idempotency_key「**当前对 local_fn 无运行期消费方**（加载期护栏/声明位）」自证；`:840 if is_write and not idempotency_key` V1 强制在册 ✅
> - `app/ops/lg_rag/multi/nodes.py:1217-1278`：write 孪生护栏 `write_done_keys` / `write_replay_guard_skip` / `replay_of` 在册（FP-4 实际运行期承载，见 N1）
> - `app/ops/capability/adapters/http_generic.py`：transport 可注入 · CI `FakeHttpTransport` 零 socket（S2 契约测 canned 可行 ✅）· 「写操作绝不自动重试」docstring（FP-6 语义支撑 ✅）
> - `app/ops/admin/service.py:49-50`：`process_sync_payload` 在册（S3 候选面实存 ✅）
> - 冻结契约：`lg-rag-sse-v1`（`docs/_tech_graph/l1/01_modules.md` :35 行备注）· web `hitl-browser-decide-v1`（`ops-desk-web/src/api/hitl.ts:19`）✅
> - `npx spec-wave verify --spec` 实跑：`VERIFY: BLOCKED · missing spec R<n> review`（traceId `verify-mw30p8y9-b771d308`）——闸只查审查文存在（正则 `spec_<slug>_audit_R<n>_*.md`），本文件命名按此口径；**审查文合入后该闸解除，但机器通过 ≠ 签收，HG-SPEC-SIGNOFF 仍待人签**
> - 闸链 TTL：`01_modules.md` hitl 行 W-fix-1 注记「超龄 approved → expired + 409 approval_expired」→ FP-5 读时判过期语义实证 ✅

## 一、六项核对表

| # | 核对重点 | 裁定 | 摘要 |
|---|---------|------|------|
| 1 | 范围/非范围完整性与聚焦 | ✅ PASS | D1–D4 聚焦「一条真实窄写能力接入既有闸链」，与一句话目标逐字对齐；非范围 8 条全数在册（不多扩 / 不碰 irreversible / 不自动改码合 PR / 不做 web / SSE 零改 / 闸链一行不动 / 不碰 OA·iOS·P / 不写生产数据），与范围无重叠无漏；D4 图谱回写限 G-L1 行备注、不新增一级模块，承图谱纪律 |
| 2 | 代码锚点真实性（红线地基） | ✅ PASS | 上列锚点 12 项全实证，唯一失分仅行号漂移（:112-140 实录 :112-133；gateway.py 路径省略段），语义全中——承仓例「行号录自审查实证 · 30 按实校正」（见 N3） |
| 3 | 三条红线一致性 | ✅ PASS | ① 闸链零新建：D1 显式复用 PR #303 `tool_exec_node` 审批闸、不改 `blocked_by` 语义 ✅；② 判序零 diff：设计纪律 2 + A5（`_match_filter` / `policy.py` 闸序段 git diff 为空）双处钉死，实读判序与 SPEC 描述一致 ✅；③ `deny_high_risk` 永不豁免：设计纪律 2 + D1「tags 含独立写 tag（不放行 testing tag 复用）」+ Q2 S1「写 tag 只豁免 deny_write 层」三层同口径 ✅；**未发现 SPEC 与红线冲突，红线链完整闭合** |
| 4 | 开放裁定结构合规（只审不签） | ✅ PASS | Q1 三案（S1 仓内落笔 / S2 issue 备注 / S3 sync 触发）收益代价成对、S3 边界风险自指「可能扭曲 sync 面职责」如实；Q2/Q3/Q4 技术裁定均有建议而不越权；Q1 建议序明示「最终由维护者在 HG-STAGE-W-EXPAND-DESIGN 签收裁定」；HG-STAGE-W-DESIGN 闸表先例（上游 task :42 · ①②③ 00 代录格式）对照，新闸类比成立 ✅ |
| 5 | 验收与开放裁定自洽性 | ⚠️ **B1** | A1–A8 逐条可机断（fixture 轨全链 / 负样本组 / 租户三处一致 / 审计串链 / 零 diff grep / freeze 零破 / pytest+ruff+graph-compile / task lint），test_strategy「不连真外网 · S2 canned 替身」与 http_generic 测试接缝实证吻合；**但 Q4 加载期断言按字面实现将与 A2/A5 自相矛盾**——见下节 B1 |
| 6 | 思考轮 R0–R5 闭合 + 签收态 | ✅ PASS | 控制表 R0–R5 全 done、early_stop=no；R0 实证（active 为空 ✅ 实扫仅 README · 唯一写能力=mock ✅ 全量 grep）；R3 FP-1~FP-7 逐条锚既有语义（FP-5 TTL / FP-2 F1–F6 / FP-6 S2 条件启用）全中；R5 交 20-spec-audit → HG-SPEC-SIGNOFF 链路与本审查位置一致；人工闸表 HG-SPEC-SIGNOFF=pending 与状态行、issue #323 三方一致 ✅ |

## 二、阻塞项（内容 · 退回 10-spec 修订）

### B1 · Q4 加载期断言与 `testing.write.echo` mock 特例的豁免口径未裁决

- **原文（SPEC §4 Q4）**：「新写能力一律 `tenant_scoped: true`（testing.write.echo 的 false 是 mock 特例，不复制）；30 加加载期断言『**写能力 tenant_scoped 必须为 true**』」。
- **冲突实证**：
  - `testing.v1.yaml:33` 实读 `tenant_scoped: false`，且 `side_effect: write`——按 Q4 断言的字面口径，该 manifest 在 `OPS_CAPABILITY_EXTRA_MANIFESTS` 显式加载时即触发 ManifestError，**加载失败**。
  - `testing.write.echo` 是既有 W 闸链（PR #303）与三 fix 全部回归测试的真实可审对象（如 `tests/test_write_approval_gate.py:367` 消费台账断言依赖该能力加载），其「mock 特例」身份在 SPEC §1/§4 中被反复承认，但**断言句本身没有写豁免谓词**。
  - 后果链：断言按字面实现 → testing.v1.yaml 不可加载 → A2 负样本组与 A5「PR #303/#307/#313/#319 既有测试原样绿」**直接自相矛盾**；30 若发现此矛盾只能走修订表回填，等于把本应在 SPEC 签收前裁决的豁免设计推迟到改码期。
- **回填建议（任选其一，建议前者）**：
  1. Q4 断言改为「除 mock 特例清单（`testing.write.echo` 及 `testing`/`mock` tag）外，写能力 `tenant_scoped` 必须为 true」，豁免谓词写死在 SPEC，task 照抄；
  2. 或豁免按 tag 谓词（`tags` 含 `testing` 的写能力不受本断言约束），并明示「特例清单不扩容」。
- **性质**：纯文档增量一句，不动范围/非范围/Q1 选型留签结构；修订后维护者可凭本审查 + 修订 diff 轻量确认人签，**无需全量 R2 复审**（承 `task_supervisor_first_fail_closed_audit_R1_20261019` 先例口径）。

## 三、非阻塞观察（不阻塞签闸 · 供 task/30 按实校正）

| ID | 位置 | 内容 |
|---|---|---|
| N1 | §5 FP-4 / §6 A2 | 「幂等重放不双写」的机制归属须写实：顶层 `idempotency_key` 对 **local_fn write 无运行期消费方**（manifest.py:552 注释自证「加载期护栏/声明位」；运行期消费方仅 http_generic 的 http 块键）。S1（local_fn 落笔）场景下 FP-4 的实际承载是**编排层 write 孪生护栏**（`nodes.py:1217-1278` `write_done_keys`/`write_replay_guard_skip`/`replay_of`）+ 审批消费单发。建议 task 阶段把机制句写实，防 30 误去 capability 幂等面找实现而「发现缺口→误扩面」 |
| N2 | §1 设计纪律 5 / §2 D1 / Q2 S1 | 「三层『显式打开』」枚举只列两项（EXTRA_MANIFESTS 显式加载 + ALLOW_WRITE_TAGS 显式放行），基线层（默认加载面结构不含 / builtin 不引用）未点名；Q2 S1「默认零 diff」已实质覆盖。建议 task 枚举写全三层，纯措辞增量 |
| N3 | §8 代码锚点 | `registry.py:112-140` 实读 :112-133（deny_high_risk :118 → deny_write :120）；`gateway.py:1318` 全路径为 `app/ops/capability/gateway.py`。语义全中，行号 30 实扫校正（承仓例） |
| N4 | 流程 | `spec-wave verify --spec` 闸只机检审查文存在性（命名须命中 `spec_<slug>_audit_R<n>_*.md`），本文件已按此口径；机检通过不等于语义通过，HG-SPEC-SIGNOFF 语义面仍待人签 |

## 四、HG-SPEC-SIGNOFF 建议

**建议维持 pending，不代签**。理由：B1 为内容阻塞（Q4 豁免口径未裁决），须先由 10-spec 修订一句；修订为纯文档增量，完成后维护者可凭本审查 + 修订 diff 轻量确认并人签 HG-SPEC-SIGNOFF → approved（可同时裁定 Q1 三案或留 `HG-STAGE-W-EXPAND-DESIGN` task 闸，均属维护者权限，本帽不越权）。签前 00 拒拆 task。

## 五、回填清单（退回 10-spec）

| # | SPEC 小节 | 动作 |
|---|-----------|------|
| 1 | §4 Q4 | 加载期断言补豁免口径：按 `testing.write.echo` 显式清单或 `testing`/`mock` tag 谓词豁免 mock 特例，并明示「特例清单不扩容」（建议文本见 B1） |
| 2 | §5 FP-4（可选吸收 N1） | 「承载机制」句写实：编排层 write 孪生护栏 + 审批消费单发；local_fn 顶层幂等键仍只是声明位 |
| 3 | §1 设计纪律 5（可选吸收 N2） | 「三层显式打开」枚举补全基线层（默认加载面不含） |

## 六、下一棒

**退回 10-spec**（仅修订 Q4 豁免口径一句 · 可选吸收 N1/N2 · **禁改 Q1 留签结构与范围/非范围实质**）→ 维护者轻量确认 → 签 HG-SPEC-SIGNOFF（可同裁 Q1）→ 00 拆 task（新设 `HG-STAGE-W-EXPAND-DESIGN` 选型闸 · 类比 HG-STAGE-W-DESIGN 先例）。

```text
## 维护者签闸（10-spec 修订后 · 拆 task 前）

- [ ] 已读 R1 审查结论（fail · 仅 B1 一项 · 已修订）
- [ ] 核对修订 diff 仅涉 Q4 豁免口径（+ 可选 N1/N2 措辞）
- [ ] 裁定 Q1 选型三案（S1 仓内落笔 / S2 issue 备注 / S3 sync 触发 · 或留 HG-STAGE-W-EXPAND-DESIGN 闸）
- [ ] 在 SPEC 人工闸表将 HG-SPEC-SIGNOFF 改为 approved（维护者 · 日期 · 00 代录）
- [ ] commit SPEC 修订后下发 00 拆 task

00 Agent 将以 SPEC 闸表为准；pending 时必须拒拆 task。
```

---

## 修订记录

| 日期 | 摘要 |
|------|------|
| 2026-11-05 | R1：六项核对 5 绿；B1（Q4 加载期断言与 testing.write.echo mock 特例豁免口径未裁决 · 按字面实现与 A2/A5 自相矛盾）阻塞 → **fail · 退回 10-spec 修订**；非阻塞 N1–N4（FP-4 机制归属 / 三层枚举 / 锚点行号漂移 / verify 闸口径）；HG-SPEC-SIGNOFF 维持 pending（不代签）· Q1 选型三案未裁（留维护者） |
