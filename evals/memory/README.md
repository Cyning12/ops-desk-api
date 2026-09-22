# evals/memory · 记忆金样评测（task memory-golden-eval · eval 轨）

> **零生产语义改动**：本目录只交证据（金样 + runner + 扫参 + 报告），不改
> `app/ops/memory/**` / `app/ops/lg_rag/**` / `app/db/**` 任何一字。
> 上游 SPEC：`docs/spec/memory-golden-eval/SPEC-memory-golden-eval_v1.md`（signed）。

## 文件

| 文件 | 说明 |
|---|---|
| `golden_v1.yaml` | 金样集 v1（50 条四类 · ops-desk 运维域） |
| `run_eval.py` | 双模式离线 runner（fake 默认 / live 真跑）+ 27 组扫参 |
| `README.md` | 本文件（schema + 标注指南 + 用法） |

## 金样 schema（golden_v1.yaml）

顶层：`version: 1` · `domain` · `golden: [case, ...]`。四类用例字段：

| 字段 | should_remember | should_not_remember | supersede | paraphrase |
|---|---|---|---|---|
| `id` | ✔ 全局唯一 | ✔ | ✔ | ✔ |
| `category` | ✔ | ✔ | ✔ | ✔ |
| `query` | ✔ 对话用户轮 | ✔ | ✔ | ✔ 复述问法 |
| `answer` | ✔ 对话助手轮 | ✔ | ✔ | — |
| `expect_facts` | ✔ ≥1 条 | ✔ 必须为 `[]` | ✔ 恰好 1 条（新值） | — |
| `setup_fact` | — | — | ✔ 旧值（同 key） | — |
| `fact` | — | — | — | ✔ 预写事实 |
| `expect_hit_key` | — | — | — | ✔ 须等于 `fact.key` |
| `fake_facts` | ✔ fake 罐头输出 | ✔（可为 `[]`） | ✔ | — |
| `note` | 建议 | 建议 | 建议 | 建议 |

- `expect_facts` / `setup_fact` / `fact` 的 `key` 必须过真闸
  （小写点分层 ≥2 段 · 非 `tmp.`/`session.`/`ephemeral.`/`draft.` 前缀；
  命名约定见 `app/ops/memory/README.md`）；`value` 为 JSON 标量非 null。
- `fake_facts` 是 **fake 模式下罐头抽取器的输出**（模拟 LLM 抽出的候选），
  与 `expect_facts`（**应该**写入什么）解耦：二者一致 = fake 全过；
  刻意不一致 = 构造 fail 用例（CI 三态测试即此手法）。live 模式忽略 `fake_facts`。

数量下限（schema 校验强制）：应记 ≥12 / 负样本 ≥12 / supersede ≥8 / 复述 ≥10。

## 标注指南

1. **应记（should_remember）**：对话中含**稳定、可复用、与本主体直接相关**的事实
   （负责的仓库 / 部署目标 / 时区 / 负责人 / 基础设施基线）。`expect_facts`
   一条一个原子事实。
2. **不应记（should_not_remember · 负样本）**：一次性信息 / 易失状态 / 通用知识 /
   他人事实 / 寒暄。判定 = **零写入**。两类形态都要覆盖：
   - 闸可拒：`fake_facts` 放易失前缀 / 非法 key / 空值 / 超长值 → 真闸拒写；
   - prompt 级：`fake_facts: []`（模拟理想 LLM 不产出）——真正考校在 live。
3. **冲突 supersede**：同一 key 先 A（`setup_fact`，runner 显式预写）后 B
   （对话声明变更，`expect_facts`=B）。判定 = 召回只见 B 且 A 表内 `superseded`。
4. **复述召回（paraphrase）**：`fact` 预写（带 9 个新鲜干扰项，确定性 top-N
   挤掉目标，只有向量通路能捞回），`query` 用**改写/换说法**。判定 = 向量通路
   top1 / top3 命中 `expect_hit_key`。
5. 新用例入仓前跑 `pytest tests/test_memory_golden_eval.py -q`（schema 校验会
   把数量/字段/key 问题一次报全）。

## 双模式用法

```bash
# fake（默认 · CI 确定性 · 不连外网不连 DB）
.venv/bin/python evals/memory/run_eval.py --backend fake \
  --golden evals/memory/golden_v1.yaml --out reports/memory_golden_eval_fake.yaml

# 附 27 组扫参（SPEC §2 D3 · 只出建议不改代码常量）
.venv/bin/python evals/memory/run_eval.py --backend fake --sweep \
  --out reports/memory_golden_eval_sweep.yaml
```

- **fake 确定性来源**：`FakeEmbedder`（关键词组 → 正交基向量，无随机）+
  罐头抽取（`fake_facts`）+ 内存事实库（id 计数器）；真实复用未改一字的生产件
  `gate.should_write` / `extract_json_object` + `MemoryFactExtraction` /
  `service._fuse_recall`。fake 全过只证明**管线与指标正确**，不构成开开关依据。
- **live 显式失败**：缺 `SILICONFLOW_API_KEY` / 外网不通 / DB 不通 →
  **退出码 2 + stderr 显式报错**，绝不静默降级冒充 fake（failure_paths 钉死）。
- **live 隔离与清场**：独立 `tenant=memory-eval`；跑后逐 run
  `revoke_by_source`（审计）+ 删除该租户全部残留行（含 superseded/显式干扰项，
  硬删仅限此专用租户）。live 进程内临时打开 `MEMORY_FACTS_VECTOR_RECALL_ENABLED`
  与 `MEMORY_FACTS_EXTRACT_ENABLED`（进程私有，不改 .env / 代码默认值）。

## 指标（SPEC §2 D2）

| 指标 | 定义 |
|---|---|
| `extraction_precision` | 命中 `expect_facts` 的写入 ÷ 全部抽取写入（SR/NG/SP） |
| `noise_write_rate` | 有写入的负样本用例 ÷ 负样本用例总数 |
| `miss_rate` | 未写全 `expect_facts` 的应记用例 ÷ 应记用例总数 |
| `paraphrase_top1/top3` | 复述用例 top1 / top3 命中率 |
| `supersede_accuracy` | 「召回仅新值 ∧ 旧值 superseded」用例占比 |

报告头部**写死** SPEC §2 D5 四条门槛与达成情况（`thresholds` 块 +
`all_thresholds_met` + `threshold_note`）：precision ≥0.9 · 噪声写入率 ≤0.1 ·
复述 top3 ≥0.8 · supersede =1.0。引用报告时必须连同头部一起读（防假绿）。

## 扫参（E3 · 只出建议）

网格 `half_life {7,30,90} × sim_floor {0.3,0.5,0.7} × source_weight_extract
{0.6,0.8,1.0}` = 27 组。场景 = 复述用例陈化 1/30/90 天三档 + 时效性
（旧相关显式 vs 新弱相关抽取）。实现：`patched_fusion_constants` 运行时临时
覆盖 `app.ops.memory.service` 模块常量调用**真** `_fuse_recall`（with 块内
恢复现场；零文件改动、零生产默认值改动）。报告含 `recommended`（组合 + 分数 +
理由）与逐维聚合理由；全部低于内部参考线（0.8）时 `recommended: null` 如实不推荐。
**改值另 task 按报告裁决。**

## 维护者复制区（真跑）

SPEC §8 已有权威复制区，此处仅指针：
`docs/spec/memory-golden-eval/SPEC-memory-golden-eval_v1.md` §8「复制区（给维护者 · 真跑）」。
真跑后对照报告头部 D5 门槛裁决开/不开开关（30 验收不含真跑结果）。
