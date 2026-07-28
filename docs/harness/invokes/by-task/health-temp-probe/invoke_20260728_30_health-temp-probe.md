# Invoke：30（含 40）· health-temp-probe

---

## 元信息表

| 字段 | 值 |
|------|-----|
| hat_id | 30（含 40 自检） |
| task_slug | `health-temp-probe` |
| task_paths | `docs/tasks/active/task_health_temp_probe.md` |
| related_review_or_none | `docs/harness/reviews/task_health_temp_probe_audit_R1_20260728.md` |
| git_branch | `fix/health-temp-probe` |
| created_utc_or_local | 2026-07-28 |
| notes | 维护者当面：临时 `/health` probe；验完回滚 |

---

## 可复制 Prompt 快照

```text
临时在 GET /health 增加 probe=20260728-a；更新 test_health；PR；部署冒烟后去掉。
```

---

## GATE_VERIFY 摘要

三闸 approved · R1 签收 · VERIFY PASS · 可开工

---

## 交付摘要

- **改动**：`app/main.py` `/health` → `{"status":"ok","probe":"20260728-a"}`
- **测试**：`pytest tests/test_health.py` → 1 passed
- **verify**：PASS
- **下一棒**：push + PR；维护者 `./deploy.sh --skip-web`；curl 对比 probe；开回滚 PR 删字段

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-07-28 | 临时 probe 落地 |
