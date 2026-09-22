# 融合权重调参日志（task memory-fusion-weight-tuning · 30 执行帽）

> 协议：每轮「定参数 → 改三常量 → 全量 live（--sweep）→ 本日志追加 → 清场核验」。
> 停止条件：达标=连续 2 轮 top3≥0.8 · 收敛=连续 3 轮 |Δtop3|≤0.05 且 |Δtop1|≤0.05 无上升趋势 · 上限=8 轮 · 异常=任一轮 errors>0 立即停。
> 环境：worktree ops-desk-api-wtune · tenant=memory-eval · 每轮跑前剥全部代理 env · PYTHONPATH 指向 wtune（已验证 import 落 wtune）。
> 样本量限制（继承 SPEC residual）：复述仅 12 例 + 时效场景 3 例 · sweep 场景分为小样本方向性证据，不冒充全量裁决分。

## Round 1（2026-09-21 22:21 起跑）

- **params**：HALF_LIFE_DAYS=90.0 · SIM_FLOOR=0.3 · SOURCE_WEIGHT_EXTRACTED=0.8
  （首轮 = 扫参推荐组合：基线报告 memory_golden_eval_20260921_post_tzfix.yaml sweep.recommended ·
  聚合方向：half_life 90d 复述 top3 均值 0.5926 最优 · sim_floor 0.3 最优 0.5926 · swe 0.8 时效 top1 折中）
- **diff**：service.py 仅 SIM_FLOOR 0.5→0.3、HALF_LIFE_DAYS 30.0→90.0（swe 本为 0.8 未动）
- **报告**：reports/tuning_round_1.yaml（run=memory-golden-eval-20260921-222154-live · 全量 50 用例）
- **指标**：paraphrase_top1=**null** · paraphrase_top3=**null**（12 复述用例全部 error，分母归零）
  · sweep 内 recency_top1（见报告 sweep 块；本轮因异常不作决策依据）
  · 抽取指标（逐轮记录 · 本轮不要求达标）：extraction_precision=0.2581 · noise_write_rate=0.2857
  · miss_rate=0.7143 · supersede_accuracy=0.4 · written_good=8 · written_noise=23
- **errors=12**：PR01–PR12 全部 TypeError: can't subtract offset-naive and offset-aware datetimes
- **清场核验**：跑后 SELECT count(*) FROM ops_memory_facts WHERE tenant_id='memory-eval' = **0**（核验脚本 exit 0）

### 异常查明（停止条件「异常」命中 · 立即停 · 循环不得带病继续）

- **定位**：_time_decay 内 now - fact.updated_at 混算——真库列由 migration 建
  timestamptz → 读回 aware；now_utc() 为 naive → 相减抛 TypeError。
  仅复述用例走 recall_with_vector → _fuse_recall → _time_decay，故 12 例全炸、其余 38 例正常。
- **根因**：本 worktree 分支 task/memory-fusion-weight-tuning（base 叠放
  task/memory-golden-eval）**不含 tz 修复**。修复在 dbc4bdd（task memory-fuse-tz-fix ·
  _as_utc 双侧归一），经 PR #147（eb8e718）合入 master；
  git merge-base --is-ancestor eb8e718 HEAD = **否**。基线报告「post_tzfix」是 tz 修复
  合并后跑的（当时跑位含修复）；本 worktree 代码面缺失 _as_utc。
- **与本轮参数改动无关**：只改了三个常量值，不可能引入 TypeError；fake 通路（内存库
  aware 时间戳）不受影响。
- **30 权限边界**：钉死契约「零越面：now_utc/…零 diff」+ 委派纪律「禁止切分支、禁止
  commit/push」→ 不得自行 cherry-pick/rebase 修复。上报 00 裁决：worktree 分支
  restack 到含 eb8e718 的 master 之上后重启循环（round 1 作废重跑）。
- **决策**：循环停止（异常条件）· 待分支修复后从 round 1 重启。

## Restack 注记（2026-09-21 · 00 裁决）

