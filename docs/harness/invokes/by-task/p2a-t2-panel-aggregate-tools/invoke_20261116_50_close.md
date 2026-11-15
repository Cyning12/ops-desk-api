# invoke · 50_close · p2a-t2-panel-aggregate-tools

## 内容

CLOSE 关账：registry T2 entry status=closed 钉 wave_tip=94f5ba87（feat PR #404 squash merge sha）· task 档迁 done（验收全勾 · 自检结论回填 · 状态行 closed）· 01_modules.md capability 行 P2a-T2 备注 + HG-GRAPH-MODULES 签收行（承 :135 T1 先例）· 本 invoke 落盘。

## 验证台账（终）

| 项 | 结果 |
|---|---|
| feat 波 | PR #404 squash merge 94f5ba87 · CI 四绿（pytest/check/import-linter/lint-wiki-delta） |
| 全量对拍 | branch 提交后余红 16 枚 == base 8af02c4a worktree 16 枚逐名恒等（零新红） |
| 目标套件 | capability 电池 150 passed 0 failed · 新文件 24 例 PG 零 skip |
| registry | status=closed · wave_tip=94f5ba87 · yaml.safe_load 通过 |
| 图谱 | capability 行备注 + 人签记录签收行 · graph-compile 绿 |

## 偏差终录

1. when_to_use loader 必填非空（manifest.py:523-526）→ 填简短引导（承 T1 先例 · when_not_to_use 不填）。
2. V10 output_schema 白名单原仅 required/min_items/empty_is_suspicious → 扩 nullable（同款非空 $ 路径校验 · result_contract 不消费纯声明面）承载设计 §1.4/§1.5 空数据 null 逐键声明；allowed_app_files 随扩 manifest.py。
3. builtin.v1.yaml 头注释「五枚」stale（T1 遗留）顺手纠为「九枚」。
4. 六处同性质 count 锚 7→9 既定后果推进（断言语义不动）。
5. 本地 .env OPS_CAPABILITY_EXTRA_MANIFESTS 污染面新发现（test_ops_write_catalog_reconcile opening_gates 断言）→ 测试策略钉五键 blank；CI 无 .env 为终裁。

## 结果

本 invoke 随 CLOSE 提交落盘；CLOSE PR 合并后本单关账完成。给 T4 交接：锚推进须全仓 grep 而非只靠本地红 · CI（无 .env）终裁 · 委派层用例须 monkeypatch.delenv · 五键 blank 协议（T2 起含 EXTRA_MANIFESTS）· 脏树期在途面守卫三枚红为结构性常态提交后复绿 · V10 nullable 声明面已开（后续工具空数据 null 逐键沿用）· registry wave_tip 钉 94f5ba87。
