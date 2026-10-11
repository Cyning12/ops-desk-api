# invoke：30-实现 verify-upstream-dual-address（2026-10-11）

> **hat**：30-implementation · **task_slug**：`verify_upstream_dual_address`  
> **worktree**：`../ops-desk-api-worktrees/t-verify-upstream-dual-address` · **分支**：`task/verify-upstream-dual-address`（base master `286d825`）  
> **性质**：上游 issue/PR 根治交付 + 本仓 task 档回填（R2–R5 裁定 · R1 NIT×3 · 实现备忘）· 本仓零 `app/` 改动 · 钉版三处不动（待上游发版）

## 1. GATE_VERIFY（首输出 · 重定向取真码）

```bash
npx spec-wave verify --target . --task docs/tasks/active/task_verify-upstream-dual-address.md > /tmp/verify30_verify_upstream_dual_address.log 2>&1; echo $?
```

→ **EXIT=0 · VERIFY: PASS**。闸扫描：HG-TASK-DRAFT / HG-AUDIT-R1 / HG-GRAPH-MODULES 三闸 approved（00 代录 · 授权 m00106 · 机读复核一致）· HG-PILOT-OPSDESK-GLAYER n/a。

## 2. 真读清单

| 对象 | 结果 |
|------|------|
| task 文件 + FRAGMENT_30_gate_verify_v1_zh.md | 范围/非范围/失败路径/思考轮种子确认 |
| CONVENTION_review_gate_dual_address_v1_zh.md | 双址分工裁定 + 误报两起实证 + 存量零挪零改契约 |
| 交接档 PROMPT_00 §2.2-3 / §4-3 / §4-4 | 立项依据 + 口径墙坑 + 钉版前科（3.2.0 implementedBy） |
| 上游源码 `src/checks/review-gates.ts` @ fad4694（本机 `~/Desktop/Projects/dsh-coding-kit`） | :92-114 findLatestReview · :96 双址写死 · :99 命名 RE · :116-119 findReview 同源 · :46 spec 面同构 —— 与 task 锚点逐行核真一致 |
| `src/cli-shared.ts:334` normalizeSlug | `replace(/_/g, '-')` —— 址B dash slug ↔ task underscore slug 归一既有工具 |
| 址B 实档 9/9 | `docs/audits/task-review/YYYYMMDD_<slug>_r<n>.md`（dash slug · 小写 _r<n> · 日期前缀） |
| 本仓钉版三处 | scripts/graph-compile.sh:28 · package.json:6 · .github/workflows/lint-wiki-delta.yml:35（均已钉 3.0.1 · 核验一致） |
| 镜像旁证 | `node_modules/spec-wave/lib/checks/review-gates.js:89-111`（编译行较源码偏移 -3~-6 · :92→:89 · :96→:90 实证） |
| 上游仓状态 | 当前 checkout 分支 `task/specwave-3-3-graph-ast`（82abf30 · 他棒未提交脏态）→ 30 用独立 worktree `~/Desktop/Projects/dsh-coding-kit-wt-review-dual-address`（base origin/main fad4694 · 与 task 锚点 HEAD 一致）零触碰当前 checkout |
| gh 权限 | Cyning12 已认证 · repo scope · origin=git@github.com:Cyning12/SpecWave.git |

## 3. R2 裁定（方案对比）

**裁定【甲】**：加第三址 `docs/audits/task-review/` + 第二命名 RE `^\d{8}_(.+?)_r(\d+)\.md$`。
- 乙（可配置扫描面）否：通解面大超最小根治诉求 · 配置面=新维护债。
- 丙（统一命名迁址B 档）否：违 CONVENTION「存量零挪零改」钉死契约。
- 同名冲突取舍：既有「最高 R 轮取最新 · 同轮按文件名序」语义跨址扫描天然合并（同一循环比较即成立）；命名口径按址绑定不串址（址A 目录不认址B 命名 · 址B 目录不认址A 命名），封堵口径漂移。

## 4. RED → GREEN 证据（上游仓 · 分支 feat/review-gates-dual-address · commit d087a4d）

**RED（测试先行 · 实现前）**——`test/cli-verify-review.test.ts` 新增 4 用例，3 红 1 绿：

