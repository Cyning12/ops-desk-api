# invoke · 00 · tenant-readonly-predicate · web 联调重试 PASS

| 项 | 内容 |
|----|------|
| **时间** | 2026-09-18 |
| **帽** | 00 |
| **分支** | `task/tenant-readonly-predicate` |
| **上游** | web 维护者/00 回报联调重试 PASS |

## 结果

| 项 | 状态 |
|----|------|
| B 下 `GET …/sessions/latest` | **PASS**（先前代理假 500 已消失） |
| A 一问 `lg-rag/stream` | **200** · 头与 UI 一致 |
| B 一问 `lg-rag/stream` | **200** · 头与 UI 一致 |

根因留痕见 `invoke_20260918_00_sessions_latest_b_triage.md`（Vite `ECONNREFUSED`→假 500，非 latest@B 业务缺陷）。

## 本仓状态

- 30 Fixture + 40 自检此前已 PASS
- 回归测 `test_sessions_latest_ok_after_switch_to_tenant_b` 已落
- **未 commit / 未 push / 未开 PR**（维护者令：等 web 一起合并）
- 本机 api `:8001` 仍可联调（勿 Docker `:8000`）

## 下一棒（待维护者令）

1. api + web **同波 commit → push → 开 PR → 一起合**  
2. 或先各自 commit、再协调合入顺序  
3. CLOSE / `git mv` task → done：**另令**  
4. 生产 B 种子：另轨

## 本窗

**未改实现码** · 已派 / 待派：无（HOLD 等合并令）
