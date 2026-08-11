# 金样 query 生成 Prompt 包（task golden-query-set-v1）

用法：每节整体复制贴入网页版三方 chat → 回收 YAML → 人筛选 + 标注 expect_hit。
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
```markdown                                                                                                                                                                                                                                            
     ## Feature Request: Persistent usage indicator in footer                                                                                                                                                                                             
                                                                                                                                                                                                                                                          
     ### Motivation                                                                                                                                                                                                                                       
     Currently, users must actively run `/usage` to check their remaining quota. This makes it easy to unknowingly hit limits mid-session. A persistent, at-a-glance usage indicator in the footer would let users manage their consumption proactively.  
                                                                                                                                                                                                                                                          
     ### Proposed Behavior                                                                                                                                                                                                                                
     Add a **third line** to the TUI footer (or extend line 2) that shows managed-platform usage when the active provider supports it:                                                                                                                    
                                                                                                                                                                                                   
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
## Bug Description

Kimi Code repeatedly fails with a provider API error that makes the session unusable. The error claims an assistant message containing `tool_calls` is not followed by the required tool response messages.

## Error Message

```
400 an assistant message with 'tool_calls' must be followed by tool messages responding to each 'tool_call_id'. The following tool_call_ids did not have response messages: Read:158
```

## Environment

- **Kimi Code version**: 0.14.0
- **Install source**: homebrew
- **OS**: darwin arm64
- **Node.js version**: 26.3.0
- **Wire protocol version**: 1.4
- **Model**: kimi-code/kimi-for-coding
- **Shell**: /bin/zsh
- **Terminal**: zed 1.6.3+stable.306.601ecb3ee5c16940191818ee7f244837abf6983c
- **Session ID**: session_c44fe4ac-ae8b-4e56-a54a-4d37be7a1c47
- **Session title**: based on @.omo what nexts?
- **Workspace**: /Users/irfandi/.local/share/opencode/worktree/91fb77f4c6c843e75d4b0755a138a24dd7e2e7fe/clever-cabin

## Reproduction / Observed behavior

1. Resume an existing session.
2. The assistant emits a tool call with id `Read:158`.
3. Subsequent LLM requests fail with HTTP 400 because the message history is missing the corresponding tool response for `Read:158`.
4. The failure persists across retries and turns, blocking the session completely.

Log excerpt from `logs/kimi-code.log`:

```
2026-06-13T02:33:12.563Z INFO  llm request  turnStep=9.18
2026-06-13T02:33:13.599Z WARN  llm request failed  turnStep=9.18 attempt=1/3 model=kimi-code/kimi-for-coding errorName=APIStatusError errorMessage="400 an assistant message with 'tool_calls' must be followed by tool messages responding to each 'tool_call_id'. The following tool_call_ids did not have response messages: Read:158" statusCode=400
2026-06-13T02:33:13.600Z ERROR turn failed  turnId=9
...
2026-06-13T02:38:05.687Z WARN  llm request failed  turnStep=1.1 attempt=1/3 model=kimi-code/kimi-for-coding errorName=APIStatusError errorMessage="..." statusCode=400
2026-06-13T02:38:28.037Z ERROR compaction failed
  APIStatusError: 400 ... Read:158
```

The error also occurs during compaction, suggesting the corrupted/conversation state is being persisted.

## Expected behavior

- The 
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
# MCP tools/list_changed notifications do not refresh session-visible tool registry

## Summary

Kimi Code connects to MCP servers and discovers tools on connect/reconnect, but the active session tool registry does not refresh when a connected MCP server sends `notifications/tools/list_changed`.

This blocks same-session dynamic MCP workflows, including lazy MCP servers that initially expose a loader tool and then expose real downstream tools after the loader is called.

## Reproduction

Local repro used a stdio MCP fixture and `McpConnectionManager` directly, without a model account or TUI:

1. Start a stdio MCP server that advertises `capabilities.tools.listChanged: true`.
2. Initial `tools/list` returns one tool: `enable_extra_tool`.
3. Call `enable_extra_tool`.
4. The server returns the `tools/call` response, then sends `notifications/tools/list_changed`.
5. A subsequent `tools/list` returns `enable_extra_tool` and `dynamic_echo`.

Before the local patch, the underlying client could re-list the server tools, but `McpConnectionManager` continued exposing only the old session-visible tools.

## Expected

When a connected server advertises `tools.listChanged` and sends `notifications/tools/list_changed`, Kimi should refresh that server's tools and emit the existing MCP status update path so the active session sees the new registry.

## Actual

Kimi discovers tools during connect/reconnect, but does not route MCP SDK `listChanged.tools.onChanged` results back into `McpConnectionManager`.

## Source Locus

- `packages/agent-core/src/mcp/client-shared.ts`
- `packages/agent-core/src/mcp/client-stdio.ts`
- `packages/agent-core/src/mcp/client-http.ts`
- `packages/agent-core/src/mcp/client-sse.ts`
- `packages/agent-core/src/mcp/connection-manager.ts`
- `packages/agent-core/test/mcp/connection-manager.test.ts`

The installed MCP SDK already supports `ClientOptions.listChanged.tools.onChanged` in `@modelcontextprotocol/sdk@1.29.0`.

## Related

- `#965`: schema-size pressure from many MCP tools; lazy loading is one mitigation path.
- `#218`: plugin reload hot-apply, related to MCP server lifecycle but not server-side dynamic tool list notifications.
- `#383`: reload com
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
### Problem / Motivation

Currently, Kimi Code CLI supports a rich plugin ecosystem via the `/plugins` command and marketplace JSON. The marketplace can be customized via `KIMI_CODE_PLUGIN_MARKETPLACE_URL` or `/plugins marketplace &lt;source&gt;`, which is great for personal or team use.

However, there is **no documented way for community developers to submit their plugins to the official marketplace**. This creates a barrier for plugin authors who want to share their work with the broader Kimi Code CLI user base. As a result, many useful community plugins remain undiscoverable unless users manually install them via GitHub URL.

### Request

I would like to request one of the following (or a combination):

1. **Open a submission/review channel** for marketplace JSON entries — similar to how VS Code extensions or Homebrew formulas are submitted. Plugin authors could submit a PR or fill out a form to have their plugin reviewed and added to the official `marketplace.json`.

2. **Document the criteria and process** for getting a plugin listed in the official marketplace. For example:
   - What metadata fields are required/recommended?
   - What trust tier (`kimi-official`, `curated`, `third-party`) applies to community submissions?
   - Are there security review requirements?

3. **Provide a community marketplace JSON** — a separate marketplace file (e.g., `community-marketplace.json`) that accepts submissions with lighter review, while the official marketplace remains for vetted plugins.

### Why this matters

- **Plugin discoverability**: Users browsing `/plugins` won't find community plugins unless they are in the marketplace JSON.
- **Ecosystem growth**: Lowering the barrier to entry encourages more developers to build and share Kimi Code CLI plugins.
- **Trust signals**: A curated marketplace gives users confidence when installing third-party plugins, compared to installing arbitrary GitHub URLs.

### Related

- The marketplace JSON format is partially documented at [Plugins | Kimi Code Docs](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/plugins.html), showing the `version`, `plugins` array with `id`, `displayName`, and `source` fields.
- The t
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
## Summary

When a kimi-code process with live background tasks is still running and a second process resumes the same session, `markLoadedTasksLost` marks the first process's non-terminal tasks as `lost` — **without any liveness probe**, even though the task's PID is persisted on disk. The `resume_hint` returned to the model then explicitly instructs `Agent(resume=agent_id)` on `task.lost`, spawning a **second concurrent worker** on the same task while the first is still alive.

We hit this in production: two subagent instances ran concurrently for ~65 minutes, each editing the same file, each reporting "another session is modifying this file" — they were seeing each other. Both eventually completed; the task record had marked one of them `lost` while it was demonstrably alive.

## Evidence (all paths verified against current master)

