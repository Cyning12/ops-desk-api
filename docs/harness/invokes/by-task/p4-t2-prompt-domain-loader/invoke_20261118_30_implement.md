# invoke · 30 实现 · p4-t2-prompt-domain-loader

> **task_slug**：p4-t2-prompt-domain-loader
> **日期**：2026-11-18
> **授权**：issue Cyning12/ops-desk-workspace#23（m03064/m03796 夜间授权 · 委派书 p4-t2-prompt-domain-loader）· 闸真源 task 人工闸表三行 approved（HG-AUDIT-R1 = R1 审查文 GO）· VERIFY: PASS 放行

## 内容

1. **app/ops/prompts/domain_context.py**（新建 · stdlib only · 仿 tenant_context.py）：DEFAULT_DOMAIN="ops" · OPS_DOMAIN_ENV="OPS_DOMAIN" · _DOMAIN_RE=[a-z0-9_]+ · resolve_domain(raw)（缺省/空白→ops · 非法→@cache _resolve_cached 回退 ops+logger.warning 一值一次）· resolve_domain_from_env() · current_domain()（contextvar 已注入用注入值 · 未注入回落 env 解析=R3 裁定）· set_current_domain(domain)->Token（词表外 ValueError 编程错误面）· reset_current_domain(token)。
2. **app/ops/prompts/loader.py**（19 §3.1）：docstring 补域纪律段；+_DOMAIN_RE；load_asset(template_id, domain=None)——domain 非空 → 词表校验（非法炸「非法 domain（拒绝路径入参）」）→ assets/<domain>/<id>.md is_file 则 _load_from_path 域件 · 否则回退根件；读取校验主体抽 _load_from_path(path, template_id)（根/域同校验面 · 坏域件 PromptAssetError 显式炸点名路径 · 否半份合并）；缓存键=(template_id, domain)。
3. **app/ops/prompts/templates.py**（19 §3.2）：docstring「10 模板」→11 + 补 §3.2 段；+get_template_for_domain(template_id, domain) 薄封装（白名单外 KeyError 原样 · load_asset 带 domain · 返回 {"version","body"} dict）；_TEMPLATE_IDS 11 id 与 TEMPLATES import 期构建零改（ops 默认面零 diff）。
4. **app/ops/prompts/render.py**（19 §3.3 调用点零 churn）：get_template 域路由——domain=current_domain()；非 ops → get_template_for_domain（KeyError→PromptTemplateNotFoundError from None）；ops → TEMPLATES.get（同对象 · 现状同路径零 diff）。mypy 类型收窄冲突重构：raw: dict[str, str] | None 前置声明 + if/else 赋值 + 统一判 None + 单一 return（mypy/ruff 双绿）。render() 本体零改。
5. **app/ops/lg_rag/run_worker.py**：import domain_context 三函数；_main() 开头 domain_token = set_current_domain(resolve_domain_from_env())（tenant_token 之前 · 与 set_current_tenant 同位）；finally 末尾 reset_current_domain(domain_token)（恒 reset）。
6. **tests/test_prompt_domain_assets.py**（新建 · 18 用例 · tmp_assets fixture 承 test_prompt_assets.py:146-151 + autouse _clean_domain_env）：域命中 / 缺失回退（按模板独立 · 否半份合并）/ 坏域件显式炸点名 oa 路径 / 非法 domain 六负例（五值+「..」路径穿越）/ resolve_domain 缺省·空白·词表 / 非法 warning（caplog）/ current_domain env 回落 / set-reset / ValueError / 白名单 KeyError / get_template_for_domain 命中+回退 / get_template ops 同对象+域路由命中+回退+NotFound / 19 §3.4 三态对拍（off vs OPS_DOMAIN=ops vs 不存在域目录 · 真实资产面全 11 id body 逐字节等）/ worker 注入（mock astream 捕获 current_domain()=="oa" · patch event_store.persist_run_event+sse_stream.persist_thread_turns · user_id 用 uuid4 避 UUID 列撞型）。
7. **图谱登记**：docs/_tech_graph/l1/01_modules.md lg_rag 行（:35）末补 P4-T2 备注 + HG-GRAPH-MODULES 签收行（承 :47 P2c-T1 先例）；graph-compile.sh done OK。

## 验证台账

| 检查 | 结果 |
|------|------|
| pytest 新文件 tests/test_prompt_domain_assets.py（真 PG 五键 blank） | 18 passed |
| pytest 六文件回归（+test_prompt_assets/test_prompt_assembly/test_prompt_packs/test_prompt_slots/test_lg_rag_sse_run_worker） | 144 passed |
| ruff check app tests（0.15.21 · CI 钉版） | All checks passed |
| mypy 五件 app 文件 | Success: no issues found |
| lint-imports（12 contracts） | 12 kept, 0 broken |
| scripts/graph-compile.sh | done OK |

## 偏差

1. current_domain() 未注入回落 resolve_domain_from_env()（R3 裁定 · R1 审查文已确认为唯一偏差 · GO 不阻塞）。
2. render.py get_template 因 mypy 类型收窄冲突做等体重构（raw 前置声明 + 单一 return · 行为零 diff · mypy/ruff 双绿实证）。

## 结果

30 实现完成（提交 46b3cea）· 进 40 验证波。
