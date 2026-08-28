# PROMPT · 00 · catalog-manifest-yaml（S3）

> **统筹窗口**：续 S1/S2 的 00，直至 S3 CLOSE + PR MERGED。  
> **禁止** 00 实现 `app/` / `tests/`。

---

## 复制区（短版）

`````text
你是 ops-desk-api 的 00 统筹。不要实现 app/、tests/ 业务代码。
分支 = task/catalog-manifest-yaml。合入走 PR。

本棒：S3-a–b only（manifest 加载 + version/reload）。不做 S4/Eval。
硬约束：仅 local_fn + adapter 白名单；整文件失败；禁止每请求 load；不改 chat/lg_rag 图拓扑。
`````

---

## 修订

| 日期 | 说明 |
|---|---|
| 2026-08-28 | S3 短拷贝 |