1. `packages/agent-core-v2/src/agent/task/taskService.ts:854-869` — `markLoadedTasksLost` iterates ghost tasks and marks every non-terminal one as `lost` and writes it back to disk. There is no `process.kill(pid, 0)`-style probe anywhere in this path.
2. `packages/agent-core-v2/src/agent/task/persist.ts:236,276` — the persisted task record **already contains `pid`** (`LegacyPersistedTask.pid`, mapped in `toProcessTaskInfo`), so the material for a liveness check is on disk, unused.
3. `packages/agent-core-v2/src/session/subagent/tools/agent.ts:481` — `resume_hint` lists `task.lost` as a recovery case and tells the model to call `Agent(resume=agent_id)`, which makes duplicate workers a scripted outcome rather than an accident.
4. There is no per-session cross-process lock, so two processes resuming the same session (e.g. a supervisor that spawns one CLI process per message with `--resume`) race: the live one's tasks get marked `lost`, and the task JSON itself is last-writer-wins between the two processes.

This is the same "killed but not reaped" family as #1882 (torn `wire.jsonl` after SIGKILL), one layer up in the stack.

## Suggested fixes (in order of effort)

1. **Probe before marking lost** (small): in `markLoadedTasksLost`, for `kind === 'process'` ghosts, run `process.kill(pid, 0)`. If the process is alive, keep the task `ru
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
## Summary

`/status` and `/usage` compute the account quota (weekly limit, 5-hour rolling window, and each reset time), but this data is only reachable **inside the interactive TUI**. There is no non-interactive way for an external tool to read it — no headless subcommand, no persisted cache file, and no hook payload field carries it.

## Why this matters

External monitors — notch/menu-bar apps, status widgets, dashboards, multi-agent orchestrators — want to surface "how much weekly quota is left, and when it resets" at a glance, across several agents at once. Today the only options are scraping the TUI or calling the provider API directly with the user's token; both are fragile or overreaching for a tool that otherwise only reads local state.

By contrast, Codex persists `token_count.rate_limits` to its local rollout JSONL, and Claude Code exposes rate limits through its statusLine payload, so third-party tools can read account quota **without any network call of their own**. Kimi is the only one with no such channel.

## Proposed options (any one unblocks it)

1. **Headless command** — `kimi usage --json` that prints the same weekly / 5h limits + reset timestamps `/usage` shows, then exits.
2. **Persisted cache file** — write the latest quota snapshot to a stable path under `~/.kimi-code/` after each turn (mirrors Codex's rollout approach).
3. **Hook payload field** — include the quota snapshot in the `Stop` / session hook payload so hook-based integrations receive it live.

## Related (in-TUI display / different channel)

- #872, #764 — same *data*, but requested for the in-TUI status bar
- #1915 — absolute reset time in `/usage`
- #1855 — programmatic *token usage* over ACP (this request is about *account quota* over a machine-readable channel)

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
## Summary

`kimi -p "<prompt>"` hangs indefinitely and writes **zero bytes** to both stdout and
stderr. The interactive TUI works normally at the same time, on the same machine,
with the same credentials and the same binary.

Non-interactive mode worked reliably earlier the same day and then stopped. I have
not been able to recover it.

## Environment

- macOS 26 (Darwin 25.5.0), arm64
- Kimi Code CLI 0.29.2 and 0.30.0 — reproduces on **both**
- Installed at `~/.kimi-code/bin/kimi`
- Auth: OAuth device-code flow (`kimi login`)
- Model: `kimi-k3` (`default_model = "moonshot-ai/kimi-k3"`)

## Reproduction

```bash
kimi -p "Reply with exactly PING"
```

Observed: no output, process never returns. Killed after 60–180s in repeated runs.

```bash
kimi -p "Reply with exactly PING" --output-format stream-json > out.txt 2>err.txt
# out.txt: 0 bytes
# err.txt: 0 bytes
```

The complete absence of output on *either* stream is the notable part — there is no
error, no partial stream, and no timeout from the CLI itself.

Meanwhile, in a terminal, the TUI answers the identical prompt immediately:

```
✨ Reply with exactly KIMI WORKING
● KIMI WORKING
```

## What I ruled out by measurement

- **Not the CLI version.** Reproduces identically on 0.29.2 and 0.30.0. Non-interactive
  mode worked on 0.30.0 for ~40 minutes before it stopped, so this is not a regression
  introduced by the 0.30.0 rollout.
- **Not an expired token.** Reproduces with a token freshly written by `kimi login`
  and valid for another 10+ minutes.
- **Not stdin.** Same behaviour with `< /dev/null`.
- **Not process contention.** Reproduces with no other `kimi` process running except
  the TUI, and also reproduces when a leftover child process is killed first.
- **Not the account or network.** The REST API answers normally throughout:
  `POST https://api.moonshot.ai/v1/chat/completions` with `kimi-k2.6` returns HTTP 200,
  and `GET /v1/models` returns the expected model list.

## Possibly relevant: token lifetime

Immediately after `kimi login`, `~/.kimi-code/credentials/kimi-code.json` contained an
`expires_at` only **15 minutes** in the future. Non-interactive runs failed both inside
and outside that window,
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
**Title:** Web UI: unbounded DOM node / listener / heap growth in long sessions — detached DOM leak, no list virtualization, per-instance global scroll listeners

## Version / Environment

- Kimi Code: 0.31.1 (SEA binary `kimi.exe web`, Windows x64)
- OS: Windows 11 (10.0.26200)
- Browser: Microsoft Edge (Chromium, latest stable)
- Related: #749, #122

## Summary

