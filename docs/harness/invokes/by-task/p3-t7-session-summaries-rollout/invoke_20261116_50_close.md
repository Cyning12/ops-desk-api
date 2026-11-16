# invoke_20261116_50_close · p3-t7-session-summaries-rollout

## feat PR
- #430 https://github.com/Cyning12/ops-desk-api/pull/430
- CI 四 job 全绿：check 12s · import-linter 12s · lint-wiki-delta 9s · pytest 2m46s
- squash merge sha：8569fa0e（P3-T7: ops_session_summaries 折叠摘要放量波（纯 env 零代码 · 对拍 9/9 过））

## 验收台账（task 验收 9 条逐条）
1. [x] 对拍数据表落 invoke_40：40 轮真源对拍三态（原文基线 25988 chars/13517 est_tokens → off 4530/2253 → on 12704/6582）· on vs 基线 **−51.1% chars / −51.3% est_tokens ≥50%** ✅
2. [x] 缓存命中实证：二跑 session_summary_cache_hits=16/17 · generated=0 · provider 零调用（重试 1 次为超时 chunk 再超时 · 不计新调用语义外事件）· 逐字节一致；run1 12/12 chunk_hash 重算全等
3. [x] 3 条 on 态摘要抽检（服务名/版本/错误码/时间戳/配置值实体全保留 · 三标记 [历史摘要 · v1 · 模型] 齐 · 无信息断裂）→ invoke_40 §抽检
4. [x] thread_id 缺失降级：on+thread_id=None → 与 off 逐字节一致 + warning「SESSION_SUMMARY_ENABLED on but thread_id missing; keep placeholders」（continuity.py:387 路径）
5. [x] RUNBOOK_session_summary_rollout_v1_zh.md 落盘（三步放量 + env 开法 + 回退 + 观测五面 + 故障排查五条）
6. [x] .env.example 两键注记 + GUIDE_env_inventory :38/:55 备注回填 + 修订表行
7. [x] 01_modules.md chat 行 P3-T7 放量备注 + HG-GRAPH-MODULES 签收行
8. [x] 目标测试 17/17 绿 + 全量 pytest 2436 passed/1 skipped 79s 零失败（环境性红未复现 · CI 终裁兜底）
9. [x] ruff check app tests 绿（零代码改动 · allowed_app_files=[]）

## 机读验证
- ruff check app tests：All checks passed!
- import-linter：Contracts kept, 0 broken（CI）
- graph-compile（图谱编译）：OK · HG-GRAPH-MODULES 签收行在册
- wave-gate / spec-wave verify：PASS（active 期）· 转 done 后 lint W3 占位消失（自检结论已回填）
- 全量 pytest：本地 2436 passed · CI 绿（四 job）

## 偏差（终态）
- **D1**：Langfuse OTLP 403（dev 密钥失效 · R-P3-6 前置债）→ span 三键由对拍脚本 monkeypatch 录制替代，键名以 summary.py:346-352 为准；不阻断验收，生产观测在密钥修复后自动恢复。
- **D2**：token 判据改 chars 主判据（仓内无 tiktoken）· 估算口径 CJK=1 其余/4 写入 invoke_40。
- **D3**：base 87fd1ddf 非 T6 合并后 SHA——T6 波文件面零冲突，纯 env 放量无代码交集；rebase 冲突（registry/01_modules 与 T6 close 同区）已双方保留消解，PR #430 MERGEABLE 后四绿。
- **环境坑**：shell 代理 NO_PROXY 含 `[::1]` 致 httpx InvalidURL（本地工具性）· 解法 env -u 代理变量 · 已登记 invoke_40。

## 结果
波 CLOSE：任务转 done · registry status=closed wave_tip=8569fa0e。
