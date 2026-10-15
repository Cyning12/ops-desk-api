/* Arch Browser · hash 路由 · 零框架 */
(() => {
  const $ = (sel, el = document) => el.querySelector(sel);
  const statusLabel = (s) => {
    if (!s) return "未知";
    if (s === "不适用" || s.includes("不适用")) return "暂未排期";
    return s;
  };
  const statusClass = (s) => {
    const label = statusLabel(s);
    if (!label) return "na";
    if (label.includes("已落地")) return "ok";
    if (label.includes("部分")) return "partial";
    if (label.includes("缺失")) return "missing";
    if (label.includes("暂未排期") || label.includes("不适用")) return "na";
    return "na";
  };

  let DATA = null;

  async function loadData() {
    const res = await fetch("./site-data.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`site-data.json HTTP ${res.status}`);
    DATA = await res.json();
  }

  function parseRoute() {
    const raw = (location.hash || "#/").replace(/^#/, "") || "/";
    const [path, qs] = raw.split("?");
    const parts = path.split("/").filter(Boolean);
    const params = Object.fromEntries(new URLSearchParams(qs || ""));
    return { parts, params, path: "/" + parts.join("/") };
  }

  function navHtml(active) {
    const items = [
      ["#/", "首页", "/"],
      ["#/host", "Host 概念", "host"],
      ["#/eng/l0", "工程 G-L0", "eng"],
      ["#/wave", "规划波次", "wave"],
    ];
    return items
      .map(([href, label, key]) => {
        const on =
          key === "/"
            ? active === "/"
            : active.startsWith(key) || (key === "eng" && active.startsWith("eng"));
        return `<a href="${href}" class="${on ? "active" : ""}">${label}</a>`;
      })
      .join("");
  }

  function shell(activeKey, body) {
    const meta = DATA
      ? `<span class="mono">${DATA.freeze_id || "?"}</span> · gen ${DATA.generated_at || ""}`
      : "";
    // 首页概念 mermaid 需全宽，不用 split
    return `
      <header class="topbar">
        <div class="brand">Ops Desk · 架构浏览器</div>
        <nav>${navHtml(activeKey)}</nav>
        <div class="meta">${meta}</div>
      </header>
      <main class="layout">${body}</main>
    `;
  }

  function hostById(id) {
    return DATA.host_modules.find((m) => Number(m.id) === Number(id));
  }

  function graphById(id) {
    return DATA.graphs.find((g) => g.id === id);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function chipBackupHtml() {
    return (DATA.layers || [])
      .map((layer) => {
        const chips = (layer.modules || [])
          .map((id) => {
            const m = hostById(id);
            if (!m) return "";
            return `<button class="chip" data-nav="#/host/${id}"><span class="num">#${id}</span>${m.title}</button>`;
          })
          .join("");
        return `<div class="layer-block"><h3>${layer.title}</h3><div class="chip-row">${chips}</div></div>`;
      })
      .join("");
  }

  function statusLegendHtml() {
    const items = [
      ["ok", "已落地"],
      ["partial", "部分"],
      ["missing", "缺失"],
      ["na", "暂未排期"],
      ["wave", "入口 / 规划"],
    ];
    return `<div class="status-legend" aria-label="状态图例">
      ${items
        .map(
          ([cls, label]) =>
            `<span class="legend-item"><span class="badge ${cls}">${label}</span></span>`
        )
        .join("")}
    </div>`;
  }

  function homeNarrativeHtml() {
    const n = DATA.home_narrative || {};
    const principles = (n.principles || [])
      .map(
        (p) =>
          `<div class="principle">
            <h3>${escapeHtml(p.title || "")}</h3>
            <p>${escapeHtml(p.body || "")}</p>
          </div>`
      )
      .join("");
    return `
      <header class="home-hero">
        <p class="eyebrow">${escapeHtml(n.product_name || "Ops Desk · Agent Host")}</p>
        <h1>${escapeHtml(n.page_title || "架构浏览器")}</h1>
        <p class="tagline">${escapeHtml(n.tagline || "")}</p>
        <p class="one-liner">${escapeHtml(n.one_liner || "")}</p>
      </header>
      <div class="note-box">叙事：主线 = Agent Host；HTTP/freeze 仍为 lg-rag 执行入口（名实分离）。</div>
      <h2 class="section-title">架构理念</h2>
      <div class="principle-grid">${principles}</div>
    `;
  }

  function scenariosPlaceholderHtml() {
    const sc = (DATA.home_narrative && DATA.home_narrative.scenarios_placeholder) || {};
    const cards = (sc.cards || [])
      .map(
        (c) => `
        <div class="card placeholder-card" aria-disabled="true">
          <div class="title">${escapeHtml(c.title || "场景占位")}</div>
          <div class="desc">${escapeHtml(c.desc || "")}</div>
          <span class="badge na">设想 · 未填充</span>
        </div>`
      )
      .join("");
    return `
      <section class="panel scenarios-placeholder">
        <h2>${escapeHtml(sc.title || "使用场景（占位）")}</h2>
        <p class="muted">${escapeHtml(sc.summary || "")}</p>
        <div class="card-grid">${cards}</div>
      </section>
    `;
  }

  function renderHome() {
    const mermaidSrc = (DATA.concept_mermaid || "").trim();
    const mermaidBlock = mermaidSrc
      ? `<div class="mermaid-box concept-mermaid" data-mermaid-ready="0">
           <pre class="mermaid">${escapeHtml(mermaidSrc)}</pre>
         </div>
         <p class="muted mermaid-hint">点击图中节点进入 Host 详页 · 节点色 = 落地状态（见图例）</p>`
      : `<p class="error">缺 concept_mermaid · 请重新执行 build_site.py</p>`;

    return shell(
      "/",
      `
      <section class="panel home-intro">
        ${homeNarrativeHtml()}
        <p class="home-actions">
          <a href="#/host">打开完整 Host 导览 →</a>
          · <a href="#/eng/l0">工程 G-L0 →</a>
        </p>
      </section>
      <section class="panel">
        <h2 class="section-title">概念总图 · 五层 + M01–M34</h2>
        <p class="muted">真值 discussions §1.2 · 可点击 · 颜色对齐落地状态</p>
        ${statusLegendHtml()}
        ${mermaidBlock}
        <details class="chip-backup">
          <summary>模块列表（备用 · chip）</summary>
          ${chipBackupHtml()}
        </details>
      </section>
      ${scenariosPlaceholderHtml()}
      <section class="panel">
        <h2 class="section-title">工程 tech_graph</h2>
        <p class="muted">G-L0 → G-L1 flow → G-L2 indexes · 真值 graph.json</p>
        <div class="card-grid">
          <div class="card" data-nav="#/eng/l0">
            <div class="title">G-L0 · 00_main</div>
            <div class="desc">顶层流程总图 · 可点节点钻取 flow</div>
          </div>
          ${(DATA.graphs || [])
            .filter((g) => g.id !== "00_main")
            .map(
              (g) => `
            <div class="card" data-nav="#/eng/flow/${g.id}">
              <div class="title">${g.id}</div>
              <div class="desc">${g.title || ""} · ${g.layer || ""}</div>
            </div>`
            )
            .join("")}
        </div>
        <p style="margin-top:1rem"><a href="#/eng/modules">一级模块表（01_modules）→</a>
        · <a href="#/eng/l2">G-L2 索引 →</a>
        · <a href="#/wave">规划 N0–N5 →</a></p>
      </section>
    `
    );
  }

  let mermaidInited = false;

  async function mountMermaid(root) {
    const box = root.querySelector(".concept-mermaid");
    if (!box || box.getAttribute("data-mermaid-ready") === "1") return;
    const nodes = box.querySelectorAll("pre.mermaid");
    if (!nodes.length) return;
    if (!window.mermaid) {
      box.insertAdjacentHTML(
        "beforeend",
        `<p class="error">mermaid CDN 未加载，chip 备用列表仍可用</p>`
      );
      return;
    }
    if (!mermaidInited) {
      window.mermaid.initialize({
        startOnLoad: false,
        securityLevel: "loose",
        theme: "dark",
        flowchart: { htmlLabels: true, curve: "basis" },
      });
      mermaidInited = true;
    }
    try {
      await window.mermaid.run({ nodes: [...nodes] });
      box.setAttribute("data-mermaid-ready", "1");
    } catch (err) {
      box.insertAdjacentHTML(
        "beforeend",
        `<p class="error">mermaid 渲染失败：${escapeHtml(err.message || err)}</p>`
      );
    }
  }

  function renderHostList(filterWave) {
    const mods = DATA.host_modules.filter((m) =>
      filterWave ? m.future_wave === filterWave : true
    );
    return shell(
      filterWave ? "wave" : "host",
      `
      <section class="panel" style="grid-column:1/-1">
        <h1>${filterWave ? `规划波次 ${filterWave}` : "Host 模块目录（34）"}</h1>
        <p class="muted">状态色来自对照文；规划波次来自扩展策略 + crosswalk。</p>
        <div class="filters">
          <button data-nav="#/host" class="${!filterWave ? "on" : ""}">全部</button>
          ${(DATA.waves || [])
            .map(
              (w) =>
                `<button data-nav="#/wave/${w.id}" class="${
                  filterWave === w.id ? "on" : ""
                }">${w.id} ${w.title}</button>`
            )
            .join("")}
        </div>
        <div class="card-grid">
          ${mods
            .map(
              (m) => `
            <div class="card" data-nav="#/host/${m.id}">
              <div class="title"><span class="mono">#${m.id}</span> ${m.title}</div>
              <div>
                <span class="badge ${statusClass(m.status)}">${statusLabel(m.status)}</span>
                ${
                  m.future_wave
                    ? `<span class="badge wave">${m.future_wave}</span>`
                    : ""
                }
                ${!m.mapped ? `<span class="badge unmap">未映射工程</span>` : ""}
              </div>
              <div class="desc">${m.one_liner || m.future_gap || "—"}</div>
            </div>`
            )
            .join("")}
        </div>
        ${mods.length ? "" : `<p class="empty">该波次暂无挂接模块。</p>`}
      </section>
    `
    );
  }

  function renderHostDetail(id) {
    const m = hostById(id);
    if (!m) {
      return shell("host", `<section class="panel"><p class="error">未知 Host #${id}</p></section>`);
    }
    const techLinks = (m.tech_modules || [])
      .map((t) => `<a href="#/eng/module/${encodeURIComponent(t)}">${t}</a>`)
      .join(" · ");
    const flowLinks = (m.flows || [])
      .map((f) => `<a href="#/eng/flow/${encodeURIComponent(f)}">${f}</a>`)
      .join(" · ");
    const srcLinks = (m.sources || [])
      .map((s) => {
        // GitHub-ish relative from repo; for local serve from dist, link as repo-relative note
        return `<a href="../../../${s}" target="_blank" rel="noopener">${s}</a>`;
      })
      .join("");

    return shell(
      "host",
      `
      <section class="panel" style="grid-column:1/-1">
        <p><a href="#/host">← Host 目录</a></p>
        <h1>#${m.id} · ${m.title}</h1>
        <div>
          <span class="badge ${statusClass(m.status)}">${statusLabel(m.status)}</span>
          <span class="badge">${m.layer}</span>
          ${m.future_wave ? `<span class="badge wave">${m.future_wave}</span>` : ""}
          ${!m.mapped ? `<span class="badge unmap">概念≠工程 / 未映射</span>` : ""}
        </div>
        <h2>一句话</h2>
        <p>${m.one_liner || "（源 MD 未抽到 · 见源文档）"}</p>
        <h2>实现细节</h2>
        <dl class="kv">
          <dt>代码落点</dt><dd class="mono">${m.code_paths || (m.paths || []).join(", ") || "—"}</dd>
          <dt>tech 模块</dt><dd>${techLinks || "—"}</dd>
          <dt>G-L1 flow</dt><dd>${flowLinks || "—"}</dd>
          <dt>残余缺口</dt><dd>${m.gap || m.future_gap || "—"}</dd>
          <dt>规划波次</dt><dd>${
            m.future_wave
              ? `<a href="#/wave/${m.future_wave}">${m.future_wave}</a> · ${m.future_gap || ""}`
              : "—"
          }</dd>
        </dl>
        <h2>源文档（真值 · 勿在本页改结论）</h2>
        <div class="sources">${srcLinks || "—"}</div>
        ${(m.paths || [])
          .filter((p) => p.startsWith("app/"))
          .map(
            (p) =>
              `<p class="muted">G-L2 捷径：<a href="#/eng/l2?path=${encodeURIComponent(
                p
              )}">${p}</a></p>`
          )
          .join("")}
      </section>
    `
    );
  }

  function renderEngL0() {
    const g = graphById("00_main");
    if (!g) {
      return shell("eng", `<section class="panel"><p class="error">缺 00_main</p></section>`);
    }
    const nodes = g.nodes || [];
    return shell(
      "eng",
      `
      <section class="panel" style="grid-column:1/-1">
        <h1>G-L0 · ${g.title || "00_main"}</h1>
        <p class="muted">${g.source_yaml_path || ""} · 点击节点钻取</p>
        <ul class="node-list">
          ${nodes
            .map((n) => {
              let href = null;
              if (n.id === "lg_rag_flow" || n.id === "lg_rag_router") href = "#/eng/flow/10_flow_lg_rag";
              else if (n.id === "chat_flow" || n.id === "chat_router") href = "#/eng/flow/10_flow_chat";
              else if (n.id === "lc_evidence_flow" || n.id === "lc_evidence_router")
                href = "#/eng/flow/10_flow_lc_evidence";
              else if (n.id === "auth") href = "#/eng/flow/10_flow_auth";
              else if (n.id === "admin_sync") href = "#/eng/flow/11_flow_sync_to_chat";
              else if (n.id === "llm") href = "#/eng/module/llm";
              else if (n.id === "db") href = "#/eng/module/db";
              const hosts = (DATA.tech_to_host && DATA.tech_to_host[n.id]) || [];
              const hostHint = hosts.length
                ? ` · Host ${hosts.map((h) => `#${h}`).join(",")}`
                : "";
              const click = href
                ? `data-nav="${href}"`
                : hosts.length
                  ? `data-nav="#/host/${hosts[0]}"`
                  : "";
              return `<li ${click}><span class="id">${n.id}</span>${n.label || ""}${hostHint}</li>`;
            })
            .join("")}
        </ul>
        <h2>边（${(g.edges || []).length}）</h2>
        <ul class="edge-list muted">
          ${(g.edges || [])
            .slice(0, 40)
            .map(
              (e) =>
                `<li class="mono">${e.from || e.source} → ${e.to || e.target}${
                  e.label ? " · " + e.label : ""
                }</li>`
            )
            .join("")}
        </ul>
      </section>
    `
    );
  }

  function renderFlow(fid) {
    const g = graphById(fid);
    if (!g) {
      return shell("eng", `<section class="panel"><p class="error">未知 flow ${fid}</p></section>`);
    }
    const hostHits = DATA.host_modules.filter((m) => (m.flows || []).includes(fid));
    return shell(
      "eng",
      `
      <section class="panel" style="grid-column:1/-1">
        <p><a href="#/eng/l0">← G-L0</a></p>
        <h1>${g.id}</h1>
        <p>${g.title || ""}</p>
        <p class="muted">${g.layer || ""} · ${g.source_yaml_path || ""}</p>
        ${
          hostHits.length
            ? `<p>映射 Host：${hostHits
                .map((m) => `<a href="#/host/${m.id}">#${m.id} ${m.title}</a>`)
                .join(" · ")}</p>`
            : `<p class="badge unmap">本 flow 暂无 Host crosswalk 挂接</p>`
        }
        <h2>节点</h2>
        <ul class="node-list">
          ${(g.nodes || [])
            .map(
              (n) =>
                `<li><span class="id">${n.id}</span>${n.label || n.kind || ""}</li>`
            )
            .join("")}
        </ul>
        <p><a href="#/eng/l2">查看 G-L2 indexes →</a></p>
      </section>
    `
    );
  }

  function renderEngModule(mid) {
    const row = (DATA.eng_modules || []).find((m) => m.module_id === mid);
    const hosts = (DATA.tech_to_host && DATA.tech_to_host[mid]) || [];
    const hint = (DATA.tech_module_hints && DATA.tech_module_hints[mid]) || {};
    return shell(
      "eng",
      `
      <section class="panel" style="grid-column:1/-1">
        <p><a href="#/eng/modules">← 模块表</a></p>
        <h1>tech module · <span class="mono">${mid}</span></h1>
        ${
          row
            ? `<dl class="kv">
                <dt>名称</dt><dd>${row.name}</dd>
                <dt>路径</dt><dd class="mono">${row.paths_glob}</dd>
                <dt>依赖</dt><dd>${row.deps}</dd>
              </dl>
              <div class="note-box">${(row.note || "").slice(0, 400)}${
                (row.note || "").length > 400 ? "…" : ""
              }</div>`
            : `<p class="badge unmap">01_modules 表未解析到该行</p>`
        }
        <p>${hint.note || ""}</p>
        <p>Host 映射：${
          hosts.length
            ? hosts.map((h) => `<a href="#/host/${h}">#${h}</a>`).join(" · ")
            : "—"
        }</p>
        ${
          hint.primary_flow
            ? `<p>主 flow：<a href="#/eng/flow/${hint.primary_flow}">${hint.primary_flow}</a></p>`
            : ""
        }
        <p><a href="#/eng/l2">G-L2 索引 →</a></p>
      </section>
    `
    );
  }

  function renderEngModules() {
    return shell(
      "eng",
      `
      <section class="panel" style="grid-column:1/-1">
        <h1>G-L1 · 01_modules 一级模块</h1>
        <p class="muted">源 docs/_tech_graph/l1/01_modules.md</p>
        <ul class="node-list">
          ${(DATA.eng_modules || [])
            .map((m) => {
              const hosts = (DATA.tech_to_host && DATA.tech_to_host[m.module_id]) || [];
              return `<li data-nav="#/eng/module/${encodeURIComponent(m.module_id)}">
                <span class="id">${m.module_id}</span>${m.name}
                ${hosts.length ? `<span class="muted"> · Host ${hosts.map((h) => "#" + h).join(",")}</span>` : ""}
              </li>`;
            })
            .join("")}
        </ul>
      </section>
    `
    );
  }

  function renderL2(params) {
    const pathQ = params.path || "";
    const indexes = DATA.l2_indexes || {};
    let hits = [];
    if (pathQ) {
      for (const [name, idx] of Object.entries(indexes)) {
        const bp = idx.by_path || {};
        for (const [p, nodes] of Object.entries(bp)) {
          if (p === pathQ || p.startsWith(pathQ) || pathQ.startsWith(p.replace(/\*\*.*$/, ""))) {
            hits.push({ index: name, path: p, nodes });
          }
        }
      }
    }
    return shell(
      "eng",
      `
      <section class="panel" style="grid-column:1/-1">
        <h1>G-L2 indexes</h1>
        <p class="muted">by_path / by_symbol · 分域文件 · 禁止单文件全仓汇总</p>
        ${
          pathQ
            ? `<div class="note-box">筛选 path=<code>${pathQ}</code> · 命中 ${hits.length}</div>
               <ul class="path-list">${hits
                 .map(
                   (h) => `<li><span class="mono">${h.index}</span> · ${h.path}
                   <div class="muted">${JSON.stringify(h.nodes).slice(0, 200)}</div></li>`
                 )
                 .join("")}</ul>`
            : ""
        }
        <h2>索引文件</h2>
        <ul class="node-list">
          ${Object.entries(indexes)
            .map(([name, idx]) => {
              const n =
                (idx.by_path_count || 0) + (idx.by_symbol_count || 0);
              return `<li>
                <span class="id">${name}</span>
                ${idx.graph_id || ""} · entries≈${n}
                <div class="muted">${idx.file || ""}</div>
                ${
                  idx.by_path
                    ? `<div class="chip-row" style="margin-top:0.4rem">${Object.keys(idx.by_path)
                        .slice(0, 12)
                        .map(
                          (p) =>
                            `<button class="chip" data-nav="#/eng/l2?path=${encodeURIComponent(
                              p
                            )}">${p.split("/").slice(-2).join("/")}</button>`
                        )
                        .join("")}</div>`
                    : ""
                }
              </li>`;
            })
            .join("")}
        </ul>
      </section>
    `
    );
  }

  function renderWaveHome() {
    return shell(
      "wave",
      `
      <section class="panel" style="grid-column:1/-1">
        <h1>规划叠层 · N0–N5</h1>
        <p class="muted">源：扩展策略 · 挂接自 crosswalk.future.wave</p>
        <div class="card-grid">
          ${(DATA.waves || [])
            .map((w) => {
              const count = DATA.host_modules.filter((m) => m.future_wave === w.id).length;
              return `<div class="card" data-nav="#/wave/${w.id}">
                <div class="title">${w.id} · ${w.title}</div>
                <div class="desc">${w.summary} · ${count} 个 Host 模块</div>
              </div>`;
            })
            .join("")}
        </div>
      </section>
    `
    );
  }

  function render() {
    const root = $("#app");
    if (!DATA) {
      root.innerHTML = `<main class="layout"><p class="error">数据未加载</p></main>`;
      return;
    }
    const { parts, params } = parseRoute();
    let html;
    if (parts.length === 0) html = renderHome();
    else if (parts[0] === "host" && parts[1]) html = renderHostDetail(parts[1]);
    else if (parts[0] === "host") html = renderHostList(null);
    else if (parts[0] === "wave" && parts[1]) html = renderHostList(parts[1]);
    else if (parts[0] === "wave") html = renderWaveHome();
    else if (parts[0] === "eng" && parts[1] === "l0") html = renderEngL0();
    else if (parts[0] === "eng" && parts[1] === "flow" && parts[2]) html = renderFlow(parts[2]);
    else if (parts[0] === "eng" && parts[1] === "module" && parts[2])
      html = renderEngModule(decodeURIComponent(parts[2]));
    else if (parts[0] === "eng" && parts[1] === "modules") html = renderEngModules();
    else if (parts[0] === "eng" && parts[1] === "l2") html = renderL2(params);
    else html = renderHome();

    root.innerHTML = html;
    root.querySelectorAll("[data-nav]").forEach((el) => {
      el.addEventListener("click", (ev) => {
        ev.preventDefault();
        location.hash = el.getAttribute("data-nav");
      });
    });
    void mountMermaid(root);
  }

  async function main() {
    const root = $("#app");
    try {
      await loadData();
      render();
      window.addEventListener("hashchange", render);
    } catch (err) {
      root.innerHTML = `<main class="layout"><section class="panel"><p class="error">加载失败：${err.message}</p>
        <p class="muted">请在仓根执行 <code>python3 docs/arch-browser/scripts/build_site.py</code>，
        再于 <code>docs/arch-browser/dist</code> 启动本地静态服务。</p></section></main>`;
    }
  }

  main();
})();