In the Web UI (`apps/kimi-web`), a long-lived session page accumulates DOM nodes, JS heap and event listeners **monotonically** until scrolling/typing becomes visibly laggy. A forced GC does **not** reclaim the nodes, and a heap snapshot shows ~377k detached DOM nodes. Refreshing the page immediately resets everything, confirming page-lifetime accumulation rather than a browser/OS issue (this is likely the root cause behind the symptoms in #749 and #122).

## Measured evidence (via CDP `Performance.getMetrics` on the live page)

| State | DOM Nodes | JS Heap | JS Event Listeners |
|---|---|---|---|
| Laggy (page open ~long session) | 677,401 | 714 MB | 30,238 |
| Immediately after F5 | 34,603 | 54 MB | 2,236 |
| 20 min after refresh (light use) | 140,750 | 195 MB | 7,780 |

- Forced `HeapProfiler.collectGarbage` (×2) does not reduce the node count → genuinely retained, not GC lag.
- Idle (no streaming): 0 long tasks in an 8s window — the jank appears **during interaction** (scroll/type/new message render), consistent with thousands of per-instance listeners and layout/GC pressure from the huge node pool.
- A same-browser control group (other heavy SPA tabs: 8k–80k nodes) shows no such growth.

## Heap snapshot analysis (1.5 GB snapshot, full parse — 11.8M records)

377,611 detached DOM nodes, top offenders:

- 109,016 × detached `<div data-v-262bbea0>` (= `ToolOutputBlock.vue` root/line divs) + 108,705 detached `Text` nodes (1:1 ratio — rebuilt tool-output block corpses)
- 10,892 × detached `SVGSVGElement` + 10,887 × `SVGPathElement`
- 4,543 × detached `<span class="ui-tip">` (Tooltip), thousands of code-block / think-block remnants

Attached heap highlights: two giant Shiki tokenizer regex strings (94 MB + 34 MB), 82 MB `ExternalStringData`, 1.97M plain `Object`s (full session state), 270k `blink::Uni
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
### What version of Kimi Code is running?

0.2.0

### Which open platform/subscription were you using?

kimi-coding

### Which model were you using?

kimi-for-coding 

### What platform is your computer?

Darwin 24.6.0 arm64 arm

### What issue are you seeing?

全新安装，启动失败；
```text
➜  artemis git:(master) ✗ curl -fsSL https://code.kimi.com/kimi-code/install.sh | bash
==> Detected target: darwin-arm64
==> Resolving latest version from https://code.kimi.com/kimi-code/latest
==> Latest version: 0.2.0
==> Fetching manifest https://code.kimi.com/kimi-code/0.2.0/manifest.json
==> Downloading https://code.kimi.com/kimi-code/0.2.0/kimi-code-darwin-arm64
######################################################################## 100.0%##O#-#                                                                         
==> Verifying checksum
==> Installed to /Users/ijkzen/.kimi-code/bin/kimi
==> /Users/ijkzen/.kimi-code/bin already in PATH
==> Done. Run: kimi --version
➜  artemis git:(master) ✗ kimi --version                              
0.2.0
➜  artemis git:(master) ✗ kimi           
 …/Projects/RUST-Project/artemis  master [+283 -101]                                                                                                                                                                                @: mention files | shift+tab: plan mode
                                                                                                                                                                                                                                                              context: 0.0%node:internal/child_process:441
    throw new ErrnoException(err, 'spawn');
          ^

Error: spawn ENOTDIR
    at ChildProcess.spawn (node:internal/child_process:441:11)
    at spawn (node:child_process:796:9)
    at execFile (node:child_process:349:17)
    at /Users/runner/work/kimi-code/kimi-code/apps/kimi-code/dist-native/intermediates/main.cjs:200069:35
    at new Promise (<anonymous>)
    at readPullRequest (/Users/runner/work/kimi-code/kimi-code/apps/kimi-code/dist-native/intermediates/main.cjs:200068:9)
    at refreshPullRequestIfNeeded (/Users/runner/work/kimi-code
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
### What version of Kimi Code is running?

`kimi --version`: `0.27.0`

### What platform is your computer?

Windows 11 x64, VSCode 1.129.0, terminal kept in the **editor area** (a common layout).

### What issue are you seeing?

There is no way to tell at a glance whether Kimi Code is working when the terminal lives somewhere that can't render `OSC 9;4` progress. Concrete case: VSCode editor-area terminal tabs never render `OSC 9;4` (only panel-area tabs do — microsoft/vscode#240117; related: #1884 for the allow-list gap). Inside the TUI the spinner is visible, but the moment you switch to another tab you lose all "is it still working?" signal.

### Proposed solution

Mirror the working state into the **terminal title** (`OSC 0`) while a turn is running, e.g. `<session-label> ⠋` with the braille frame animated on a timer, restored to `<session-label>` when the turn ends. Terminal titles are plain text and render everywhere — panel tabs, editor-area tabs, tmux, web terminals (xterm.js `onTitleChange`), Windows Terminal.

Prior art: Claude Code writes its working state into the terminal title the same way; this is how its users get working-state in tabs.

Ideally behind a config flag (e.g. `tui.toml`), default on or off per maintainer taste.

### Reference implementation (local patch, works today)

I patched the installed `dist/main.mjs` as a stopgap. In the TUI terminal class:

```ts
setTitle(title) {
  title = title && title.length > 10 ? title.slice(0, 10) + "…" : title;
  this._tabStatusTitle = title;
  process.stdout.write(`\x1b]0;${title}\x07`);
}

setProgress(active) {
  if (this._tabStatusTimer) { clearInterval(this._tabStatusTimer); this._tabStatusTimer = undefined; }
  const base = this._tabStatusTitle || "kimi";
  if (active) {
    const frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏".split("");
    let i = 0;
    this._tabStatusTimer = setInterval(() => {
      i = (i + 1) % frames.length;
      process.stdout.write(`\x1b]0;${base} ${frames[i]}\x07`);
    }, 200);
    this._tabStatusTimer.unref?.();
  } else {
    process.stdout.write(`\x1b]0;${base}\x07`);
  }
  // ...original progress-sequence logic unchanged
}
```

Effect in VSCode editor-area tabs: idle `node · 修复登录bu…`, wo
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
## 问题发现 / Discovery

在将 kimi-cli 的 scoped subagent YAML 工作流迁移到 kimi-code 的 hierarchical AGENTS.md 模型时，我们发现子代理无法发现包级别的 AGENTS.md 文件。

When migrating kimi-cli scoped subagent YAML workflows to kimi-code's hierarchical AGENTS.md model, we discovered subagents cannot discover package-level AGENTS.md files.

## 根本原因 / Root Cause

prepareSystemPromptContext(kaos) 通过 kaos.getcwd() 向上遍历目录树来加载 AGENTS.md。会话中的所有代理共享同一个 Kaos 实例（session.config.runtime.kaos）。SessionSubagentHost.spawn() 创建的子代理继承此共享实例，而 configureChild 无条件将子代理的 cwd 设为父代理的 cwd。因此，子代理的 AGENTS.md 发现范围永远被锁定在父代理的工作目录，无法访问包级规则。

prepareSystemPromptContext(kaos) loads AGENTS.md by walking up the directory tree from kaos.getcwd(). All agents in a session share the same Kaos instance (session.config.runtime.kaos). SessionSubagentHost.spawn() creates subagents that inherit this shared instance, and configureChild unconditionally sets the child's cwd to the parent's cwd. Consequently, a subagent's AGENTS.md discovery is permanently locked to the parent agent's working directory — package-level rules are invisible.

## 影响 / Impact

- 在 monorepo 中，无法为 packages/domain、packages/infra 等包作用域子代理加载特定的 AGENTS.md 规则。
- 破坏了 kimi-cli 中通过 scoped subagent YAML 实现的 monorepo 工作流。

- In a monorepo, package-scoped subagents (e.g. packages/domain, packages/infra) cannot load package-specific AGENTS.md rules.
- Breaks monorepo workflows that worked in kimi-cli via scoped subagent YAMLs.

## 最小复现 / Minimal Reproduction

1. 在 monorepo 的根目录和 packages/domain/AGENTS.md 分别创建不同的 AGENTS.md。
2. 从根目录启动会话。
3. 使用 Agent 工具生成一个 coder 子代理，任务涉及 packages/domain。
4. 子代理的系统提示中只会包含根目录的 AGENTS.md，packages/domain/AGENTS.md 不会出现。

1. Create distinct AGENTS.md files at repo root and at packages/domain/AGENTS.md.
2. Start a session from the repo root.
3. Use the Agent tool to spawn a coder subagent with a task involving packages/domain.
4. The subagent's system prompt only contains the root AGENTS.md; packages/domain/AGENTS.md is absent.

## 提议修复 / Proposed Fix

已在 PR #172 中实现，核心思路：

Implemented in PR #172. Core approach:

1. 为 AgentToolInputSchema 添加可选的 cwd 参数。  
   Add an optional cwd parameter to AgentToolInputSchema.
2. 当 cwd 提供时，SessionSubagentHost.spawn() 通过 pa
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
### What version of Kimi Code is running?

0.7.0

### Which open platform/subscription were you using?

kimi code

### Which model were you using?

kimi-k2.6

### What platform is your computer?

_No response_

### What issue are you seeing?

审批模式中选择Approved for session，下次仍需要审批。

### What steps can reproduce the bug?

由于审批不会被/export导出，以下是从命令行中复制的对话。第一段Write不同文件时就会提示审批，第二段执行同样的bash命令也会提示审批。
```
 ✨ 我正在进行测试，接下来按照我的提示进行操作即可，不需要复杂的分析。
    在当前文件写入一个文件，a.txt，写入"1"

 ● 用户要求我在当前工作目录下创建一个文件 `a.txt`，并写入内容 `"1"`。这是一个非常简单的任务，不需要复杂分析，直接用
   `Write` 工具即可。

 ● Used Write (a.txt) · 1 line
      1  1

   Approved for session: Writing a.txt

 ● 用户要求我完成一个简单任务：在当前目录创建 a.txt 并写入 "1"。Write 工具已经成功执行，写入了 1
   字节。任务已经完成，我应该简洁地回复用户确认。

 ● 已写入完成，a.txt 内容为 1。

 ✨ 再执行一次

 ● 用户要求"再执行一次"，意思是在当前文件再次写入 a.txt，写入"1"。这是重复之前的操作，直接用 Write 工具即可。

 ● Used Write (a.txt) · 1 line
      1  1

 ● Write 工具已成功执行，再次写入了 a.txt 文件，内容为 "1"。任务完成，简洁回复用户即可。

 ● 已再次写入完成，a.txt 内容仍为 1。

 ✨ 在b.txt 写入1

 ● 用户要求在 b.txt 中写入 "1"。这是一个简单的写入操作，直接用 Write 工具即可。

 ● Used Write (b.txt) · 1 line
      1  1

   Approved for session: Writing b.txt

 ● Write 工具已成功执行，写入了 b.txt 文件，内容为 "1"。任务完成，简洁回复用户即可。

 ● 已写入完成，b.txt 内容为 1。
   Exporting session as Markdown…
```

