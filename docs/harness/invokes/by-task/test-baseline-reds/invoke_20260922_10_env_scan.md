# invoke · 10-task · 环境/依赖钉版核对（排除项）

> hat=10 · 2026-09-22

## 核对结果

| 项 | 仓内钉版 | 本机 venv 实装 | CI 安装 | 结论 |
|----|----------|----------------|---------|------|
| pytest-asyncio | pyproject `>=0.23,<1` · uv.lock **0.26.0** | **0.26.0**（`.venv/bin/python` 实证） | `uv pip install "pytest-asyncio>=0.23,<1"` → 0.26.0 | **对齐 · 排除版本漂移假设**（初查时 `pip list` 读到 pyenv 全局 1.4.0 系误读，已用 venv 路径复核纠正） |
| pytest | `>=8.2,<9` | 8.4.2 | 同钉版 | 对齐 |
| CI PG service | — | — | pytest.yml **无 postgres service** | CI DB 用例全 skip（假绿 · 见 rootcause_chat_ws L4） |
| 宿主代理 env | — | `http_proxy/https_proxy/all_proxy=127.0.0.1:7890` · `no_proxy` 含裸 `::1` | 无 | D1-L2 / D2 的环境差异源 |

## 结论

缺陷非依赖版本漂移所致；环境差异 = 宿主 shell 代理 env + CI 无 PG 两层。
