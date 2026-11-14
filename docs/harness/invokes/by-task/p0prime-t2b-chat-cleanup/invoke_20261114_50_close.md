# invoke 50 · CLOSE 登记 · p0prime-t2b-chat-cleanup

- wave_tip：bcf5f12（PR #380 squash · CI 四件全绿）。
- 目标测试 56 passed（本地真 PG）；迁移 up/down/up 于 scratch 库 opsdesk_t2b_scratch 实证（down 三表复现 · 再 up 消失）。
- 干净 worktree /tmp/opsdesk-api-t2b 全量：2093 passed / 2 skipped / 1 failed（唯一红=既有 ta2 · baseline 同红 · 另卡 fix-ta2-hitl-ttl-db-store 承接）。
- 偏差 ①：CI 首波 lint-wiki-delta 红——task 档模板 wiki_delta/wiki_delta_note 两行缺失，补登 amend（7b08796f）后复绿；教训=新 task 档必须带 wiki_delta 字段。
- 偏差 ②：实施面追加 app/ops/session/history.py 删除（唯一 import OpsRun 的生产残留 · 实扫零调用方），registry allowed_app_files 已同步补登三件。
- 偏差 ③：test_wave_gate_registry 在途面含未提交 app/ 改动会咬 closed entry 白名单锚——先 commit 再跑闸（教训沿用）。
- 归档导出（prod cynaya.cn 旧 chat 三表数据导出）为运营侧动作，本卡仅落代码与迁移；导出窗口由维护者择机执行，drop 迁移已随本 wave 入库（如导出未完成，可对 prod 延后执行迁移）。