```

 ✨ 再执行一次 -c

 ● 用户要求再执行一次 `python -c "print('1')"`。这是一个简单的命令执行请求，直接用 Bash 工具执行即可。

 ● Used Bash (python -c "print('1')")



   Approved for session: Running: python -c "print('1')"

 ● 用户要求"再执行一次 -c"，我已经执行了 `python -c "print('1')"`，输出是 `1`。任务完成，简洁回复即可。

 ● 输出：

     1

 ✨ 好的，再执行一次

 ● 用户要求"再执行一次"，指的是再次执行 `python -c "print('1')"`。这是重复之前的操作，直接用 Bash 执行即可。

 ● Used Bash (python -c "print('1')")



   Approved for session: Running: python -c "print('1')"

 ● 用户要求"再执行一次"，我已经执行了 `python -c "print('1')"` 并得到了输出 `1`。任务完成，简洁回复即可。

 ● 输出：

     1
```

### What is the expected behavior?

_No response_

### Additional information

_No response_
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
# DeepSeek 模型使用 `openai-legacy` provider 时 `xhigh`/`max` thinking effort 被错误 clamp 为 `high`

## 问题描述

当用户配置了 DeepSeek 模型（`deepseek/deepseek-v4-flash`、`deepseek/deepseek-v4-pro` 等）并通过 `openai-legacy` adapter 使用时，`xhigh` 和 `max` 的 thinking effort 会被 `clampChatCompletionsReasoningEffort` 函数强行降级为 `high`，导致 DeepSeek 实际支持的 `max` 级别无法生效。

## 复现步骤

1. 配置 DeepSeek 模型（type = "openai"），例如：
   ```toml
   [models."deepseek/deepseek-v4-flash"]
   provider = "deepseek"
   model = "deepseek-v4-flash"
   capabilities = ["thinking", "tool_use"]
   reasoning_key = "reasoning_content"
   ```

2. 设置 thinking effort 为 `xhigh` 或 `max`：
   ```toml
   [thinking]
   effort = "xhigh"
   ```

3. 发起对话时，实际发送给 DeepSeek API 的 `reasoning_effort` 是 `"high"` 而非 `"xhigh"`/`"max"`。

## 根因分析

问题出在 `packages/kosong/src/providers/openai-legacy.ts:138-146` 的 `clampChatCompletionsReasoningEffort` 函数：

```ts
function clampChatCompletionsReasoningEffort(
  reasoningEffort: string | undefined,
  model: string,
): string | undefined {
  if (reasoningEffort !== 'xhigh') {
    return reasoningEffort;
  }
  return supportsOpenAIChatCompletionsXHighReasoning(model) ? 'xhigh' : 'high';
}
```

该函数调用 `supportsOpenAIChatCompletionsXHighReasoning`（定义在 `capability-registry.ts:209-211`）来判断模型是否支持 `xhigh`，但该函数只检查 OpenAI 的模型白名单：

```ts
const OPENAI_CHAT_COMPLETIONS_XHIGH_REASONING_MODELS = new Set([
  'gpt-5.2',
  'gpt-5.4',
  'gpt-5.5',
]);

export function supportsOpenAIChatCompletionsXHighReasoning(modelName: string): boolean {
  return OPENAI_CHAT_COMPLETIONS_XHIGH_REASONING_MODELS.has(modelIdLeaf(modelName));
}
```

由于 DeepSeek 模型名（如 `deepseek-v4-flash`）不在该白名单中，`xhigh` 和 `max` 被统一降级为 `high`。

## 完整的代码链路

```
用户配置: thinking.effort = "xhigh"
    ↓
thinkingEffortToReasoningEffort("xhigh") → "xhigh"       (openai-common.ts:176-178)
    ↓
clampChatCompletionsReasoningEffort("xhigh", "deepseek-v4-flash")  (openai-legacy.ts:520-528)
    ↓
supportsOpenAIChatCompletionsXHighReasoning("deepseek-v4-flash") → false  (capability-registry.ts:209-211)
    ↓
返回 "high"   ← xhigh 被错误降级
```

同时 `max` 也是同样的命运：
```
thinkingEffortToReasoningEffort("max") → "xhigh"  (openai-common.ts:177-178)
    ↓ ...同样的 clamp 路径...
    ↓ 返回 "high"
```


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
### What version of Kimi Code is running?

kimi, version 0.16.0

### Which open platform/subscription were you using?

Kimi Code

### Which model were you using?

K2.7 Code

### What platform is your computer?

Windows 11, Git Bash (MINGW64)

### What issue are you seeing?

流式输出过程中，终端偶尔会自动跳到最顶部，导致无法看到正在输出的内容，需要手动滚回底部。

### What steps can reproduce the bug?

1. 启动 kimi-code，进行一个会产生较长输出的对话（超过终端视口高度）
2. 当模型先 thinking 再输出 assistant 文本时，thinking 阶段结束切换渲染模式时，终端会跳到顶部
3. 或者在长对话中，任何发生在视口上方的组件渲染变化都可能触发

### What is the expected behavior?

流式输出时终端应保持在底部，跟随最新输出内容，不跳回顶部。

### Additional information

**根因分析**

问题出在底层 TUI 渲染库 `@earendil-works/pi-tui` 的 `doRender()` 方法中。当前版本（0.16.0）依赖的 pi-tui 版本为 `^0.74.0`，经确认最新发布的 0.18.0、0.19.0 也使用相同的 pi-tui 版本，因此该问题在最新版本中同样存在。

在 `tui.js` 第 909 行：

```
if (firstChanged < prevViewportTop) {
    fullRender(true);  // 发出清屏序列
    return;
}
```

当第一条变更行在视口上方时，diff 渲染器认为无法通过增量更新到达，触发全屏重绘。`fullRender(true)` 会发出清屏序列，导致终端从顶部开始重新渲染。

**典型触发场景**：thinking 阶段结束时，`ThinkingComponent` 从 live 模式（带动画 spinner）切换到 finalized 模式（静态文本），渲染输出发生变化。此时 transcript 已超过终端高度，视口在底部（`prevViewportTop > 0`），而 thinking 组件位于 transcript 靠前位置，`firstChanged < prevViewportTop` 条件成立。

**上游修复情况**

pi-tui 最新版本是 **0.79.10**（当前使用 0.74.0），相关修复：
- **0.51.1**：修复了 `prevViewportTop` 计算使用 stale `maxLinesRendered` 导致不必要的 full redraw
- **0.63.0**：修复了内容收缩后 viewport 跟踪错误

**建议**
1. **短期**：升级 `@earendil-works/pi-tui` 到 >= 0.79.10，利用已有的 viewport 跟踪修复减少误触发
2. **根本修复**：在 pi-tui 上游修复 `firstChanged < prevViewportTop` 分支的降级策略
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
## 问题描述

在 Windows 11 上通过 Git Bash 运行 `kimi update` 时，无法检测到 npm 全局安装来源，始终显示：

```
Detected install source: unsupported package manager or layout.
To update manually, run: npm install -g @moonshot-ai/kimi-code@x.x.x
```

即使 kimi-code 已通过 `npm install -g` 安装，`detectInstallSource()` 仍然返回 `"unsupported"`。

## 根因

**源文件**: `apps/kimi-code/src/cli/update/source.ts`

`detectInstallSource` 函数（约第 103 行）调用：

```typescript
execFileText(npmCommand(platform), ["prefix", "-g"])
```

在 `platform === "win32"` 时，`npmCommand` 返回 `"npm.cmd"`。当 Node.js 进程由 Git Bash / MSYS2 环境启动时，`child_process.execFile("npm.cmd", ...)` 会抛出 `EINVAL` 错误（`spawn` 同样失败）。

