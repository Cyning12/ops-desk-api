# 架构浏览器（Arch Browser）

> **角色**：把 Agent Host 概念大纲与 `_tech_graph` 工程真值编成**可点击**静态 HTML。  
> **纪律**：原 MD / YAML **不删除**；本目录 HTML/`site-data.json` 为**衍生只读视图**。  
> **对照**：[`../discussions/2026-09-24_agent-host_current_architecture_v1_zh.md`](../discussions/2026-09-24_agent-host_current_architecture_v1_zh.md)  
> **SPEC 系列（升级轨道）**：[`../spec/arch-browser/README.md`](../spec/arch-browser/README.md) · 主文 `SPEC-arch-browser_v0.md` · 波次 `01_execution_waves.md`

## 打开

```bash
# 仓根
python3 docs/arch-browser/scripts/build_site.py
cd docs/arch-browser/dist && python3 -m http.server 8765
# 浏览器打开 http://127.0.0.1:8765/
```

若应用已挂载静态路由：`GET /docs/arch-browser/`（见 `app/main.py`）。

## 目录

| 路径 | 说明 |
|------|------|
| `catalog/host_outline.json` | Host 五层 + M01–M34 薄目录（人维） |
| `catalog/crosswalk.yaml` | Host # ↔ tech_graph module/flow/波次（人维） |
| `catalog/home_narrative.json` | 首页理念文案 + 场景占位（简历向） |
| `scripts/build_site.py` | 聚合 graph.json + MD 摘要 → `dist/site-data.json` |
| `web/` | 静态壳源（index/app/style） |
| `dist/` | 生成物（可直接静态托管） |

## 路由

| Hash | 含义 |
|------|------|
| `#/` | 首页：理念 + 状态色 mermaid（可点）+ 场景占位 + chip 备用 · 工程入口 |
| `#/host` · `#/host/{n}` | Host 目录 / 模块详页 |
| `#/eng/l0` | 工程图谱（原 G-L0 · 00_main）：Mermaid 可点钻取 flow/module |
| `#/eng/flow/{id}` · `#/eng/module/{id}` | 工程钻取 |
| `#/eng/l2?path=` | G-L2 indexes |
| `#/wave` · `#/wave/N2` | 规划叠层 |

## 默认 Mermaid 组件

所有可点击图谱统一走 `web/app.js` 的 `mermaidPanelHtml` + `mountMermaid`：

- 工具栏：缩小 / 放大 / 1:1 / 适应宽度 / 复制源码
- 适应宽度：`(视口宽) / (图 viewBox·maxWidth 设计宽)`，视口 ≥ 图宽 → 100%（非写死 48%）
- 主布局无 max-width 封顶，仅 `min-width: 720px`；SVG 用自然像素宽 + transform 缩放
- 滚轮缩放、空白处拖拽平移；节点点击自管 hash 跳转

后续新图只调用 `mermaidPanelHtml(src, hint)`，勿再手写裸 `.mermaid-box`。

## 真值

| 面 | 源 |
|----|-----|
| 概念 / 状态 / 缺口 | `docs/discussions/**` |
| 工程节点边 | `docs/_tech_graph/shared/graph.json`（`graph-compile` 产物） |
| 交叉映射 | `catalog/crosswalk.yaml` |
| 规划波次 | 扩展策略 N0–N5 + crosswalk `future.wave` |

改图谱后建议：`./scripts/graph-compile.sh` → `python3 docs/arch-browser/scripts/build_site.py`。

## 非目标

不替代 `graph-compile`；不做在线编辑；不在 HTML 内手改架构结论。

## SpecWave 提示

HG-SPEC-SIGNOFF=signed（2026-11-07，维护者授权 lead 代行）。W1 已交付：白名单源 MD（45 篇）随 build 复制进 `dist/docs/`，`#/doc?path=` 查看器（marked + mermaid 就地渲染），详页源链命中白名单走站内链接。W2–W4 待逐波人签后拆 task。
