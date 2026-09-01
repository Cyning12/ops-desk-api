# Invoke：30（含 40）· host-comms-task-writer（C3）

| 字段 | 值 |
|---|---|
| hat_id | 30（含 40） |
| task_slug | `host-comms-task-writer` |
| task_paths | `docs/tasks/active/task_host_comms_task_writer.md` |
| related_review_or_none | `docs/harness/reviews/task_host_comms_task_writer_audit_R1_20260901.md` |
| git_branch | `task/host-comms-task-writer` |
| created_utc_or_local | 2026-09-01 |
| notes | 00 代签 HG-AUDIT-R1 后派发；**仅 C3 受控写盘纯服务**（plan_task_write + apply_task_write）；禁止 HTTP 路由 · 注册进 Gateway registry/manifest · 删/移动文件能力 · 写 done/ · 改 SPEC §7 白名单 · 真跑 npx · 签 human_gate · 切分支/push/开 PR |

---

## 人工闸扫描（GATE_VERIFY · 30 重填 · 读 task 表）

| human_gate_id | task表status | 用户/invoke声称 | 一致？ | blocks_30 | 30可开工？ |
|---|---|---|---|---|---|
| HG-TASK-DRAFT | approved | 00 代签 | Y | N | Y |
| HG-AUDIT-R1 | approved | 00 代签 + R1 文 pass | Y | Y | Y |
| HG-GRAPH-MODULES | approved | 不新增一级模块 · 00 代签 · 仅 capability 行备注 | Y | N | Y |

reviews：`task_host_comms_task_writer_audit_R1_20260901.md` 存在且内容 pass？ **是**（内容零阻塞 · 非阻塞 5 条 30 知情并逐项处置）

pre-30 invoke：00 + 10 已落盘？ **是**

机械：`npx dsh-coding-kit@1.10.0 verify --target . --task docs/tasks/active/task_host_comms_task_writer.md` → **VERIFY: PASS**（exit 0 · 开工前与收尾各跑一次均 PASS）

结论：**可进入读码/改码**（30 首输出已重扫本表）

---

## 可复制 Prompt 快照

hat_id：30（含 40 自检）
task_slug：host-comms-task-writer
本帽禁区：HTTP 路由；注册进 Gateway registry/manifest；删/移动文件能力；写 `docs/tasks/done/`；改 SPEC §7 白名单；真跑 `npx dsh-coding-kit`；签发 human_gate；切分支/push/开 PR。

首动作：GATE_VERIFY（FRAGMENT_30_gate_verify）→ 通过再改码。

00 定夺摘要：
- `app/ops/capability/task_writer.py` 纯服务（**非** Gateway Capability · 不进 registry/manifest · 无 HTTP 路由）
- `plan_task_write(slug, content, *, kind, repo_root)` + `apply_task_write(plan, confirmed=False)`；dry-run 返回 WritePlan + diff 预览不落盘；confirmed=True 才写
- allowlist 仅 `docs/tasks/active` · `docs/tasks/draft`（可创建）· `docs/harness/invokes/by-task/<slug>/`（realpath 前缀判定防 symlink/.. 逃逸）
- 禁代签机械挡（宁严：人工闸节内 approved 一律拒 → invalid_content）；结构自检；文件名 `task_<kebab>.md` / `invoke_*.md`；overwrite 默认拒；原子写
- WritePlan 防伪造（apply 复跑校验或校验摘要）

验证：verify · ruff 触及路径 · pytest（CI 等价口径 `DATABASE_URL=postgresql+asyncpg://127.0.0.1:1/invalid` · 旧测零破坏）· graph-compile · lint-wiki-delta。

完成后：回填本 invoke 交付摘要 + task「自检结论（执行者）」；**不 CLOSE（留给 00）**；commit 不 push。

## 签收栏

00 代签落盘 · 维护者 Prompt 授权 · 2026-09-01 · VERIFY PASS

---

## 交付摘要

