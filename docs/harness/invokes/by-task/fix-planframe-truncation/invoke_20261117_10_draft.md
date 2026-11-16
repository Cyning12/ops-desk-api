# invoke_10 · 起草（fix-planframe-truncation）

## 内容

1. 落 task 档 `docs/tasks/active/task_fix_planframe_truncation.md`
   （照 docs/tasks/done/task_fix_434_worker_thread_upsert.md 模板 ·
   人工闸表三行 approved 引 issue #23 m03064/m03283/m03694 夜间授权 ·
   思考轮 R0-R5 全回填 · 验收 8 条全机判锚）。
2. registry.yaml 追加 entry（status=active · base=6cbb947e ·
   allowed_app_files=[sse_stream.py, hitl/resume.py, history.py] ·
   banned_prefixes=[alembic/, scripts/]）。
3. 勘察结论入档：截断点 sse_stream.py:68 _PAYLOAD_MAX=800 +
   :90-128 _summarize_payload 逐 key 截断，emit :279-329 同一 dict 双用
   （SSE+persist）为根因；第二路径 hitl/resume.py:139-156 同修；
   回放端点 payload 透传零改动；history.py:217 假设破须读时截断。
4. 修法裁定（委派书预批）：落库全文 · SSE 帧面截断保持 · 拆两常量
   （_PAYLOAD_MAX=800 / _PERSIST_PAYLOAD_MAX=32_000 对齐 _ANSWER_MAX）。

## 验证台账

| 项 | 结果 |
|---|---|
| task 档结构（照 fix-434 模板） | 齐备（元信息/人工闸/背景/范围/非范围/失败路径/验收/必读/思考轮 R0-R5/测试策略/修订记录） |
| registry entry | 已追加（active · base=6cbb947e） |
| `npx --yes spec-wave@3.5.0 task lint --file docs/tasks/active/task_fix_planframe_truncation.md` | PASS |

## 偏差

无。

## 结果

10 起草完成，进 20-R1 审查。
