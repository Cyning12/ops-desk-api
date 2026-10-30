# invoke · 30 · execute · specwave-upgrade-3-5-0

| 项 | 内容 |
|----|------|
| **时间** | 2026-10-30 |
| **帽** | 30 |
| **task** | `docs/tasks/active/task_specwave_upgrade_3_5_0.md` |
| **授权** | 双闸 approved（00 代录 · 维护者长期授权锚 m00236「授权00签收后续文档」）· 维护者令 2026-10-30「更新specwave」· 全程本地严禁 push/PR |
| **retention** | minimal（升级类精简形态 · task meta invoke_retention_profile=minimal） |

## 闸扫描（GATE_VERIFY 真值 = task 表）

| gate | status | 依据 |
|------|--------|------|
| HG-TASK-DRAFT | approved | task 人工闸表（00 代录 · m00236） |
| HG-AUDIT-R1 | approved | task 人工闸表（00 代录 · m00236） |
| HG-GRAPH-MODULES | n/a | graph_change_layer=none |

`npx spec-wave verify --task <本 task>` 闸解析 approved 通过（missing R<n> review 按维护者授权 --allow-no-review 留痕豁免 · exempt 条目四字段照登 · 禁伪造审查）。

## 执行记录

1. `npx spec-wave@3.5.0 upgrade --target . --yes` → EXIT=0 · 仅改 .coding-kit/manifest.json（3.3.0→3.5.0 · from_version 3.3.0）
2. 钉位全量对齐：package.json / package-lock.json（npm install --package-lock-only）/ pnpm-lock.yaml（pnpm install --lockfile-only）/ scripts/graph-compile.sh:35（GRAPH_CLI 默认 spec-wave@3.5.0 + 2026-10-30 对齐记录 · 历史注释零改）/ .github/workflows/lint-wiki-delta.yml:39+:43（+ 对齐记录）
3. S7/S8 读码实证零改动：app/ops/capability/harness_cli.py _kit_pin() env 单源无硬编码默认；tests/test_capability_harness_cli.py 断言系 monkeypatch env 注入样例
4. 验证矩阵 V1–V8 全绿（详见 task 自检结论）：check EXIT=0 · task lint PASS · 现存 task verify 3.5.0≡3.3.0 逐字节一致（非回归照登）· graph-compile EXIT=0 首行 [spec-wave@3.5.0] 图谱零 diff · pytest 32 passed · grep 3.3.0 清零 · lint-wiki-delta PASS · --version 3.5.0
5. 3.5.0 graph_anchor 实证：INFO 一行 skipped=graph_path_unreachable（graph_modules_path=l1/01_modules 相对仓根不可达）· exit 不变不挡 · 与升级前读码预断一致
6. FEEDBACK 落盘 docs/spec/doc-health/feedback/2026-10-30_3.5.0_ops-desk-api_upgrade.md

## commit 链

da2a82b（task 落稿）→ 4db4371（双闸代录 + exempt 扩列）→ 6c9d0e6（钉位全量对齐）→ 73efeef（自检回填 + FEEDBACK）

## 结论

**S1–S9 / V1–V8 全绿 · 升级完成**；遗留（照登待维护者裁决另案）：①prompts sync（含新 FRAGMENT_graph_first_read_v1_zh）②legacy profile graph_modules_path 修正。
