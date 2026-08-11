# 金样 query 生成 Prompt 包（task golden-query-set-v1）

用法：每节整体复制贴入网页版三方 chat → 回收 YAML → 人筛选 + 标注 expect_hit。
模式：URL 链接（需三方能联网抓取）。
负样本不进本包（人写，防泄漏进语料）。

---

## 象限：ZH问→EN文档

### P01 · issue #43

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #43：
标题：feat(tui): persistent usage indicator in footer
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/43
```

### P02 · issue #705

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #705：
标题：[Bug] Provider API error 400: assistant message with 'tool_calls' missing corresponding tool response (tool_call_id Read:158)
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/705
```

### P03 · issue #1138

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #1138：
标题：MCP tools/list_changed notifications do not refresh session-visible tool registry
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/1138
```

### P04 · issue #1566

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #1566：
标题：[Feature Request] Open marketplace JSON submission/review process for community plugins
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/1566
```

### P05 · issue #1924

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #1924：
标题：Background tasks marked "lost" without liveness check; resume spawns duplicate concurrent workers
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/1924
```

### P06 · issue #2157

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #2157：
标题：feat: expose account quota (weekly + 5h + reset) through a machine-readable channel
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/2157
```

### P07 · issue #2358

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #2358：
标题：kimi -p (non-interactive) hangs and produces zero output, while the interactive TUI works with the same credentials
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/2358
```

### P08 · issue #2548

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #2548：
标题：Web UI: unbounded DOM node / listener / heap growth in long sessions (detached DOM leak, no list virtualization, per-instance global scroll listeners)
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/2548
```

### P09 · issue #87

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #87：
标题：Fail to launch Kimi-code
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/87
```

### P10 · issue #1885

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #1885：
标题：feat(tui): mirror working state into terminal title (OSC 0) for terminals that can't render OSC 9;4
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/1885
```


---

## 象限：ZH问→ZH/混合文档

### P11 · issue #173

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #173：
标题：[Bug] Subagents cannot discover package-level AGENTS.md due to shared Kaos cwd
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/173
```

### P12 · issue #325

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #325：
标题：审批模式 Approved for session 失效
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/325
```

