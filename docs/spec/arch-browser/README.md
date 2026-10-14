# Arch Browser · SPEC 系列入口

> **Open Folder**：`ops-desk-api/`  
> **实现目录**：`docs/arch-browser/`（衍生静态视图 · **不**替代 discussions / `_tech_graph` 真值）  
> **本系列角色**：把初版交付钉成可升级轨道；后续棒次走 SpecWave（10-spec → 20-audit → 00-task → 30）

## 读序

| 顺序 | 文档 | 说明 |
|------|------|------|
| 1 | [`SPEC-arch-browser_v0.md`](./SPEC-arch-browser_v0.md) | 主 SPEC：目标、范围、纪律、验收、开放裁定 |
| 2 | [`01_execution_waves.md`](./01_execution_waves.md) | 升级波次 W0–W4（拆 task 认领面） |
| 3 | [`../../arch-browser/README.md`](../../arch-browser/README.md) | 实现面打开方式 / 目录 / 路由 |

## 真值对照

| 面 | 路径 |
|---|---|
| 概念 / 模块状态 | `docs/discussions/**` · `docs/arch-browser/catalog/crosswalk.yaml` |
| 工程节点边 | `docs/_tech_graph/shared/graph.json` |
| 首页文案 / 场景占位 | `docs/arch-browser/catalog/home_narrative.json` |
| 构建 | `docs/arch-browser/scripts/build_site.py` · `scripts/arch-browser-build.sh` |
| 静态产物 | `docs/arch-browser/dist/`（`site-data.json` + web 壳） |
| API 挂载 | `app/main.py` → `GET /docs/arch-browser/`（需 dist 存在） |

## SpecWave 提示

- **禁止**在 HTML/`app.js` 手改架构结论；结论只改 discussions / crosswalk / narrative，再 `build_site.py`。
- 升级波次默认 **docs + 静态壳**；Nginx 生产暴露属 workspace/deploy 仓协同（见 W2）。
- 人签 `HG-SPEC-SIGNOFF` 前：可合入初版实现，但 **不**开升级波次的 30 改码 task。