Round 1 异常根因 = 叠放 base（task/memory-golden-eval）缺 tz 修复。00 已将 origin/master
（含 PR #147 eb8e718 · _as_utc 双侧归一）merge 进本分支（merge commit 077f500），
git merge-base --is-ancestor eb8e718 HEAD = 是 · service.py 含 _as_utc 已复核。
阻塞解除 · 循环自 Round 2 重启（Round 1 为无效异常轮 · 不计入 8 轮上限）。

## Round 2（2026-09-21 22:32 起跑 · restack 后首个有效轮）

- **params**：HALF_LIFE_DAYS=90.0 · SIM_FLOOR=0.3 · SOURCE_WEIGHT_EXTRACTED=0.8（首轮扫参推荐 · 重跑）
- **diff**：service.py 仅 SIM_FLOOR 0.5→0.3、HALF_LIFE_DAYS 30.0→90.0
- **报告**：reports/tuning_round_2.yaml（run=memory-golden-eval-20260921-223221-live · 全量 50 用例）
- **指标**：paraphrase_top1=**0.9167**（11/12）· paraphrase_top3=**1.0**（12/12 · ≥0.8 MET）
  · sweep 内 recency_top1（当前参数组 90/0.3/0.8）= 1.0（sweep 为 fake 确定性 · 与基线一致）
  · 抽取指标（逐轮记录 · 不要求达标）：extraction_precision=0.2286 · noise_write_rate=0.2857
  · miss_rate=0.7143 · supersede_accuracy=0.4 · written_good=8 · written_noise=27
- **errors=0**（tz 修复生效 · 异常根因消除）
- **清场核验**：跑后 SELECT count(*) WHERE tenant_id='memory-eval' = **0**（exit 0 · 报告 cleanup revoked=53 tenant_rows_deleted=165）
- **决策**：top3=1.0 ≥ 0.8 首个达标轮。按「连续 2 轮」判据，Round 3 以**同参数**跑确认轮
  （防单次运气；确认轮=全量 50 用例 · 若再 ≥0.8 即达标停止并以此参数定稿）。

## Round 3（2026-09-21 22:38 起跑 · 确认轮 · 同参全量 50）

- **params**：HALF_LIFE_DAYS=90.0 · SIM_FLOOR=0.3 · SOURCE_WEIGHT_EXTRACTED=0.8（与 Round 2 相同 · 定稿候选）
- **diff**：无新增（常量沿用 Round 2 值）
- **报告**：reports/tuning_round_3.yaml（run=memory-golden-eval-20260921-223800-live · 完整 50 用例全量跑 · 非 sweep 场景分）
- **指标**：paraphrase_top1=**0.9167**（11/12）· paraphrase_top3=**1.0**（12/12 · ≥0.8 MET · 连续第 2 轮）
  · sweep 内 recency_top1（90/0.3/0.8 组）= 1.0
  · 抽取指标（逐轮记录 · 藏丑禁令如实写）：extraction_precision=0.2059（较 R2 0.2286 略降 · live LLM 抽取波动）
  · noise_write_rate=0.3571（较 R2 0.2857 升）· miss_rate=0.7143 · supersede_accuracy=0.3（较 R2 0.4 降）
  · written_good=7 · written_noise=27
  · 注：抽取侧指标属抽取校准 task 范畴（本 task 钉死契约 · 不要求达标但必须记录）
- **errors=0**
- **清场核验**：跑后 SELECT count(*) WHERE tenant_id='memory-eval' = **0**（exit 0 · 报告 cleanup revoked=53 tenant_rows_deleted=164）

## 停止裁决

- **命中条件：达标**（连续 2 轮全量 live paraphrase_top3 ≥ 0.8：R2=1.0 · R3=1.0 · 确认轮=完整 50 用例）
- **定稿参数（以第 2 轮参数）**：HALF_LIFE_DAYS=90.0 · SIM_FLOOR=0.3 · SOURCE_WEIGHT_EXTRACTED=0.8
- **有效轮数**：3（R1 异常作废不计上限 · R2/R3 有效）
- **样本量限制如实声明**：复述 12 例小样本（SPEC residual ①② 继承）· 单 goldenset 调参存在过拟合残余（正面解=金样扩样 · 另议）
- **未达标项如实记录**：extraction_precision / noise_write_rate / supersede_accuracy 三轮均 NOT-MET —— 属抽取校准 task 范围，本 task 不定罪不粉饰
