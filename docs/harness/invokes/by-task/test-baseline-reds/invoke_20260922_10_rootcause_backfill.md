# invoke · 10-task · D3 backfill flaky 根因定位

> hat=10 · 2026-09-22 · 读码定位

## 竞态链

1. 回填扫描 keyset 分页：`scripts/memory_embedding_backfill.py:215-222` `WHERE id > last_id ORDER BY id ASC LIMIT batch`（默认批 200，两个种子行同页）。
2. 用例 `test_reconcile_mismatch_marks_failed`（`tests/test_memory_embedding_backfill.py:541-573`）经 `RecordingFakeEmbedder.on_text` 在首页 embed 期间（首页扫描**已完成**后）注入并发 NULL 行，id = `uuid.uuid4()`（行 559）。
3. 注入行 uuid **> 首页水位**（≈50%）→ 被下一页扫到并嵌入 → `embedded==3, remaining_null_active==0, status=="pass"` → 断言 `embedded==2 / status=="failed"` 翻车。
4. 注入行 uuid **< 水位** → 永不入页 → `remaining==1 != failed==0` → `status=="failed"` → 预期路径。

## 修复方向裁定

并发注入行用**确定性小 id**（`UUID(int=1)` 或由种子行 `min(id)` 推导减一），恒落水位的「过去」侧 → 断言恒成立。不改 `run_backfill` 生产分页（keyset 幂等性是生产正确性来源，动不得）。备选（不取）：threading.Event 钉注入时机 —— 注入必然发生在首页扫描后，时序钉不死 uuid 排序问题，id 才是变量本体。
