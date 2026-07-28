# BACKFILL_DRAFT · harness 2.20.0 · 建议回填产品仓（来自 ops-desk-api）

> **性质**：草稿建议 · **禁止**在本业务仓改 cyning-harness 源码；由产品维护者挑选合入。  
> **来源 FEEDBACK**：`FEEDBACK_harness_2_20_0_from_ops_desk_api_20260728.md`

---

## A. RUNBOOK_upgrade_wiki_delta_v1_zh.md

1. **§1 后增「overlay 自检」**（P2）  
   - `diff`：`AGENTS.md` / `CLAUDE.md` / `.cursor/rules/05-harness-starter.mdc`  
   - 说明：marker merge 会丢掉仓内定制关键词与 pre-30 句。

2. **§5 增 Python/npx-only 交叉链**（P2）  
   - 一句指向 `ci/samples/README.md` 的 `package-manager-cache: false` 专节。  
   - 明确：无 `package.json` 的 FastAPI 仓同样必须关缓存（防未来加 packageManager 踩坑）。

3. **「已迁完仓」快速路径**（P3）  
   - `upgrade → check → lint-wiki-delta → lint --strict →（可选）挂 CI`  
   - 注明：若 missing=0 则跳过决策树补字段。

4. **§5 cp 路径**（P3）  
   - 给不依赖本机 monorepo checkout 的复制法（raw URL 或「从已 install 的包 `…/ci/samples/`」）。

## B. USER_GUIDE §6.0b / wiki export

5. **统一 `wiki export` 旗标**（P3）：`--root` vs `--target` 只保留一个对外名，或两者等价并写清。

## C. upgrade / local.json

6. **local.json**（P3）：文档建议加入 `.gitignore`；或 upgrade 对已存在文件不覆盖绝对路径。

## D. 调度 / Open Folder

7. Prompt 模板勿写死 `Desktop/Projects/…`；改为「定位业务仓 git root 后再 Open Folder」（P2 · 调度侧）。

---

## 非建议

- 不因本 dogfood 削弱 close 硬闸 / `--strict` 语义。  
- 不要求业务仓把 `--strict` 立刻设成 CI 必绿（本仓选择：默认 lint 硬失败，strict 注释保留）。
