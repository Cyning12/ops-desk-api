# Invoke：env 红基线治理 + N3 自注册 + fail-closed 立档（30 治理单棒）

> task：env-red-n3-governance · 分支 `agent/env-red-n3-governance` · 2026-11-07
> 授权：维护者当面指令「B 全做」（销 api#337 CLOSE invoke §遗留挂账 1–3）· 单棒闭环（实现即验收）

## GATE_VERIFY

- HG-TASK-DRAFT：approved（维护者 2026-11-07 09:15 当面指令 · 档内闸表代签）
- HG-GRAPH-MODULES：approved（graph_change_layer=none · 档内闸表代签）

## 挂账①：2 枚 env 红修复（红测先行双证据）

**修复前取证（09:17 · 2 failed）**：

- `test_embedder_failure_degrades_with_marker`：播种子 `write_fact()` 未传 embedder，
  内部走真 `get_query_embedder()` → 缺 `SILICONFLOW_API_KEY` 裸奔 RuntimeError。
  根因=测试隐式依赖真实外部环境（CI skip 面：无 key 环境根本走不到断言）。
- `test_hitl_cross_instance_resume`：resume 端点 2026-11-02 W-fix 起改异步受理
  （请求内只 preflight 秒回 accepted），测试仍断同步内联契约（state/answer 直出）→
  恒红「图没真推进」。叠加替身图漂移：`_DpState` 五键与 `resume._summarize` 提取表
  （react_round/route/subtasks…）零重叠，同步形态下 state 摘要也恒空。

**修复（零 src 改动 · 只动三枚测试文件）**：

1. embedder 用例：播种 `monkeypatch.setattr("app.ops.rag.embedder.get_query_embedder",
   lambda: FakeEmbedder())`——照同文件 ⑦ 变异检验的既有装配口径，不引新范式；
2. hitl 用例：①`tests/dualproc_server.py` 替身 aggregator 增 `hitl_unlocked_ids`
   （summarizer 可见键 · 语义=真 supervisor 解锁列表）②断言改双契约：同步内联老契约
   直断 / 异步 accepted 新契约断受理形态 + replay 轮询等恢复段 done 终帧（60s 上限，
   与后台执行体不再赛跑）。

**修复后（09:22 · 2 passed）**：红转绿双证据达成。

**第二迭代（全量首跑逮出 · 09:34 修复）**：全量套件首跑暴露轮询与恢复段写窗赛跑——replay 在恢复段在写窗时按服务端设计契约返 409 + Retry-After（router D1 · 「客户端退避重试·沉降后同请求零 diff」），初版轮询把 409 当失败直断。修=轮询循环内 409 退避 continue（不在此判失败）· 压测 5/5 过（3.4s/遍）· 整文件 9 passed。

## 挂账②：N3 波次审计闸自注册（registry.yaml + 通用闸 + 程序）

三件套：
- `docs/harness/audit_gates/registry.yaml`——种子 entry = diff-whitelist-anchor-drift
  （status=closed · base d337486 · tip c17e63b · allowed 三集合照抄 TC8 声明白名单含 F1 两件）；
- `tests/test_wave_gate_registry.py`——通用闸（banned 在途前置[含 closed] · active committed
  闭窗 ⊆ allowed · N2 tip 不可解析带审计跳过）+ 种子回归牙（allowed 集合与原 TC8 钉死一致）；
- `docs/harness/audit_gates/README.md`——自注册三步程序 + 闸语义表 + 与 bespoke 闸关系。

**三变异探针实证（全咬）**：
1. banned 在途探针（untracked `scripts/.n3_banned_probe`）→ FAIL「禁改面在途触碰」；
2. active committed 面探针（status 翻 active）→ 真跑 `git diff d337486 c17e63b` ⊆ allowed PASS
   （证明面审计真实执行非静默跳过；期间逮出本闸自身 `--name-only` 缺 `--` 笔误并已修）；
3. 缩白名单探针（删 review40 行）→ FAIL 列出越界件（回归牙实证）。

## 挂账③：fail-closed 正式立档

`docs/harness/audit_gates/adr-001-fail-closed-stranded-wave.md`：状态 accepted（维持不修正）·
三条理由（方向正确/真实 CI 零影响[40 棒浅克隆实证]/修正成本高企且正解在 N3 声明面）·
触发条件与 revisit 条件入档。

## 质量门（本棒）

| 项 | 结果 |
|----|------|
| 两枚 env 红修复后命令级 | 2 passed（修复前 2 failed 见上） |
| `tests/test_wave_gate_registry.py` | 2 passed（常态绿） |
| `ruff check`（本棒四面） | All checks passed（全仓 13 枚为 miniconda 新 ruff 版基线既有·与本棒无关） |
| `spec-wave task lint` | LINT: PASS（W4 合法豁免 warn） |
| `spec-wave task lint-wiki-delta --target .` | LINT-WIKI-DELTA: PASS（214 scanned · 0 issues） |
| 全量 pytest | 见下 |

## 全量摘要（回填）

2106 passed · 4 skipped · 0 failed（09:37 全量 · 34.7s）——原基线 2 枚 env 红消失 · 零新增红 · 基线全绿达成。迭代留痕：全量首跑（09:34）曾 1 failed（初版轮询未处理恢复段写窗 409 契约）→ 修轮询退避 + 压测 5/5 + 整文件 9 passed → 复跑全量如上。

