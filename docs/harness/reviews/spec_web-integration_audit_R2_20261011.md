# SPEC 书面审查：web-integration · R2（20-spec-audit · 增量复核）

## 元信息

| 字段 | 值 |
|---|---|
| **帽** | 20-spec-audit（SPEC 书面审 · 不实现代码 · 不改 SPEC 实质内容 · 不签 HG-SPEC-SIGNOFF） |
| **日期** | 2026-10-11 |
| **对象 SPEC** | `docs/spec/web-integration/SPEC-web-integration_v0.md`（v0.1 · draft-v0.1 · commit a4d4d02 · 分支 task/web-integration-spec · HG-SPEC-SIGNOFF 维持 pending） |
| **立项令** | 维护者令（m02397）：「为 web 项目生成联调需求 spec，让前端项目把已经存在功能联调完成」 |
| **轮次** | R2（增量复核 · 前一轮 R1 BLOCKED 见 spec_web-integration_audit_R1_20261011.md） |
| **复核窗口** | `git diff 9fdab48..a4d4d02` —— 仅 SPEC 本体一档，15+/14-，零越界改动 |
| **复核方法** | diff 窗逐条对拍 R1 BLOCKER/NIT 消化声明；修订引入的**新增声明**逐一亲读实证（主仓 master cae745e · A 面 SPEC worktree t-tool-catalog-page 42803fc）；修订后全文悬空引用扫描 |

---

## 一、R1 裁定消化 · 逐条复核

### BLOCKER B1（hitl.waiting 缺口失真）—— ✅ 消化，无残留失真

| 修订点 | 结果 | 实证 |
|---|---|---|
| §1.1 缺口②改写（:34） | ✅ | 「帧驱动审批卡 web **已交付**（chat.ts:709 `case 'hitl.waiting'` · :396 钉案 · pending 无轮询 :435）——真残留仅 useLgRagSse.ts:28 帧型 doc comment 6 型未收（`event_type: string` 运行时全透传 · 清单/文档级补全）」——四处锚点与 R1 亲读记录逐字吻合 |
| §4 F2 联调需求列同步 | ✅ | 改「帧型 doc comment 清单补全（缺口② · 纯文档级 · 运行时已全透传）」· 不再含已交付工作 |
| §9 T-W2 内容列同步 | ✅ | 改「帧型 doc comment 清单补全（7 型 · 文档级）」——6+hitl.waiting=7 与后端 sse_stream.py 实证 7 帧型一致；「审批卡帧驱动提示」已移除 |
| §6 D3 重写 | ✅ | 原「帧驱动 vs 轮询 pending」二选框架（前提失真）废弃；重写为「HITL 多端一致性」——多标签页/多设备他端 decide 后本端同步策略（A 不管 · B 手动刷新钮 · C 轻轮询 · 倾向 A）。系真开放项（单维护者现状下合理挂起待裁定），与代码无矛盾 |
| §7 原 Q4 废弃 | ✅ | :160 废弃注记在案（「帧驱动已交付无裁定必要，清单补全作 NIT 级直入 T-W2」）——与 B1 实证一致 |

### NIT N1-N6 —— ✅ 全部消化

