# Invoke：30/40 · capability-policy-sandbox（H2）

| hat_id | 30/40 |
| task_slug | capability-policy-sandbox |

## 实现

- `app/ops/capability/policy.py`：`check_invoke` · `HOST_ONLY_POLICY_KEYS`
- `gateway._dispatch` 统一 Policy 门 · span `policy_blocked` / `risk_level`
- `tests/test_capability_policy.py`（8 cases）
- G-L1 `capability` 备注

## 40

pytest policy + capability_gateway · ruff 0 · graph-compile 绿

| 2026-08-27 | PASS |
