# invoke · delegation-naming-boundary · CLOSE（2026-10-20）

## 五棒闭环
1. SPEC v0.1 signed（HG-SPEC-SIGNOFF=approved · 维护者 m00092/m00100）
2. 10-task 草稿 v0.1 → 20-task-audit R1=conditional_pass（M1 TC1×TC8 两牙互斥 / M2 闸登记历史行豁免 / M3 env 台账事实错误）→ v0.2 全闭合 → R2=pass
3. HG-AUDIT-R1=approved（00 代签 · 维护者 m00147 扩展授权 · d337486）
4. 30 实施（cd9b217 → e2a1c6f → 50c9e68 · TC1–TC10 全 ✔ · park 1762/0 · .env 对拍 IDENTICAL）
5. 40=approve 阻塞 0（红测 23f/32p 逐字复验 · 三态独立复验）

## 裁定链（00）
1. 冲突 A：FP-2 旧行为钉 test_tc2 增补一行 setenv 忠实翻译（白名单扩充带限定语 · 与 #2 redline 方案甲同性质）
2. 冲突 B：#3 闸前置硬 fail 收窄至 _BANNED_PREFIXES（跨波次碰撞修正 · 先例 9dd5c79/c61a2d5）
3. 40 非阻塞 O1/O2 现棒处置（01_modules.md:35 双分号顺手修 · 审查文白名单入库裁定甲先例）
4. CLOSE done/ 移动面预登记（50c9e68 · #3 O1 先例 · 保态①严格 pass）

## 行为变化宣告（FP-2 唯一有意变化）
write 重放护栏默认开：delegation off 时孪生写重放亦被拦（此前不拦）。
应急口：LG_RAG_WRITE_REPLAY_GUARD_ENABLED=false 恢复旧行为。

## 遗留挂账（invoke §九移交）
1. GATE_VERIFY 机读误报第 4 次（闸表 approved + commit 实证仍报 pending）——spec-wave 机读闸另案
2. .env 在场 37 项既有噪声族（与基线 IDENTICAL · 非本波次引入）——治理另案
3. 共享 cap_env 夹具注册表泄漏面——根治另案
4. _WAVE_TIP=None 占位 → 合并后 00 钉锚 mini PR（#287 先例）
