---
hat: 10
task_slug: repo-logging-init
date: 2026-10-11
---

# invoke · 10+task 起草 · repo-logging-init（仓级 logging 初始化）

## 落稿摘要

- 首棒（子 Agent 1906fcc0）长读卡滞 · interrupt 留痕 · **00 代笔**（授权 m01606 过程文档代签 · 文档面非实现码不违 delegate-only）。
- 锚点亲读：app/main.py 全文 49 行（lifespan :13-26 无 logging）· app/config.py:11 load_dotenv · 全仓 basicConfig|dictConfig 命中清单（evals/scripts/alembic 自含 · **app/ 零初始化**精确口径）· 55 处 getLogger(__name__) grep 计数 · 源钉案三文档（SPEC §9 序2 / D1 CLOSE 改进建议 #1 / 验收便签坑位 1）。
- 交付：docs/tasks/active/task_repo_logging_init.md——D1 落点三候选（倾向 A 模块级 · 幂等天然）· D2 level 来源（倾向 env OPS_LOG_LEVEL 默认 INFO fail-closed）· D3 format 对齐验收启动器 · D4 uvicorn logger 共存防双行 · 钉死契约 5 · TC1-TC5（TC2=原坑位 1 场景反转实证为核心验收）· 三闸 pending。

## 留 20 审要点

- D1/D2 倾向是否成立（A 最小面 vs C 可演进 · env 口 vs 钉死）。
- TC4「无重复行」机验形态（root handler 与 uvicorn handler 交互实测）。
- 图谱预判（01_modules.md 是否涉 app/main 行）。