### P13 · issue #525

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #525：
标题：DeepSeek 模型使用 openai-legacy provider 时 xhigh/max thinking effort 被错误 clamp 为 high (v0.11.0 regression #457)
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/525
```

### P14 · issue #981

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #981：
标题：终端流式输出时偶尔自动滚动到顶部（pi-tui fullRender 触发清屏）
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/981
```

### P15 · issue #1356

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #1356：
标题：kimi update fails to detect npm-global install source on Windows Git Bash (EINVAL in execFile)
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/1356
```

### P16 · issue #1909

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #1909：
标题：[Bug] wind-allskill 插件完全不可用：agent_gw Python SDK 未预装导致 NETWORK_ERROR
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/1909
```

### P17 · issue #2111

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #2111：
标题：fix(tui): /provider 命令 UI 文案承诺 refresh 但未实现入口，且 refresh 端点对无 source 的 provider 是 no-op
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/2111
```

### P18 · issue #2380

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #2380：
标题：MCP client 收到 -32600 Unknown session id 后不自动 reinitialize，重试仍原样重发旧 session id（Streamable HTTP，server 重启后）
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/2380
```

### P19 · issue #87

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #87：
标题：Fail to launch Kimi-code
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/87
```

### P20 · issue #1885

```text
你是企业研发协作工具的用户。阅读下面的 GitHub issue，生成 2 个中文问题。
要求：
- 模拟真实用户：遇到现象问原因 / 想调配置问安全值 / 关心成本问开销 / 对比行为差异 / 问内部机制
- 不复述标题；口语化但保留关键技术词（函数名、配置项）
- 答案必须能在正文中找到（至少部分覆盖）
- 只输出 YAML，不要任何解释：
- query: "……"
  angle: 原因|配置|成本|对比|机制

issue #1885：
标题：feat(tui): mirror working state into terminal title (OSC 0) for terminals that can't render OSC 9;4
正文：
请联网阅读这个 GitHub issue（JSON 格式，body 字段为正文）：
https://api.github.com/repos/MoonshotAI/kimi-code/issues/1885
```


---

## 象限：EN问→EN文档

### P21 · issue #225

```text
You are a user of an engineering-collaboration tool. Read the GitHub issue below and write 2 questions in English.
Rules:
- Real user voice: root cause / safe config value / cost / behavior difference / internals
- Do not restate the title; keep key technical terms (function names, config keys)
- The answer must be findable in the body (at least partially)
- Output YAML only, no explanation:
- query: "……"
  angle: cause|config|cost|comparison|mechanism

issue #225:
Title: Test suite is not portable on Windows (path separators, path.resolve, platform-conditional snapshots, shell)
Body:
Read this GitHub issue via web (JSON; the body field is the content):
https://api.github.com/repos/MoonshotAI/kimi-code/issues/225
```

### P22 · issue #800

```text
You are a user of an engineering-collaboration tool. Read the GitHub issue below and write 2 questions in English.
Rules:
- Real user voice: root cause / safe config value / cost / behavior difference / internals
- Do not restate the title; keep key technical terms (function names, config keys)
- The answer must be findable in the body (at least partially)
- Output YAML only, no explanation:
- query: "……"
  angle: cause|config|cost|comparison|mechanism

issue #800:
Title: ACP authorization responses return only "bash" — makes automatic authorization impossible
Body:
Read this GitHub issue via web (JSON; the body field is the content):
https://api.github.com/repos/MoonshotAI/kimi-code/issues/800
```

### P23 · issue #1219

```text
You are a user of an engineering-collaboration tool. Read the GitHub issue below and write 2 questions in English.
Rules:
- Real user voice: root cause / safe config value / cost / behavior difference / internals
- Do not restate the title; keep key technical terms (function names, config keys)
- The answer must be findable in the body (at least partially)
- Output YAML only, no explanation:
- query: "……"
  angle: cause|config|cost|comparison|mechanism

issue #1219:
Title: pip install kimi-code installs an outdated version; requires re-downloading via install.sh
Body:
Read this GitHub issue via web (JSON; the body field is the content):
https://api.github.com/repos/MoonshotAI/kimi-code/issues/1219
```

### P24 · issue #1685

```text
You are a user of an engineering-collaboration tool. Read the GitHub issue below and write 2 questions in English.
Rules:
- Real user voice: root cause / safe config value / cost / behavior difference / internals
- Do not restate the title; keep key technical terms (function names, config keys)
- The answer must be findable in the body (at least partially)
- Output YAML only, no explanation:
- query: "……"
  angle: cause|config|cost|comparison|mechanism

issue #1685:
Title: ACP: expose undo and session fork/close (btw support)
Body:
Read this GitHub issue via web (JSON; the body field is the content):
https://api.github.com/repos/MoonshotAI/kimi-code/issues/1685
```

### P25 · issue #1943

```text
You are a user of an engineering-collaboration tool. Read the GitHub issue below and write 2 questions in English.
Rules:
- Real user voice: root cause / safe config value / cost / behavior difference / internals
- Do not restate the title; keep key technical terms (function names, config keys)
- The answer must be findable in the body (at least partially)
- Output YAML only, no explanation:
- query: "……"
  angle: cause|config|cost|comparison|mechanism

issue #1943:
Title: [Bug] 0.27.0 web server process repeatedly dies with SIGSEGV in V8 GC marking — 6 crashes in ~26 h
Body:
Read this GitHub issue via web (JSON; the body field is the content):
https://api.github.com/repos/MoonshotAI/kimi-code/issues/1943
```

### P26 · issue #2163

```text
You are a user of an engineering-collaboration tool. Read the GitHub issue below and write 2 questions in English.
Rules:
- Real user voice: root cause / safe config value / cost / behavior difference / internals
- Do not restate the title; keep key technical terms (function names, config keys)
- The answer must be findable in the body (at least partially)
- Output YAML only, no explanation:
- query: "……"
  angle: cause|config|cost|comparison|mechanism

issue #2163:
Title: ACP: agent-initiated turns (background task completions, cron fires) never emit session/update while no prompt is in flight
Body:
Read this GitHub issue via web (JSON; the body field is the content):
https://api.github.com/repos/MoonshotAI/kimi-code/issues/2163
```

### P27 · issue #2370

```text
You are a user of an engineering-collaboration tool. Read the GitHub issue below and write 2 questions in English.
Rules:
- Real user voice: root cause / safe config value / cost / behavior difference / internals
- Do not restate the title; keep key technical terms (function names, config keys)
- The answer must be findable in the body (at least partially)
- Output YAML only, no explanation:
- query: "……"
  angle: cause|config|cost|comparison|mechanism

issue #2370:
Title: Expose steering over ACP: map _session/steering to the existing Session.steer()
Body:
Read this GitHub issue via web (JSON; the body field is the content):
https://api.github.com/repos/MoonshotAI/kimi-code/issues/2370
```

### P28 · issue #2549

```text
You are a user of an engineering-collaboration tool. Read the GitHub issue below and write 2 questions in English.
Rules:
- Real user voice: root cause / safe config value / cost / behavior difference / internals
- Do not restate the title; keep key technical terms (function names, config keys)
- The answer must be findable in the body (at least partially)
- Output YAML only, no explanation:
- query: "……"
  angle: cause|config|cost|comparison|mechanism

issue #2549:
Title: Feature: runtime skill source toggles and per-name skill exclusion
Body:
Read this GitHub issue via web (JSON; the body field is the content):
https://api.github.com/repos/MoonshotAI/kimi-code/issues/2549
```