```text
✖ 址B 单落（不落址A）→ VERIFY: PASS · exit 0 —— verify 误报 missing R<n> review BLOCKED（误报面复现）
✖ findLatestReview 跨址合并取最高 R 轮：址A R1 + 址B r2 → round=2 —— actual: null
✖ findLatestReview 址B slug 去 _v<n> 版本后缀生效 —— actual: null
✔ 址B 落址A 式命名不认 → 仍 BLOCKED（反向钉死 · 实现前后须恒绿）
ℹ 既有 8 用例全绿（基线无污染）
```

**GREEN（实现后）**：

```text
test/cli-verify-review.test.ts: ℹ tests 12 · pass 12 · fail 0
npm run typecheck: 干净（tsc --noEmit）
npm test 全量: ℹ tests 989 · pass 988 · fail 0 · skipped 1
```

实现要点（`src/checks/review-gates.ts` findLatestReview）：
- dirs 扩三址 + 命名口径按址绑定（址A: `task_<slug>_audit_R<n>_*.md` · 址B: `YYYYMMDD_<slug>_r<n>.md`）
- 址B slug 匹配：normalizeSlug 归一 + 去 `task_` 前缀 + stripVer(`_v<n>`) 剥离
- 址B 目录不存在 existsSync continue 零噪音；`findReview` 布尔投影同源同治（status/dry-run/verify 零调用点改动）
- spec 扫描面（:46 findSpecReview）裁定**不扩**：址B 目录语义为 task-review · spec 审查无址B 落档实证 · follow-up 登记 issue #35

## 5. 上游交付物

| 项 | 值 |
|----|----|
| issue | https://github.com/Cyning12/SpecWave/issues/35 |
| PR | https://github.com/Cyning12/SpecWave/pull/36（base main · feat/review-gates-dual-address @ d087a4d · 仅 src+test 两档 · harness/task/invoke 档未进 PR） |
| commit 前缀 | `feat(review-gates):`（循上游 feat(scope) 惯例） |
| 发版版本号 | 待上游维护者评审/发版（非本 task 范围） |

## 6. 本仓改动面

仅 `docs/tasks/active/task_verify-upstream-dual-address.md` 一档回填：
- R2–R5 思考轮回填 + 控制表更新
- R1 NIT×3 回填：① :55 镜像路径改 `node_modules/spec-wave/` 正确写法 + 编译行偏移 -3~-6 注 ② 验收 lint-wiki-delta 命令钉 `spec-wave@3.0.1`（与 CI :35 一致）③ 镜像行弱化为旁证照录（真值以上游源码锚点为准）
- 实现备忘 / 自检结论 / 修订记录回填

**钉版三处不动**（上游 PR 未合未发版 · 失败路径第 4 行钉死：未 bump 即解除双落纪律 = 误报面复现）。存量档零挪零改核验：址A reviews 档与址B 既有档 git diff 零（本仓 diff 仅 task 档 + 本 invoke）。

## 7. 验收执行

- `npx spec-wave verify --target . --task <task>` → EXIT=0 PASS（§1 在案）
- `pytest tests -q` 零新增红对拍：见 30 汇报（master 基线 4-7 红为环境性钉案 · 勿当回归修）
- `npx --yes spec-wave@3.0.1 task lint-wiki-delta --target .` → 见 30 汇报（wiki_delta=n/a 恒绿口径）

## 8. 偏离与遗留

- **偏离**：上游仓作业用独立 git worktree 替代「checkout 内另起分支」——上游仓当前 checkout 有他棒未提交脏态（task/specwave-3-3-graph-ast），worktree 更严格满足「勿动其当前 checkout 分支」纪律（intent 一致 · 隔离更强）。上游 worktree 需 `npm install`（22 包）方得跑测试——上游仓自身依赖 · 非本仓新依赖。
- **遗留**：上游 PR #36 评审/合入/发版（上游维护者决策）→ 发版后循 task 验收节收口：钉版三处 bump（单独 commit）→ 址B 单落红绿对照实证 → CONVENTION 修订解除双址复制强制 → AGENTS.md/CLAUDE.md 核双址表述。task 保持 active 不提前 CLOSE。
