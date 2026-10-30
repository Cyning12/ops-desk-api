# fix-no-proxy-bracket-ipv6-sanitize 审查（R1 · 20-task-audit 存量回填）

> **审查对象**：`docs/tasks/done/task_fix_no_proxy_bracket_ipv6_sanitize.md`（v1.0 · 已归档 done/）
> **审查帽**：20-task-audit（R1 · 存量回填补审 · 依 `docs/tasks/active/task_api_legacy_reviews_backfill.md` v0.4 缺口②）
> **日期**：2026-10-30
> **补审背景**：本 task 交付期仓级 reviews 机读扫描（spec-wave verify review-gates）尚未启用，R1 审查文当时未落盘，仓级扫描判缺口「missing R<n>」；按本轮回填 task 纪律补审落盘，不走豁免。
> **核对材料**：done task 原文 · 收尾文档 `docs/tasks/close/close_fix_no_proxy_bracket_ipv6_sanitize_20261028.md` · 交付 commit 链（PR #295 · squash 1d26aa7 · `git merge-base --is-ancestor 1d26aa7 master` 实证在 master）· 现行代码抽查（本帽 2026-10-30 亲验）
> **纪律声明**：事后补审不改 task 与交付实质内容；范围/验收/failure_paths 逐条对照交付实证核对，结论据实。

## 一、范围与非范围核对

| task 声明 | 交付实证 | 裁定 |
|---|---|---|
| `app/main.py` 启动期清洗函数 `_sanitize_no_proxy_env()`（双键 NO_PROXY/no_proxy · 去方括号 · 仅在变化时写回） | 现行 `app/main.py:43` 定义 `def _sanitize_no_proxy_env`（函数体 :43-68 · 亲验） | ✅ 一致 |
| 调用点在 `_init_logging()` 之后、任何 app 包 import 之前 | 现行 `app/main.py:73` 调用（亲验） | ✅ 一致 |
| 8 条单测（monkeypatch env · httpx client 构造回归钉） | `tests/test_no_proxy_sanitize.py` 现存于仓（亲验） | ✅ 一致 |
| 非范围：不改 httpx · 不动其它 env 处理 | close 文档 diff 面仅 main.py + 测试档，零越界 | ✅ 一致 |

**根因与修复对因核对**：task 钉案根因——`NO_PROXY=[::1]` 方括号 IPv6 条目触发 httpx `InvalidURL ':1]'`（trust_env 构造期读取）；修复在 import 窗口期前清洗写回，机制对因，且对无方括号 env 保持逐字节零 diff（幂等无害口径）。

## 二、验收标准与交付一致性

| 验收 | 实证 | 裁定 |
|---|---|---|
| 1. 单测：`NO_PROXY=localhost,127.0.0.1,::1,[::1]` → 清洗后 `[::1]` 变 `::1`、其余条目与顺序不变；httpx client bypass 判定不抛 InvalidURL | 测试档现存；close 文档录 CI 4/4 绿 | ✅ |
| 2. 无方括号 env → 清洗后逐字节不变（零 diff 口径） | 测试档现存 | ✅ |
| 3. `NO_PROXY`/`no_proxy` 大小写两键同处理；键缺失 no-op | 测试档现存覆盖 | ✅ |
| 4. 钉版 ruff 0.15.21 绿 + pytest 不引入新红（28 红基线口径） | close 文档录实证输出 | ✅ |
| 40 live 补验：脏 env 重启 + run 1039c1a9 无 InvalidURL | close 文档录 live 补验 PASS | ✅ |

## 三、failure_paths 核对

- **清洗插入点必须在 `_init_logging()` 之后、先于任何 app 包 import**（import 链窗口期即可能构造 client）→ 现行 :73 调用点符合 ✓
- **httpx client 构造时读 env（trust_env）** → import 期清洗覆盖其后全部构造：机制前提成立 ✓
- **uvicorn --reload 子进程继承 supervisor env** → import 期清洗天然覆盖每次 reload：落实 ✓
- **未来 httpx 上游修复该解析** → 本清洗幂等 + 零 diff 保持无害：设计口径落实 ✓

## 四、结论/签收

本帽裁定：本 task 审查 **PASS**。验收 4 条与交付逐条一致（另 40 live 补验通过），范围与非范围零漂移，failure_paths 四条全部落实；交付 commit 1d26aa7（PR #295）已在 master 实证且 CI 全绿，现行代码抽查（main.py:43 定义 / :73 调用点 + 测试档存续）与 task 声明一致。核对全程未发现历史交付的实质问题，零内容阻塞项遗留。HG-AUDIT-R1 当时维护者签收（task 人工闸表 m00416 转录）与本审查结论相容；本件为存量回填审查，既有闸态照登不重签。

## 修订

| 日期 | 说明 |
|------|------|
| 2026-10-30 | 20 R1 存量回填补审落盘（task_api_legacy_reviews_backfill v0.4 缺口②）：done task + close 文档 + PR #295 交付链 + 现行代码抽查逐条核对，裁定 PASS，零实质问题 |