`catch` 块直接返回 `"unsupported"`，导致 `canAutoInstall` 返回 false，进入手动更新提示分支。

## 复现环境

- OS: Windows 11
- Shell: Git Bash (MSYS2)
- Node.js: v24.18.0 (via fnm)
- npm: 全局 prefix 为 `%USERPROFILE%\.npm-global`

## 验证

```
execFile("npm.cmd", ["prefix", "-g"])           → EINVAL
spawn("npm.cmd", ["prefix", "-g"])              → EINVAL
execFile("npm.cmd", ["prefix", "-g"], {shell:true}) → 正常工作
```

## 修复建议

在 `catch` 块中添加 fallback 启发式检测——当 `npm prefix -g` 因平台兼容性失败时，通过包路径模式判断是否属于 npm 全局安装：

```typescript
} catch {
  // Fallback: when npm prefix detection fails (e.g. EINVAL on Git Bash),
  // check if package path matches a typical npm global node_modules layout
  const normalized = normalizeForHeuristic(packageRoot);
  const npmNodeModulesSeg = `/node_modules/${NPM_PACKAGE_NAME}`;
  const npmLibSeg = `/lib${npmNodeModulesSeg}`;
  if (normalized.endsWith(npmNodeModulesSeg.toLowerCase()) ||
      normalized.endsWith(npmLibSeg.toLowerCase())) {
    return "npm-global";
  }
  return "unsupported";
}
```

npm 全局安装的包路径始终以 `<prefix>/node_modules/@moonshot-ai/kimi-code` 结尾，这个启发式检测无需运行 npm 命令即可完成判断。
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
## 问题概述

`wind-allskill` 插件（Wind 万得数据）在 Kimi 桌面版中返回 `NETWORK_ERROR`，经排查根因为 **`agent_gw` Python SDK 未预装** 在 managed Python runtime 中。该依赖缺失导致 Wind 取数链路在导入阶段即崩溃，用户侧无法通过配置修复。

## 环境信息

| 项目 | 值 |
|------|-----|
| 操作系统 | macOS |
| Node.js 版本 | v24.15.0 |
| Python 版本 | 3.12 (Kimi managed runtime) |
| `KIMI_API_KEY` 环境变量 | ✅ 已设置 |
| `~/.kimi/agent-gw.json` | ❌ 不存在 |
| `agent_gw` Python 包 | ❌ **未安装** |

## 根因分析

### 执行链路

```
用户请求 → wind 技能路由 → cli.mjs → wind_tool.py
                                    ↓
                          from agent_gw import ...  ← 💥 导入失败
                                    ↓
                     SystemExit("Missing dependency: agent-gw...")
                                    ↓
                          NETWORK_ERROR 返回给用户
```

### 关键代码位置

**文件**: `wind-allskill/skills/wind-mcp-skill/scripts/wind_tool.py:28-33`

```python
def _client_cls():
    try:
        from agent_gw import AgentGwClient, AgentGwError
    except ModuleNotFoundError as exc:
        raise SystemExit(
            "Missing dependency: agent-gw. Install it with: "
            'pip install "git+ssh://git@dev.msh.team/leixun/agent-gw-pysdk.git@v0.1.0"'
        ) from exc
```

### 安装尝试

```bash
pip install "git+ssh://git@dev.msh.team/leixun/agent-gw-pysdk.git@v0.1.0"
```

**失败**: `Connection closed by 198.18.0.16 port 22` — 客户端无 SSH 权限访问内部私有仓库。

### 配置 workaround 无效

曾尝试创建 `~/.kimi/agent-gw.json` 作为 workaround，但**无效** — 因为 `agent_gw` 导入失败发生在配置文件读取之前。

## 影响评估

| 插件/功能 | 状态 |
|-----------|------|
| Wind 行情查询 (A股/港股/美股/基金/指数/债券) | ❌ 完全不可用 |
| Wind K 线数据 | ❌ 完全不可用 |
| Wind 财务数据 | ❌ 完全不可用 |
| Wind 选股筛选 | ❌ 完全不可用 |
| Wind 宏观数据 (EDB) | ❌ 完全不可用 |

## 复现步骤

1. 在 Kimi Work 中加载 `wind-allskill` 插件
2. 执行任意 Wind 数据查询，例如：
   ```bash
   node cli.mjs call stock_data get_stock_price_indicators \
     '{"windcode":"688234.SH","indexes":"最新成交价"}'
   ```
3. 返回 `NETWORK_ERROR`，detail 显示 `Missing dependency: agent-gw`

## 建议修复方案

### 方案 A：预装 agent_gw SDK（推荐）

在 Kimi 桌面版的 managed Python runtime 中预装 `agent_gw` 包，或将其作为插件的捆绑依赖自动安装。

参考 Yahoo Finance 插件已采用的安装方式：
```bash
python3 -m pip install "$(curl -s https://cdn.kimi.com/agentgw/pysdk/manifest.json | python3 -c 'import json,sys; print(json.load(sys.stdin
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
## 现象

TUI 里 `/provider` 命令打开的 Provider Manager，文案明明写着可以 refresh，但 UI 上找不到任何 refresh 操作，只能 add / delete。手动调 kap-server 的 `POST /api/v1/providers:refresh` 端点，对没存 `source` 的 provider 也是空打（orchestrator 直接跳过、零网络请求），UI state 也不会更新。要让模型列表真正刷新，只能删掉再重新 add（"reconnect"）才行，绕了一大圈。

复现步骤里详细列了三条独立的失败路径。

## 版本

- `kimi --version` 输出（0.29.0）
- kap-server：`http://127.0.0.1:58627`，单实例 daemon 模式
- 触发问题的 provider（本机环境样例，不代表所有用户）：
  - `minimax-cn-coding-plan`（type: anthropic，无 `source` 字段）
  - `opencode-go`（type: openai，无 `source` 字段）
  - `managed:kimi-code`（type: kimi，OAuth-managed）

## 平台

macOS（arch64），loopback daemon。

## 期望行为

1. `/provider` UI 里有一个显式的 refresh 操作（按键 + 底部 hint 提示），点了之后真的去拉远端模型列表并刷新 UI。
2. `POST /api/v1/providers:refresh`（含 `:refresh_oauth` 和单 provider 的 `{id}:refresh`）对所有已配置 provider 都能产生预期效果：对内置 managed / OAuth / 自定义 registry 的 provider 拉远端 `/models`；对其他类型的 provider 至少给出明确说明（"此 provider 无可刷新的远端来源"），而不是静默 no-op。
3. 远端刷新后 TUI 端的 `availableProviders` / `availableModels` 内存 state 应当跟着 reload，不管 orchestrator 的 `changed` 列表是否为空。

## 复现步骤

### 步骤 1 — UX 文案与实现不一致

打开 TUI，输入 `/provider`：

- 顶部 hint 实际显示：`↑↓ navigate · D delete · Esc cancel`（`apps/kimi-code/src/tui/components/dialogs/provider-manager.ts:48`）
- 命令注册描述却写着：`Manage AI providers (add / delete / refresh)`（`apps/kimi-code/src/tui/commands/registry.ts:197`）

→ "refresh" 在命令描述里被承诺，但 UI 既没有 R 键也没有对应 callback（`ProviderManagerOptions` 接口只有 `onAdd` / `onDeleteSource` / `onClose`，`handleInput` 只识别方向键 / Enter / `D` / `Esc`）。

### 步骤 2 — 后台 refresh 对 UI 不可见，且对多数 provider 是 no-op

`apps/kimi-code/src/tui/kimi-tui.ts:731-735`：

```ts
await this.authFlow.refreshAvailableModels();
void this.refreshProviderModelsInBackground();
```

后台 fire-and-forget 调用 `AuthFlowController.refreshProviderModels()`（scope=`all`）。但底层 `refreshProviderModels()`（`packages/oauth/src/refreshProviderModels.ts:377-766`）的 4 个分支是：

