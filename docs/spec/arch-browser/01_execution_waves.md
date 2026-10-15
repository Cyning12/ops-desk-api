# Arch Browser · 执行波次（W0–W4）

> **上游**：[`SPEC-arch-browser_v0.md`](./SPEC-arch-browser_v0.md)  
> **纪律**：每波单 task（或明确子棒）；人签前 W1+ 不开 30；合入后建议 `build_site.py` 再部署

---

## W0 · 初版基线（本 PR）

| 项 | 内容 |
|---|---|
| **状态** | **已实现**（随 `docs/arch-browser` 初版 PR） |
| **产物** | catalog + web 壳 + build + dist + `/docs/arch-browser` mount + 首页理念/状态色 Mermaid/场景占位 |
| **验收** | 主 SPEC §5 |
| **后续** | 不重做；缺陷走 `fix/arch-browser-*` 小 PR |

---

## W1 · 源文档真 URL + MD / Mermaid 查看器

| 项 | 内容 |
|---|---|
| **目标** | 详页「源文档」可打开；支持 Mermaid 渲染（浏览器内） |
| **建议做法** | `build_site.py` 按白名单复制 `sources[]` / `source_md_rel` → `dist/docs/...`；新增 `#/doc?path=` 查看器（marked + mermaid）；链改为站内真路径 |
| **白名单（草案）** | `docs/discussions/agent-host-current-architecture/modules/*.md` · 总览/扩展策略两篇 · crosswalk 引用的 `_tech_graph/l1/*.md`（**禁** `.env` / secrets / harness invoke 私货） |
| **开放裁定** | 主 SPEC Q2 |
| **建议分支** | `task/arch-browser-w1-doc-viewer` |
| **test_strategy** | build 后断言白名单文件存在于 dist；查看器对含 mermaid 的样例 MD 冒烟 |

---

## W2 · 生产公开入口（Nginx）

| 项 | 内容 |
|---|---|
| **目标** | `https://www.cynaya.cn/docs/arch-browser/` 登录/未登录均可看 |
| **建议做法** | workspace `deploy/nginx/ops-desk.conf` 增 `location /docs/arch-browser/` → `proxy_pass http://127.0.0.1:8000/docs/arch-browser/`（或 alias 磁盘 dist）；api deploy 带上 dist；**不**改 Vue 登录守卫 |
| **前置** | 主 SPEC Q1 人裁定「未登录可读」 |
| **跨仓** | Nginx 真值在 `ops-desk-workspace/deploy/`；本波 api 侧只保证 mount + dist 入库 |
| **建议分支** | api：`task/arch-browser-w2-mount-verify` · workspace：另 PR nginx |
| **回滚** | 删 nginx location + reload |

---

## W3 · 使用场景模块（填占位）

| 项 | 内容 |
|---|---|
| **目标** | 首页/独立 `#/scenarios` 展示真实请求路径故事 + 可选证据链 |
| **建议做法** | 扩展 `home_narrative.json` 或新 `catalog/scenarios.yaml`；build 写入 `site-data.json`；去掉「设想 · 未填充」或仅保留未就绪项 |
| **内容纪律** | 不泄露租户数据；证据用仓内公开 reports/discussions 相对路径 |
| **开放裁定** | 主 SPEC Q3 |
| **建议分支** | `task/arch-browser-w3-scenarios` |

---

## W4 · 简历包装与韧性

| 项 | 内容 |
|---|---|
| **目标** | 用人单位弱网/无 CDN 仍可用；可选打印/分享摘要 |
| **建议做法** | mermaid/marked vendor 进 `dist/vendor/`；`home_narrative` 增「给招聘官的 60 秒读法」；可选 `prefers-reduced-motion` |
| **开放裁定** | 主 SPEC Q4 |
| **建议分支** | `task/arch-browser-w4-resume-harden` |

---

## 波次依赖

```text
W0 (done) → W1 (doc viewer)
         ↘ W2 (nginx)     【W1/W2 可并行，W2 不依赖查看器】
         ↘ W3 (scenarios) 【可与 W1 并行】
              → W4 (harden) 【建议 W1 后再做 vendor】
```

---

## 修订记录

| 日期 | 说明 |
|------|------|
| 2026-10-14 | 初稿：W0 基线 + W1–W4 升级认领面 |