| NIT | 修订 | 结果 | 实证 |
|---|---|---|---|
| N1 sync 锚点 | §2.6 改 `POST /admin/sync`（单端点）· admin/sync.py:**28** | ✅ | :28 `@router.post("")` 端点行 · 单端点表述与代码一致（R1 已亲读） |
| N2 manifest_errors 错挂 | §2.5 注记移挂 **catalog** 行（B2 分支 capability.py:217-218）；runtime 行改「meta 两键（B2 契约钉零 diff）」 | ✅ | catalog 挂点与 B2 分支实证一致；runtime 行新表述亲读通过（见下「新增声明复核」） |
| N3 done{resumed} 引用 | §2.2 锚点改 resume.py:131 · event_store.py:99-107；引文改 close_hitl_replan_carry_and_persist_guard_20261010.md:36 钉案①+验收档 20261010:106 | ✅ | 三处锚点均系 R1 亲读实证行（resume.py:131 硬编码 resumed · event_store coalesce 缺省 · close/acceptance 真钉案档） |
| N4 测试计数 | §8 FP-5/§9 T-W2 改「Vitest 全量 **225** 条 · chat-store.spec.ts **65** 条 it 全绿为闸」 | ✅ | 与 R1 实测计数逐字吻合（原「chat-store 28 枚」失真已消） |
| N5 Q1/Q6 重复 | §7 合并为单一 Q1 · 倾向 ops-desk-web `docs/spec/web-integration/`（四枚 SPEC 先例 · 实现主体在 web 仓）· api 仓不留或仅留指针 | ✅ | 矛盾解除（原 Q1 暂落 api 仓 vs 原 Q6 倾向 web 仓）；「web 仓四枚 SPEC 先例」R1 已核属实 |
| N6 A 面状态行观察项 | changelog v0.1 行照登「N6 转 A 面链」 | ✅ | 观察项本不要求本 SPEC 改动；照登转链处理正确 |

### 结构性复核

| 项 | 结果 | 实证 |
|---|---|---|
| Q 块重编号（Q1-Q4 · 原 Q5→Q4） | ✅ | 全文扫描无悬空引用——T-W2 旧「Q4 裁定后」依赖已移除；残留 Q4/Q5/Q6 字样仅存在于重编号注记与 changelog 历史行（v0 行系历史记录，非现状声明） |
| 状态行/闸纪律 | ✅ | draft-v0.**1** · 「HG-SPEC-SIGNOFF 维持 pending」明钉——未借修订擅自翻 signed |
| changelog v0.1 行 | ✅ | 逐项与实际 diff 对应，无虚报消化项 |
| 越界检查 | ✅ | diff stat 仅 SPEC 本体一档（15+/14-）· 零其它档改动 · 未引入未经亲读的新锚点（新增锚点 resume.py:131/close 档:36/验收档:106/B2 分支 capability.py:217-218 均系 R1 已实证行号） |

## 二、修订引入的新增声明 · 亲读复核

| 新声明 | 结果 | 实证 |
|---|---|---|
| §2.5 runtime 行「meta 两键（B2 契约钉零 diff）」 | ✅ 实质成立（观察项 O1） | 亲读 app/ops/capability/manifest.py:145-147：`get_capability_manifest_metadata()` 返回 `dict(_LAST_META)` =「最近一次成功 load/reload 的 **version + count**」恰两键，经 admin/capability.py:99 挂入 runtime 响应 `manifest` 键；B2 分支改动面在 capability.py:217-218（catalog summary）不动 runtime——「B2 后 runtime meta 不变」实质成立。**措辞注记（O1 · 非阻塞）**：A 面 SPEC 明文「零 diff」钉在 catalog 既有键（SPEC-tool-catalog-page_v0.md:52/:113/:156），runtime meta 之不变系隐含推论而非明文钉案；惟声明内容真实，不要求再改 |
| §6 D3 重写引入「多标签页/多设备」新裁定面 | ✅ 合理 | 系范围表述修正后的真开放项（原 D3 假前提废弃后的如实挂起），无代码矛盾，倾向 A（不管）与单维护者现状自洽 |

## 三、阻塞清单

无。R1 唯一 BLOCKER B1 已消化，diff 窗内未见新失真、未见越界改动、未见闸纪律违反。

## 四、非阻塞清单

- O1（观察项 · 无需消化）：§2.5 runtime 行「B2 契约钉零 diff」之零 diff 明文钉在 A 面 catalog 既有键（A 面 SPEC :52），runtime meta 两键之不变系隐含推论；声明实质真实（manifest.py:145-147 version+count · B2 不动 runtime），仅供 00/维护者知悉措辞口径。

---

## 结论：R2 PASS

R1 所退 BLOCKER B1 与 NIT N1-N6 全部消化，修订零越界、零新失真。SPEC v0.1（commit a4d4d02）通过 20-spec-audit 书面审查，可进签收流程。HG-SPEC-SIGNOFF 签署权在维护者（或其授权代录 · 承 A 面 m01606 先例），本帽不签、维持闸行 pending 待签署动作。
