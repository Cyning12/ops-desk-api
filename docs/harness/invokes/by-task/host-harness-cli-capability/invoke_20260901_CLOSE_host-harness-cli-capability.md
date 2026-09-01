# Invoke：CLOSE · host-harness-cli-capability

| 字段 | 值 |
|---|---|
| hat | CLOSE |
| task_slug | host-harness-cli-capability |
| date | 2026-09-01 |
| PR | [#114](https://github.com/Cyning12/ops-desk-api/pull/114) MERGED |

归档 → `docs/tasks/done/task_host_harness_cli_capability.md`

- 00 代签 · 维护者 Prompt 授权（`PROMPT_00_t4_close_through_c4_serial` · 串行波次 4）
- 生产：无 Alembic；Capability 默认 `policy_blocked`（SPEC 06 §7 · 须 Host 策略通道显式开启）· 业务零影响
- `harness.status` 未做（SPEC 可选）→ C4 开工时补
- 下一棒：C2 `host-comms-prompt-pack`（00 串行波次 5 · 依赖 H4 + kit ≥1.10 FRAGMENT + C1 ✓）