1. `source.kind === 'apiJson'`（自定义 registry）
2. Managed Kimi Code OAuth
3. Open Platform
4. Managed Kimi Code endpoint API-key（**强匹配** `type=kimi` 且 `base_url` 命中 managed endpoint）

`minimax-cn-coding-plan` / `opencode-go` 这类普通带 `apiKey` 的 anthropic/openai provider，4 个分支一个都不命中，orchestrator 直接跳过、零网络请求。

### 步骤 3 — 即使真的改了 co
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
**What version of Kimi Code is running?**

0.30.0（0.29.x 同现）

**Which open platform/subscription were you using?**

Kimi Code（managed:kimi-code，OAuth 登录）

**Which model were you using?**

kimi-code/k3-256k

**What platform is your computer?**

Microsoft Windows NT 10.0.26200.0 x64

**What issue are you seeing?**

Streamable HTTP 的 MCP server 重启后，server 端 session 失效，对后续每个请求返回 `-32600 Unknown session id`（错误文案即协议原文 "client should reinitialize"）。**kimi-code client 不发起新的 `initialize` 握手，而是把同一个已失效的 session id 原样重发**——实测连续 6 个请求（JSON-RPC id 72–77，跨度约 21 分钟）全部携带同一失效 session id，无一自愈。此后所有 MCP 调用持续失败，直到用户手动 `/mcp` 重连。

0.29.0 changelog 的 "Reconnect a dropped MCP server connection automatically when one of its tools is called, and retry the call once" 只覆盖**传输层掉线**；本 case 中 TCP/HTTP 层始终正常——server 返回了结构化的 JSON-RPC 错误响应，是**应用层 session 失效**，不在现有重连逻辑的触发条件内。

session wire 日志原始帧（已裁剪无关字段并脱敏；session id 为 server 端已失效的随机 hex）：

```json
{"jsonrpc": "2.0", "id": 72, "error": {"code": -32600, "message": "Unknown session id '0fbc7f3f46a19394ee69ba83d4a726ab' for 'tools/call'; client should reinitialize"}}
{"jsonrpc": "2.0", "id": 73, "error": {"code": -32600, "message": "Unknown session id '0fbc7f3f46a19394ee69ba83d4a726ab' for 'tools/call'; client should reinitialize"}}
{"jsonrpc": "2.0", "id": 74, "error": {"code": -32600, "message": "Unknown session id '0fbc7f3f46a19394ee69ba83d4a726ab' for 'tools/call'; client should reinitialize"}}
{"jsonrpc": "2.0", "id": 75, "error": {"code": -32600, "message": "Unknown session id '0fbc7f3f46a19394ee69ba83d4a726ab' for 'tools/call'; client should reinitialize"}}
{"jsonrpc": "2.0", "id": 76, "error": {"code": -32600, "message": "Unknown session id '0fbc7f3f46a19394ee69ba83d4a726ab' for 'tools/call'; client should reinitialize"}}
{"jsonrpc": "2.0", "id": 77, "error": {"code": -32600, "message": "Unknown session id '0fbc7f3f46a19394ee69ba83d4a726ab' for 'tools/call'; client should reinitialize"}}
```

对应本地时间戳（epoch ms）：`1785336079817` → `1785337347072`，跨度约 21 分钟。client 侧工具报错原文：

```text
Tool "mcp__unreal-mcp__call_tool" failed: Streamable HTTP error: Error POSTing to endpoint: {
        "jsonrpc": "2.0",
        "id": 72,
        "error":
        {
  
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
### What version of Kimi Code is running?

0.2.0

### Which open platform/subscription were you using?

kimi-coding

### Which model were you using?

kimi-for-coding 

### What platform is your computer?

Darwin 24.6.0 arm64 arm

### What issue are you seeing?

全新安装，启动失败；
```text
➜  artemis git:(master) ✗ curl -fsSL https://code.kimi.com/kimi-code/install.sh | bash
==> Detected target: darwin-arm64
==> Resolving latest version from https://code.kimi.com/kimi-code/latest
==> Latest version: 0.2.0
==> Fetching manifest https://code.kimi.com/kimi-code/0.2.0/manifest.json
==> Downloading https://code.kimi.com/kimi-code/0.2.0/kimi-code-darwin-arm64
######################################################################## 100.0%##O#-#                                                                         
==> Verifying checksum
==> Installed to /Users/ijkzen/.kimi-code/bin/kimi
==> /Users/ijkzen/.kimi-code/bin already in PATH
==> Done. Run: kimi --version
➜  artemis git:(master) ✗ kimi --version                              
0.2.0
➜  artemis git:(master) ✗ kimi           
 …/Projects/RUST-Project/artemis  master [+283 -101]                                                                                                                                                                                @: mention files | shift+tab: plan mode
                                                                                                                                                                                                                                                              context: 0.0%node:internal/child_process:441
    throw new ErrnoException(err, 'spawn');
          ^

Error: spawn ENOTDIR
    at ChildProcess.spawn (node:internal/child_process:441:11)
    at spawn (node:child_process:796:9)
    at execFile (node:child_process:349:17)
    at /Users/runner/work/kimi-code/kimi-code/apps/kimi-code/dist-native/intermediates/main.cjs:200069:35
    at new Promise (<anonymous>)
    at readPullRequest (/Users/runner/work/kimi-code/kimi-code/apps/kimi-code/dist-native/intermediates/main.cjs:200068:9)
    at refreshPullRequestIfNeeded (/Users/runner/work/kimi-code
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
### What version of Kimi Code is running?

`kimi --version`: `0.27.0`

### What platform is your computer?

Windows 11 x64, VSCode 1.129.0, terminal kept in the **editor area** (a common layout).

### What issue are you seeing?

There is no way to tell at a glance whether Kimi Code is working when the terminal lives somewhere that can't render `OSC 9;4` progress. Concrete case: VSCode editor-area terminal tabs never render `OSC 9;4` (only panel-area tabs do — microsoft/vscode#240117; related: #1884 for the allow-list gap). Inside the TUI the spinner is visible, but the moment you switch to another tab you lose all "is it still working?" signal.

### Proposed solution

Mirror the working state into the **terminal title** (`OSC 0`) while a turn is running, e.g. `<session-label> ⠋` with the braille frame animated on a timer, restored to `<session-label>` when the turn ends. Terminal titles are plain text and render everywhere — panel tabs, editor-area tabs, tmux, web terminals (xterm.js `onTitleChange`), Windows Terminal.

Prior art: Claude Code writes its working state into the terminal title the same way; this is how its users get working-state in tabs.

Ideally behind a config flag (e.g. `tui.toml`), default on or off per maintainer taste.

### Reference implementation (local patch, works today)

I patched the installed `dist/main.mjs` as a stopgap. In the TUI terminal class:

```ts
setTitle(title) {
  title = title && title.length > 10 ? title.slice(0, 10) + "…" : title;
  this._tabStatusTitle = title;
  process.stdout.write(`\x1b]0;${title}\x07`);
}

setProgress(active) {
  if (this._tabStatusTimer) { clearInterval(this._tabStatusTimer); this._tabStatusTimer = undefined; }
  const base = this._tabStatusTitle || "kimi";
  if (active) {
    const frames = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏".split("");
    let i = 0;
    this._tabStatusTimer = setInterval(() => {
      i = (i + 1) % frames.length;
      process.stdout.write(`\x1b]0;${base} ${frames[i]}\x07`);
    }, 200);
    this._tabStatusTimer.unref?.();
  } else {
    process.stdout.write(`\x1b]0;${base}\x07`);
  }
  // ...original progress-sequence logic unchanged
}
```

Effect in VSCode editor-area tabs: idle `node · 修复登录bu…`, wo
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
## Summary

Running the full test suite on Windows (with a correctly-configured Git Bash) produces a large number of failures that are **all environment / cross-platform-portability issues, not product logic bugs**. On a clean checkout I get:

```
Test Files  44 failed | 339 passed | 5 skipped (388)
     Tests  143 failed | 4830 passed | 42 skipped | 2 todo (5017)
```

