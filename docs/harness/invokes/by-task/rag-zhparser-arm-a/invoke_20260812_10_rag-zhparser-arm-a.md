# Invoke：10 · rag-zhparser-arm-a（方案固化）

---

## 元信息表


| 字段                     | 值                                                               |
| ---------------------- | --------------------------------------------------------------- |
| hat_id                 | 10                                                              |
| task_slug              | `rag-zhparser-arm-a`                                            |
| task_paths             | `docs/tasks/active/task_rag_zhparser_arm_a.md`                  |
| related_review_or_none | （待）`docs/harness/reviews/task_rag_zhparser_arm_a_audit_R1_*.md` |
| git_branch             | `task/rag-zhparser-arm-a`                                       |
| created_utc_or_local   | 2026-08-12                                                      |
| notes                  | 自 master 新开分支；固化维护者 Dockerfile/COPY/判读补充；**未进 30**              |


---

## GATE_VERIFY（首输出摘要）


| human_gate_id | task表status | blocks_30 | 30可开工？ |
| ------------- | ----------- | --------- | ------ |
| HG-TASK-DRAFT | approved    | N         | —      |
| HG-AUDIT-R1   | pending     | Y         | **N**  |


reviews R1：否 · pre-30 invoke 10：本文件 · 结论：**STOP 改码** · 待 HG-AUDIT-R1

---



## 本轮交付（10 · 文档/方案）

1. 自 `origin/master` 开分支 `task/rag-zhparser-arm-a`
2. 回写 task：镜像 Dockerfile 要点、影子库 SQL、`COPY` 灌库（禁全量 dump）、英文退化实测、判读三档（含 +5～8pp 弃 A）、评测 DSN/`RAG_FTS_CONFIG`
3. 注明：关键词路 query 与 index 必须同 `chinese`（env 切换，不改 RRF）

禁止本轮：改 `app/**`、建镜像落地、碰主库。

---



## 下一闸

维护者签 `HG-AUDIT-R1` + 落 R1 审查文后，再开 30：`Dockerfile.pg-zhparser`、影子初始化脚本、`RAG_FTS_CONFIG`、跑 r4-A。