| 项 | 结果 |
|---|---|
| GATE_VERIFY | PASS · 可开工（三闸 approved · verify exit 0 · 开工前与收尾各复跑一次均 PASS） |
| 实现 | 新模块 `app/ops/capability/task_writer.py`：`plan_task_write(slug, content, *, kind, repo_root=None, overwrite=False) -> WritePlan`（路径解析 + allowlist realpath 前缀判定 + 结构自检 + 禁代签挡 + exists 检查 + unified diff 预览 · 零落盘副作用）· `apply_task_write(plan, *, confirmed=False) -> WriteResult`（checksum 防伪造 + 复跑全部校验 + confirmed=True 原子落盘）；kind 三形态 `task_active/task_draft/invoke` 唯一推导目录与文件名；错误前缀族 `invalid_args/path_not_allowed/invalid_content/invalid_structure/exists/plan_tampered/io_failed`（harness_cli 同族风格） |
| R1 非阻塞 5 条 | 全部处置（① 禁代签宁严：人工闸节内 HG- 行含 approved 一律拒 · 大小写不敏感 · 无占位例外 ② 双保险：apply 复跑全部校验 + WritePlan sha256 校验摘要 · 篡改/手造 → plan_tampered ③ realpath：resolved 目标对字面拼接 allowlist 根 is_relative_to 判定 · symlink 替身逃逸识破 ④ kind/目录错配归并 path_not_allowed · slug/kind 非法 invalid_args ⑤ mkdir parents 仅 confirmed 落盘时且目录已过 allowlist 判定） |
| 测试 | 新 `tests/test_capability_task_writer.py` **48 用例**全 tmp_path 沙箱（零网络零 npx）：allowlist 3 命中 + 11 注入 slug 参数化拒 · symlink 逃逸 · dry-run 不落盘/零目录副作用 · confirmed 落盘内容一致 · draft/invokes mkdir parents · 禁代签 5 例（含 overwrite 注入 approved 侧路 · apply 复跑内容关）· 结构缺节 3+1 · 文件名/kind 错配 · overwrite exists/diff 差异/竞态复跑 · 原子写 mock os.replace 失败不留半截 + 同目录临时文件 rename 语义 · plan 伪造/篡改 3 例 · 不进 registry（AST + grep + 活注册表） |
| 自检 | verify exit 0（×2）· ruff 触及路径 exit 0（全量 exit 1 = 2 处**既有**问题 rag/tokenizer UP035 · test_rag_chunker I001 · 与 C2 同款 · 按 P-07 不顺手改）· pytest **CI 等价 exit 0**（591 passed · 39 skipped · 基线 543+48 · 旧测零破坏）· graph-compile exit 0（9 graphs · graph.json 仅 generated_at 刷新）· lint-wiki-delta PASS（exit 0）· task lint PASS（W4 合法） |
| 图谱 | `01_modules.md` capability 行备注（C3 task_writer 受控写盘纯服务 · 非 Gateway Capability · 不进 registry/manifest · 无 HTTP 路由）+ 人签记录行（00 代签）；未增 implementedBy → G-L2 indexes 无需同步；不新增一级模块 |
| 已知未测项 | `repo_root` 缺省解析（parents[3]）在部署/打包环境的路径有效性（无部署接线 · 测试全显式 tmp_path）；invoke 文件名为推导式 `invoke_<slug>.md`（真实命名含日期/帽由 C4/Host 接线层决定 · invoke_* glob 已断言）；无人工闸节内容的禁代签挡不生效（task 类由结构自检封死该侧路 · invoke 类不设人工闸节） |
| 禁区核对 | 无 HTTP 路由 · 未 import/call gateway/registry/manifest（AST 断言）· registry/defaults/manifest/builtin.yaml 零 task_writer 引用 · SPEC §7 零变更（SPEC 文件零 diff）· 无删/移动文件能力 · 不写 done/ · 未真跑 npx · 未签 human_gate · 未切分支/未 push/未开 PR |
| 收尾 | task 验收 13 条勾选 + 自检结论（执行者）表 + 修订记录 30+40 行 + 文末「不 CLOSE（留给 00）」；分笔 commit · 未 push |

关键路径：
- `app/ops/capability/task_writer.py`（新增）· `tests/test_capability_task_writer.py`（新增）
- `docs/_tech_graph/l1/01_modules.md`（capability 行备注 + 人签记录）· `docs/_tech_graph/shared/graph.json`（生成物时间戳）
- `docs/tasks/active/task_host_comms_task_writer.md`（验收勾选 · 自检结论（执行者）· 修订记录 · 不 CLOSE）
