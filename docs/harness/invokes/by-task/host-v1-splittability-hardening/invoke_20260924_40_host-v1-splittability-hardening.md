# Invoke · 40（核验 + PR）· host-v1-splittability-hardening（V1-E）

> **日期**：2026-09-24  
> **帽**：40（**00 委派子 Agent**）  
> **前置 30**：[V1-E 30 实现收口](88d8c578-e399-4cf7-a51c-6881fee6de43) · tip `5bed0ae` / feat `41fca32`  
> **图谱**：HG-GRAPH-MODULES 人签行已 **00 代录 approved**  
> **工作目录**：`/private/tmp/opsdesk-wt-master40` · 分支 `task/host-v1-splittability-hardening`

## 40 必做

1. `git pull` · 确认图谱人签为纯 `approved` · `npx spec-wave verify --task …` PASS  
2. **独立核验**（不采信 30）：  
   - `tests/test_splittability_hardening.py` 全绿  
   - `lint-imports` 12 kept / 0 broken  
   - ruff 净增 ≤0（对照 master）  
   - `graph-compile` 绿  
   - B1 相关抽核  
   - diff 白名单对拍 task  
3. **D1 dualproc 纪律（强制）**：`test_multi_replica_dualproc.py` 若仍 ERROR，须用 master+同 .env 实证为基线/fixture 漂移；**禁止**在 PR/验收中写成「双进程全绿」。对照 D5 FINDINGS #1（另开 `fix-multi-replica-dualproc-tenant-session` 建议保留）。GUIDE 补扫条目须在。  
4. push（若有 00 代录 commit）+ `gh pr create`（标题建议含 V1-E / splittability）  
5. 盯 CI；**不做 CLOSE**（留给 00）  
6. 回写本 invoke：摘要 · PR URL · CI · dualproc 结论口径

## 修订

| 日期 | 说明 |
|---|---|
| 2026-09-24 | 00 下发 40（图谱已代录 · dualproc 红须如实标注） |