The same tree is green on Linux CI. I've categorized every failure cluster below with `file:line` evidence so the maintainers can decide whether/how to support running the suite on Windows. I'm raising an issue first (per CONTRIBUTING) rather than sending a broad unsolicited PR, because several of these require an intent decision (e.g. should tool paths be native or normalized?).

## Environment

- OS: Windows 10 Pro (x64)
- Node: v24.16.0, pnpm 10.33.0
- Shell: Git Bash, set via `KIMI_SHELL_PATH`
- Repro: `pnpm install` → `pnpm test`

## Failure categories

### 1. Git Bash path detection (already being addressed)
Without `KIMI_SHELL_PATH`, ~205 tests abort with `shell.git_bash_not_found` because bash lives at `…\Git\usr\bin\bash.exe` while detection probed `…\Git\mingw64\bin\bash.exe`. This is already handled by **#145** (`packages/kaos/src/environment.ts`) — listing it only for completeness.

### 2. Path separator `/` vs `\` (cuts both ways → test-only)
- `packages/agent-core/test/skill/scanner.test.ts:58` — scanner returns forward-slash paths (`C:/Users/.../.kimi-code/skills`); the test expects native `\` via `path.join` + `realpath`.
- `apps/kimi-code/test/scripts/native/paths.test.ts:52` — the opposite: `nativeIntermediatesDir()` returns native `\` paths; the test hardcodes `${appRoot}/dist-native/intermediates` with `/`.

Because the mismatch goes in both directions, this is test-portability noise rather than a single product bug — but it does mean tests bake in a separator convention.

### 3. `path.resolve` assumes a POSIX absolute input
- `packages/migration-legacy/test/sessions/workdir-bucket.test.ts:33` hashes the raw literal `'/Users/me/Developer/proj'`, but `computeWorkdirBucket` (`packages/migration-legacy/src/sessions/workdir-bucket.ts:26`) runs `resolve()` first (correctly, and inte
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
### What version of Kimi Code is running?

0.15.0

### Which open platform/subscription were you using?

subscription

### Which model were you using?

kimi-for-coding

### What platform is your computer?

macOS (Apple Silicon)

### What issue are you seeing?

When using `kimi acp` mode, all authorization/permission prompts return only a generic `"bash"` string instead of the actual command that needs to be authorized. Because no concrete command is provided, **ACP clients cannot implement automatic authorization** — there is simply nothing to evaluate against allow-lists, deny-lists, or any policy rules.

In a normal terminal session, the CLI displays the full command and lets the user approve or reject it interactively. In ACP mode, the response is reduced to just `"bash"` with no command content. This means:

- The client cannot determine what action is being requested
- The client cannot apply any authorization policy (allow/deny rules)
- The client cannot auto-approve safe commands or auto-deny dangerous ones
- The client cannot even present the command to a human for manual review

### What steps can reproduce the bug?

Using [agentline](https://github.com/seven-tt/agentline) as the ACP client:

1. Start `kimi acp` and connect agentline as the ACP client
2. Send a message in the IM platform (e.g. "create a file named test.txt")
3. agentline forwards the request to `kimi acp` via ACP protocol
4. kimi acp processes the request and triggers an authorization prompt (e.g. to write a file or execute a shell command)
5. The ACP authorization response is received by agentline — but it contains only `"bash"`, **not the actual command**
6. agentline attempts to apply its authorization policy:
   - Cannot match against allow-list → **auto-approve fails**
   - Cannot match against deny-list → **auto-deny fails**
   - Cannot display the command to the user in IM → **manual approval fails**
7. The operation is stuck — no authorization decision can be made, and the agent cannot proceed

**Result**: Every operation that requires authorization is permanently blocked. The ACP client cannot perform automatic authorization because there is no concrete command to evaluate.

##
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
**Describe the bug**
Every time I install Kimi Code using pip:



it installs an old version of the CLI. To actually get the latest version (e.g., 0.20.3), I have to re-run the installer from the official download URL:

==> Detected target: linux-x64
==> Resolving latest version from https://code.kimi.com/kimi-code/latest
==> Latest version: 0.20.3
==> Fetching manifest https://code.kimi.com/kimi-code/binaries/0.20.3/manifest.json
==> Downloading https://code.kimi.com/kimi-code/binaries/0.20.3/kimi-code-linux-x64
==> Verifying checksum
==> Backed up existing kimi to /root/.kimi-code/bin/kimi.bak
==> Installed to /root/.kimi-code/bin/kimi
==> /root/.kimi-code/bin already configured in /root/.bashrc
==> Done. Run: kimi --version
==> If `kimi` is not found, restart your shell or run: source /root/.bashrc

This is confusing because the PyPI package appears out of sync with the latest release distributed by the install script.

**Expected behavior**
Requirement already satisfied: kimi-code in /usr/local/lib/python3.12/dist-packages (1.48.0)
Requirement already satisfied: kimi-cli==1.48.0 in /usr/local/lib/python3.12/dist-packages (from kimi-code) (1.48.0)
Requirement already satisfied: agent-client-protocol==0.8.0 in /usr/local/lib/python3.12/dist-packages (from kimi-cli==1.48.0->kimi-code) (0.8.0)
Requirement already satisfied: aiofiles<26.0,>=24.0 in /usr/local/lib/python3.12/dist-packages (from kimi-cli==1.48.0->kimi-code) (25.1.0)
Requirement already satisfied: aiohttp==3.13.3 in /usr/local/lib/python3.12/dist-packages (from kimi-cli==1.48.0->kimi-code) (3.13.3)
Requirement already satisfied: typer==0.21.1 in /usr/local/lib/python3.12/dist-packages (from kimi-cli==1.48.0->kimi-code) (0.21.1)
Requirement already satisfied: kosong==0.54.0 in /usr/local/lib/python3.12/dist-packages (from kosong[contrib]==0.54.0->kimi-cli==1.48.0->kimi-code) (0.54.0)
Requirement already satisfied: loguru<0.8,>=0.6.0 in /usr/local/lib/python3.12/dist-packages (from kimi-cli==1.48.0->kimi-code) (0.7.3)
Requirement already satisfied: prompt-toolkit==3.0.52 in /usr/local/lib/python3.12/dist-packages (from kimi-cli==1.48.0->kimi-code) (3.0.52)
Requirement already satisfied: pillow==12.2.0
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
## Motivation

The ACP adapter currently exposes `/compact` as a built-in slash command, but two adjacent session operations have no ACP surface:

- **Undo** — `Session.undoHistory(count)` exists in the node SDK (the TUI's `/undo` drives it), but ACP clients cannot reach it. Hosts embedding `kimi acp` (IDEs, chat bots) have no way to roll back turns.
- **Fork / btw** — `KimiHarness.forkSession` exists in the node SDK, but ACP clients cannot create an ephemeral fork to run a side conversation that cannot pollute the main session's context.

## Proposal

1. **`/undo [count]` built-in slash command** (same shape as `/compact`): parse an optional positive-integer count, refuse while a turn is running (the kernel's `context.undo` has no active-turn guard, so an undo landing mid-turn would splice the history the in-flight turn is still reading), and call `Session.undoHistory(count)`.
2. **`kimi/session/fork` extension method** `{ sessionId } -> { sessionId }`: fork a session into an ephemeral copy and register it as a first-class ACP session the client can `session/prompt` with the full streaming/tool surface. Kernel-side `SESSION_FORK_ACTIVE_TURN` rejection is preserved.
3. **`kimi/session/close` extension method** `{ sessionId, archive? }`: close and drop a session from the adapter; with `archive: true` also archive the on-disk directory (the fork cleanup path). Requires an `archiveSession` passthrough in the node SDK (agent-core already implements it).

Extension methods live in the `kimi/*` namespace so they cannot collide with future ACP spec methods.

## Known limitation

ACP-supplied `mcpServers` are not carried into forks: `resumeSession` rebuilds MCP from the on-disk config only. Carrying caller-supplied MCP servers through fork is a follow-up.
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
### What version of Kimi Code is running?

0.27.0 (self-contained binary at `~/.kimi-code/bin/kimi`, bundled Node.js v24.15.0; binary installed 2026-07-18)

### Which open platform/subscription were you using?

Kimi Code subscription (`managed:kimi-code`, OAuth)

### Which model were you using?

`kimi-code/k3`, thinking effort `max`

### What platform is your computer?

Linux x86_64 (Arch Linux, kernel 7.0.14-zen), 23 GiB RAM. Running in web server mode (`kimi server`, bound to 0.0.0.0).

### What issue are you seeing?

The kimi web server process dies abruptly with **SIGSEGV** — 6 crashes in ~26 hours, all with the same signature: the faulting threads are always inside **V8 garbage-collection marking**.

Crash timeline (times UTC+8, all SIGSEGV, coredumps preserved):

| # | Time | Signal |
|---|------|--------|
| 1 | 2026-07-19 12:04:03 | SIGSEGV |
| 2 | 2026-07-20 11:21:08 | SIGSEGV |
| 3 | 2026-07-20 11:22:18 | SIGSEGV |
| 4 | 2026-07-20 11:22:55 | SIGSEGV |
| 5 | 2026-07-20 13:43:03 | SIGSEGV |
| 6 | 2026-07-20 13:49:18 | SIGSEGV |

Stack traces (via `coredumpctl`, crashes #5 and #6):

Main thread — incremental marking:
```
#0  v8::internal::MarkingVisitorBase<v8::internal::MainMarkingVisitor>::ProcessStrongHeapObject<v8::internal::FullHeapObjectSlot>
#1  v8::internal::BodyDescriptorBase::IteratePointers<v8::internal::MainMarkingVisitor>
#2  v8::internal::MarkCompactCollector::ProcessMarkingWorklist<...>
#3  v8::internal::IncrementalMarking::Step
#4  v8::internal::IncrementalMarking::AdvanceAndFinalizeIfComplete
#5  v8::internal::IncrementalMarkingJob::Task::RunInternal
#6  node::PerIsolatePlatformData::RunForegroundTask
#7  node::PerIsolatePlatformData::FlushForegroundTasksInternal
#8  uv__async_io → uv__io_poll → uv_run
#9  node::SpinEventLoopInternal → node::NodeMainInstance::Run → node::Start
```

V8Worker threads (several per crash) — concurrent marking:
```
#0  v8::internal::MarkingVisitorBase<v8::internal::ConcurrentMarkingVisitor>::ProcessStrongHeapObject<v8::internal::FullHeapObjectSlot>
    (frame #0 varies: also VisitMapPointer and MarkBit::Set)
#1  v8::internal::BodyDescriptorBase::IteratePointers<v8::internal::ConcurrentMarkingVisitor>
#2  v8::i
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
## Summary

When kimi-code is driven as an ACP agent (`kimi acp`), turns that the agent starts **on its own** — e.g. resuming after a background subagent / background bash task completes, or a cron/scheduled reminder fires — never emit any `session/update` notifications. The client only receives traffic for these turns once the user sends a new prompt, and even then the missed content is lost (not buffered). From the client's perspective the agent goes silently idle, does invisible work, and the results never appear.

## Environment

- kimi-code 0.29.0 (`~/.kimi-code/bin/kimi`), macOS
- ACP client: a desktop app hosting `kimi acp` over stdio (SergeCode, a T3-Code-style host)

## Reproduction

1. Over ACP, start a session and ask the agent to delegate work to background subagents (the `Agent` tool with `run_in_background`, or background Bash tasks).
2. Wait for the background tasks to complete. The kimi runtime injects the completion notification into the session and the agent **autonomously starts a new turn** (reads the task output, posts a summary) — with no `session/prompt` from the client.
3. Observe the ACP wire during that window.

**Expected:** the agent-initiated turn streams `session/update` notifications as it happens — `user_message_chunk` for the injected completion notification, then `agent_thought_chunk` / `agent_message_chunk` / `tool_call*` for the turn's work. ACP permits agent→client notifications outside the prompt lifecycle.

**Actual:** zero `session/update` notifications while no prompt is in flight. The only agent→client traffic is `session/request_permission` for tool calls made *by those autonomous turns* — which proves the turns execute but their content is suppressed. The turns' text/tool activity is also **not** flushed when the next `session/prompt` arrives; it is never emitted at all.

## Evidence (production ACP session log)

A real session where 3 background subagents + 2 background validation commands completed while the client was idle (5 autonomous turns between 18:24–18:31):

| window | `session/update` from autonomous turns | other agent→client traffic |
|---|---|---|
| 18:24–18:28 (3 subagent-completion turns) | **0** | 12 ×
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
### Summary

`kimi acp` currently has no way for an ACP client to inject a message into a running turn, even though Kimi Code already implements steering everywhere else. As a result, ACP hosts can only queue a follow-up and wait for the turn to finish, while the TUI can steer it immediately with `Ctrl-S`.

This is a request to expose the existing capability through the ACP surface, matching the extension method that `claude-agent-acp` and `codex-acp` already ship.

### The capability already exists — only the ACP surface is missing

| | |
| --- | --- |
| Core SDK | `packages/node-sdk/src/session.ts` — `async steer(input: string \| PromptInput)` → `rpc.steer({ sessionId, input })` |
| Official smoke test | `packages/node-sdk/examples/kimi-harness-steer-smoke.ts` — calls `await session.steer(STEER)` while a prompt stream is still running |
| TUI | `docs/en/reference/keyboard.md` — `Ctrl-S`: "Steer: inject the current input directly into the running turn" |
| ACP adapter | `packages/acp-adapter/**` — no reference to steering anywhere; `AcpSession.prompt()` maps straight to `session.prompt()` |

The adapter already holds the same `KimiHarness` / `Session` instance that exposes `steer()`, so this is a thin mapping rather than new functionality.

### Prior art: the wire shape is already established by two other adapters

Both adapters below implement the same extension method, so hosts can support all of them with one code path:

- `@agentclientprotocol/claude-agent-acp` (verified in `0.62.0`)
- `@agentclientprotocol/codex-acp` (verified in `1.1.7`)

**Advertisement** — top-level `_meta` in the `initialize` response:

```json
{ "_meta": { "steering": { "supported": true } } }
```

**Request** — `_session/steering`:

```json
{ "sessionId": "…", "prompt": [ { "type": "text", "text": "…" } ] }
```

**Response**:

```json
{ "outcome": "injected" }
```

`injected` means the prompt joined the turn that is currently running. Both adapters also define a `startedNewTurn` outcome for the case where the target turn had already finished.

### One caveat worth avoiding from the start

In `claude-agent-acp`, the `startedNewTurn` path starts a **detached** turn: it emits `session/u
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
### What feature would you like to see?

## Motivation

Currently, all six skill sources (builtin, user, workspace, plugin, extra, explicit) are unconditionally merged into the skill catalog, and every discovered skill appears regardless of user preference. There is no way to:

- Disable an entire skill source at runtime (e.g. suppress workspace skills in favor of a curated builtin set).
- Hide specific skills by name without removing them from disk.

## Proposed solution

Two new `config.toml` sections consumed by `WorkspaceSkillCatalogService`:

### `[skill_sources]`

Per-source boolean toggles. Setting any key to `false` disables that entire source in the merged catalog. The source is still scanned; only the merge phase skips it.

```toml
[skill_sources]
workspace = false   # hide project-level skills
plugin = false      # hide plugin-contributed skills
```

All six sources default to enabled when the key is absent or the entire section is omitted.

### `exclude_skill_names`

A string array of skill names to exclude from the merged view, compared case-insensitively.

```toml
exclude_skill_names = ["git-commit-message-zh", "map-game-codebase-zh"]
```

Default is `[]` (no exclusion).

## Scope

`agent-core-v2` only — consumed by `WorkspaceSkillCatalogService.remerge()`. Config changes take effect immediately without requiring a restart.

## Branch

Implementation ready at [feat/skill-source-toggles](https://github.com/Vincent-Huang-2000/kimi-code/tree/feat/skill-source-toggles)

### Additional information

_No response_
```
