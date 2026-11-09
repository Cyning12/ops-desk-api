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
      ["#/eng/l0", "工程图谱", "eng"],
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

  // W1：白名单内源文档 → 站内 #/doc 查看器；白名单外保持仓相对外链
  function docHref(path) {
    const hit = (DATA.docs_index || []).find((d) => d.path === path);
    return hit ? `#/doc?path=${encodeURIComponent(path)}` : `../../../${path}`;
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
      <div class="note-box">叙事：主线 = Agent Host；对外演示统一 Agent Host 口径（名实分离：工程钻取层保留真值名）。</div>
      <h2 class="section-title">架构理念</h2>
      <div class="principle-grid">${principles}</div>
    `;
  }

  function scenariosPlaceholderHtml() {
    const sc = (DATA.home_narrative && DATA.home_narrative.scenarios_placeholder) || {};
    const cards = (sc.cards || [])
      .map((c) => {
        if (c.status === "live") {
          return `
        <div class="card">
          <div class="title">${escapeHtml(c.title || "场景")}</div>
          <div class="desc">${escapeHtml(c.desc || "")}</div>
          <span class="badge wave">已落地 · 按波次更新</span>
        </div>`;
        }
        return `
        <div class="card placeholder-card" aria-disabled="true">
          <div class="title">${escapeHtml(c.title || "场景占位")}</div>
          <div class="desc">${escapeHtml(c.desc || "")}</div>
          <span class="badge na">设想 · 未填充</span>
        </div>`;
      })
      .join("");
    return `
      <section class="panel scenarios-placeholder">
        <h2>${escapeHtml(sc.title || "使用场景（占位）")}</h2>
        <p class="muted">${escapeHtml(sc.summary || "")}</p>
        <div class="card-grid">${cards}</div>
      </section>
    `;
  }

  /** 从 mermaid 源解析 click 指令 → { nodeId: href } */
  function parseMermaidClicks(src) {
    const map = {};
    const re = /^\s*click\s+(\S+)\s+"([^"]+)"/gm;
    let m;
    while ((m = re.exec(src || ""))) {
      map[m[1]] = m[2];
    }
    return map;
  }

  /** 默认 Mermaid 组件：渲染 + 缩放工具栏（后续所有图都走这里） */
  function mermaidPanelHtml(src, hint) {
    const mermaidSrc = (src || "").trim();
    if (!mermaidSrc) return "";
    const clicksJson = escapeHtml(JSON.stringify(parseMermaidClicks(mermaidSrc)));
    return `
      <div class="mermaid-viewer clickable-mermaid" data-mermaid-ready="0" data-zoom="1" data-mz-clicks="${clicksJson}">
        <div class="mermaid-toolbar" role="toolbar" aria-label="图谱缩放">
          <button type="button" class="mz-btn" data-mz="out" title="缩小（滚轮亦可）" aria-label="缩小">−</button>
          <span class="mermaid-zoom-label" data-mz-label>100%</span>
          <button type="button" class="mz-btn" data-mz="in" title="放大" aria-label="放大">+</button>
          <button type="button" class="mz-btn" data-mz="reset" title="重置 100%" aria-label="重置">1:1</button>
          <button type="button" class="mz-btn" data-mz="fit" title="按当前视口宽度适应（非固定比例）" aria-label="适应宽度">适应</button>
          <button type="button" class="mz-btn" data-mz="copy" title="复制 Mermaid 源码" aria-label="复制源码">复制源码</button>
        </div>
        <textarea class="mz-src-store" hidden readonly aria-hidden="true">${escapeHtml(
          mermaidSrc
        )}</textarea>
        <div class="mermaid-viewport" tabindex="0" title="空白处拖拽平移 · 滚轮缩放">
          <div class="mermaid-stage">
            <pre class="mermaid">${escapeHtml(mermaidSrc)}</pre>
          </div>
        </div>
      </div>
      <p class="muted mermaid-hint">${escapeHtml(
        hint || "点击图中节点进入对应模块"
      )} · 滚轮缩放 · 空白处拖拽平移</p>`;
  }

  // ---- 演示面视图过滤（D1 已锁 · 名实分离）----
  // 真值在 DATA / docs/_tech_graph 内不动；此处仅渲染层隐藏或改名，不改业务语义。
  const ENG_DEMO_HIDDEN_FLOWS = new Set(["10_flow_chat", "10_flow_lc_evidence"]);
  const ENG_DEMO_FLOW_LABEL = { "10_flow_lg_rag": "Agent 工作台（SSE 流式运行）" };
  const ENG_L0_DEMO_HIDDEN = new Set([
    "chat_router",
    "chat_flow",
    "lc_evidence_router",
    "lc_evidence_flow",
  ]);
  const ENG_L0_DEMO_LABEL = {
    lg_rag_router: "Agent 工作台 路由",
    lg_rag_flow: "Agent 工作台（SSE 流式运行）",
  };
  const DEMO_TEXT_SCRUB = [
    [/lg[_-]rag/gi, "Agent Host"],
    [/LG RAG/g, "Agent Host"],
    [/LC Evidence/gi, "证据链"],
    [/legacy Chat/gi, "旧版对话"],
  ];
  const demoText = (s) =>
    DEMO_TEXT_SCRUB.reduce((t, [re, to]) => t.replace(re, to), s || "");

  function renderHome() {
    const mermaidBlock =
      mermaidPanelHtml(
        DATA.concept_mermaid,
        "点击图中节点进入 Host 详页 · 节点色 = 落地状态（见图例）"
      ) || `<p class="error">缺 concept_mermaid · 请重新执行 build_site.py</p>`;

    return shell(
      "/",
      `
      <section class="panel home-intro">
        ${homeNarrativeHtml()}
        <p class="home-actions">
          <a href="#/host">打开完整 Host 导览 →</a>
          · <a href="#/eng/l0">工程图谱 →</a>
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
        <p class="muted">工程图谱 → G-L1 flow → G-L2 indexes · 真值 graph.json</p>
        <div class="card-grid">
          <div class="card" data-nav="#/eng/l0">
            <div class="title">工程图谱 · 00_main</div>
            <div class="desc">顶层流程总图 · Mermaid 可点钻取</div>
          </div>
          ${(DATA.graphs || [])
            .filter((g) => g.id !== "00_main" && !ENG_DEMO_HIDDEN_FLOWS.has(g.id))
            .map(
              (g) => `
            <div class="card" data-nav="#/eng/flow/${g.id}">
              <div class="title">${ENG_DEMO_FLOW_LABEL[g.id] || g.id}</div>
              <div class="desc">${demoText(g.title || "")} · ${g.layer || ""}</div>
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

  const MZ_MIN = 0.25;
  const MZ_MAX = 4;
  const MZ_STEP = 0.15;

  /** Mermaid 图真实设计宽（px）：优先 viewBox / 原 maxWidth，勿用被 width:100% 压扁的 clientWidth */
  function mermaidNaturalWidth(svg) {
    if (!svg) return 1;
    const cached = parseFloat(svg.getAttribute("data-mz-natural-w") || "");
    if (cached > 1) return cached;
    const vb = (svg.getAttribute("viewBox") || "").trim().split(/[\s,]+/).map(Number);
    if (vb.length === 4 && vb[2] > 1) return vb[2];
    const maxW = parseFloat(svg.style.maxWidth);
    if (maxW > 1) return maxW;
    try {
      const bb = svg.getBBox();
      if (bb && bb.width > 1) return bb.width;
    } catch (_) {
      /* ignore */
    }
    const attrW = parseFloat(svg.getAttribute("width"));
    if (attrW > 1) return attrW;
    return Math.max(1, svg.getBoundingClientRect().width || 1);
  }

  /** 渲染后把 SVG 固定到自然像素宽，缩放交给 .mermaid-stage transform */
  function normalizeMermaidSvg(viewer) {
    const svg = viewer && viewer.querySelector(".mermaid-stage svg");
    if (!svg) return;
    const w = mermaidNaturalWidth(svg);
    svg.setAttribute("data-mz-natural-w", String(w));
    svg.setAttribute("width", String(w));
    svg.removeAttribute("height");
    svg.style.width = `${w}px`;
    svg.style.maxWidth = "none";
    svg.style.height = "auto";
  }

  function mermaidNodeKey(el) {
    if (!el || !el.closest) return null;
    const node = el.closest("g.node");
    if (!node) return null;
    const idAttr = node.id || "";
    const m = idAttr.match(/flowchart-([\w-]+)-\d+$/);
    return m ? m[1] : null;
  }

  /** 自管节点跳转：不依赖 mermaid 内置 click（易被平移 capture 吞掉） */
  function bindMermaidNodeNav(viewer) {
    if (!viewer || viewer.getAttribute("data-mz-nav") === "1") return;
    let clickMap = {};
    try {
      clickMap = JSON.parse(viewer.getAttribute("data-mz-clicks") || "{}") || {};
    } catch (_) {
      clickMap = {};
    }
    const svg = viewer.querySelector("svg");
    if (!svg || !Object.keys(clickMap).length) {
      viewer.setAttribute("data-mz-nav", "1");
      return;
    }
    svg.addEventListener("click", (ev) => {
      const viewport = viewer.querySelector(".mermaid-viewport");
      if (viewport && viewport.getAttribute("data-suppress-click") === "1") return;
      const key = mermaidNodeKey(ev.target);
      if (!key) return;
      const href = clickMap[key];
      if (!href) return;
      ev.preventDefault();
      ev.stopPropagation();
      if (href.startsWith("#")) location.hash = href;
      else location.assign(href);
    });
    viewer.setAttribute("data-mz-nav", "1");
  }

  function attachMermaidZoom(viewer) {
    if (!viewer || viewer.getAttribute("data-mz-bound") === "1") return;
    const viewport = viewer.querySelector(".mermaid-viewport");
    const stage = viewer.querySelector(".mermaid-stage");
    const label = viewer.querySelector("[data-mz-label]");
    if (!viewport || !stage) return;

    // 挂载时再规范化一次（mermaid.run 刚结束时 SVG 可能尚未带齐 viewBox）
    normalizeMermaidSvg(viewer);

    let scale = 1;
    let tx = 0;
    let ty = 0;
    let dragging = false;
    let moved = false;
    let lastX = 0;
    let lastY = 0;

    const apply = () => {
      stage.style.transform = `translate(${tx}px, ${ty}px) scale(${scale})`;
      viewer.setAttribute("data-zoom", String(scale));
      if (label) label.textContent = `${Math.round(scale * 100)}%`;
    };

    const clamp = (s) => Math.min(MZ_MAX, Math.max(MZ_MIN, s));

    const setScale = (next, originX, originY) => {
      const prev = scale;
      scale = clamp(next);
      if (prev === scale) {
        apply();
        return;
      }
      const rect = viewport.getBoundingClientRect();
      const ox = originX == null ? rect.width / 2 : originX;
      const oy = originY == null ? rect.height / 2 : originY;
      const ratio = scale / prev;
      tx = ox - (ox - tx) * ratio;
      ty = oy - (oy - ty) * ratio;
      apply();
    };

    const fitWidth = () => {
      const svg = stage.querySelector("svg");
      if (!svg) {
        scale = 1;
        tx = 0;
        ty = 0;
        apply();
        return;
      }
      normalizeMermaidSvg(viewer);
      const naturalW = mermaidNaturalWidth(svg);
      const vw = Math.max(1, viewport.clientWidth);
      // 按「当前视口宽 / 图设计宽」算比例；视口 ≥ 图宽 → 100%，不会写死 48%
      const next = (vw - 24) / naturalW;
      scale = clamp(Math.min(1, next));
      tx = 0;
      ty = 0;
      apply();
    };

    const copySource = async (btn) => {
      const store = viewer.querySelector(".mz-src-store");
      const text = store ? store.value : "";
      if (!text) return;
      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          await navigator.clipboard.writeText(text);
        } else {
          store.hidden = false;
          store.select();
          document.execCommand("copy");
          store.hidden = true;
        }
        if (btn) {
          const prev = btn.textContent;
          btn.textContent = "已复制";
          btn.classList.add("is-ok");
          setTimeout(() => {
            btn.textContent = prev;
            btn.classList.remove("is-ok");
          }, 1200);
        }
      } catch (_) {
        if (btn) btn.textContent = "复制失败";
      }
    };

    viewer.querySelectorAll("[data-mz]").forEach((btn) => {
      btn.addEventListener("click", (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        const act = btn.getAttribute("data-mz");
        if (act === "in") setScale(scale + MZ_STEP);
        else if (act === "out") setScale(scale - MZ_STEP);
        else if (act === "reset") {
          scale = 1;
          tx = 0;
          ty = 0;
          apply();
        } else if (act === "fit") fitWidth();
        else if (act === "copy") void copySource(btn);
      });
    });

    viewport.addEventListener(
      "wheel",
      (ev) => {
        ev.preventDefault();
        const rect = viewport.getBoundingClientRect();
        const ox = ev.clientX - rect.left;
        const oy = ev.clientY - rect.top;
        const delta = ev.deltaY > 0 ? -MZ_STEP : MZ_STEP;
        setScale(scale + delta, ox, oy);
      },
      { passive: false }
    );

    // 仅空白处平移；点在 g.node 上绝不 capture，否则吞掉模块跳转
    viewport.addEventListener("pointerdown", (ev) => {
      if (ev.button !== 0) return;
      if (mermaidNodeKey(ev.target)) return;
      dragging = true;
      moved = false;
      lastX = ev.clientX;
      lastY = ev.clientY;
      viewport.classList.add("is-panning");
      try {
        viewport.setPointerCapture(ev.pointerId);
      } catch (_) {
        /* ignore */
      }
    });
    viewport.addEventListener("pointermove", (ev) => {
      if (!dragging) return;
      const dx = ev.clientX - lastX;
      const dy = ev.clientY - lastY;
      if (Math.abs(dx) + Math.abs(dy) > 3) moved = true;
      lastX = ev.clientX;
      lastY = ev.clientY;
      tx += dx;
      ty += dy;
      apply();
    });
    const endPan = (ev) => {
      if (!dragging) return;
      dragging = false;
      viewport.classList.remove("is-panning");
      try {
        if (ev && ev.pointerId != null) viewport.releasePointerCapture(ev.pointerId);
      } catch (_) {
        /* ignore */
      }
      if (moved) {
        viewport.setAttribute("data-suppress-click", "1");
        setTimeout(() => viewport.removeAttribute("data-suppress-click"), 0);
      }
    };
    viewport.addEventListener("pointerup", endPan);
    viewport.addEventListener("pointercancel", endPan);

    apply();
    viewer.setAttribute("data-mz-bound", "1");
  }

  async function mountMermaid(root) {
    const boxes = [...root.querySelectorAll(".mermaid-viewer, .clickable-mermaid")];
    if (!boxes.length) return;
    if (!window.mermaid) {
      boxes.forEach((box) => {
        if (box.getAttribute("data-mermaid-ready") === "1") return;
        box.insertAdjacentHTML(
          "beforeend",
          `<p class="error">mermaid CDN 未加载，备用列表仍可用</p>`
        );
      });
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
    for (const box of boxes) {
      if (box.getAttribute("data-mermaid-ready") === "1") {
        attachMermaidZoom(box);
        bindMermaidNodeNav(box);
        continue;
      }
      const nodes = box.querySelectorAll(".mermaid-stage .mermaid");
      if (!nodes.length) continue;
      try {
        await window.mermaid.run({ nodes: [...nodes] });
        box.setAttribute("data-mermaid-ready", "1");
        // 等一帧，确保 SVG viewBox / maxWidth 已写入再量宽
        await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
        normalizeMermaidSvg(box);
        attachMermaidZoom(box);
        bindMermaidNodeNav(box);
      } catch (err) {
        box.insertAdjacentHTML(
          "beforeend",
          `<p class="error">mermaid 渲染失败：${escapeHtml(err.message || err)}</p>`
        );
      }
    }
  }

  function engL0NodeHref(nodeId) {
    const id = nodeId || "";
    if (id === "lg_rag_flow" || id === "lg_rag_router") return "#/eng/flow/10_flow_lg_rag";
    if (id === "chat_flow" || id === "chat_router") return "#/eng/flow/10_flow_chat";
    if (id === "lc_evidence_flow" || id === "lc_evidence_router")
      return "#/eng/flow/10_flow_lc_evidence";
    if (id === "auth") return "#/eng/flow/10_flow_auth";
    if (id === "admin_sync") return "#/eng/flow/11_flow_sync_to_chat";
    if (id === "llm") return "#/eng/module/llm";
    if (id === "db") return "#/eng/module/db";
    if (id === "struct_doc") return "#/eng/modules";
    const hosts = (DATA.tech_to_host && DATA.tech_to_host[id]) || [];
    if (hosts.length) return `#/host/${hosts[0]}`;
    return null;
  }

  function engL0ChipBackupHtml(nodes) {
    return (nodes || [])
      .filter((n) => !ENG_L0_DEMO_HIDDEN.has(n.id))
      .map((n) => {
        const href = engL0NodeHref(n.id);
        const label = ENG_L0_DEMO_LABEL[n.id] || n.label || "";
        const hosts = (DATA.tech_to_host && DATA.tech_to_host[n.id]) || [];
        const hostHint = hosts.length
          ? ` · Host ${hosts.map((h) => `#${h}`).join(",")}`
          : "";
        if (!href) {
          return `<span class="chip muted"><span class="num">${n.id}</span>${label}${hostHint}</span>`;
        }
        return `<button class="chip" data-nav="${href}"><span class="num">${n.id}</span>${
          label
        }${hostHint}</button>`;
      })
      .join("");
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
              <div class="desc">${(m.display && m.display.one_liner) || m.one_liner || m.future_gap || "—"}</div>
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
    // 对照展示走 display 演示口径（build 生成）；真值字段仅供反向索引/工程钻取层
    const disp = m.display || {};
    const techLinks = (disp.tech_chips || [])
      .map((c) => `<a href="${c.href}">${c.label}</a>`)
      .join(" · ");
    const flowLinks = (disp.flow_chips || [])
      .map((c) => `<a href="${c.href}">${c.label}</a>`)
      .join(" · ");
    const srcLinks = (m.sources || [])
      .map((s) => {
        const hit = (DATA.docs_index || []).find((d) => d.path === s);
        const href = docHref(s);
        return hit
          ? `<a href="${href}">${s}</a> <span class="muted">(站内查看)</span>`
          : `<a href="${href}" target="_blank" rel="noopener">${s}</a>`;
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
        <p>${disp.one_liner || m.one_liner || "（源 MD 未抽到 · 见源文档）"}</p>
        <h2>实现细节</h2>
        <dl class="kv">
          <dt>代码落点</dt><dd class="mono">${disp.code_paths || (disp.paths || []).join(", ") || "—"}</dd>
          <dt>tech 模块</dt><dd>${techLinks || "—"}</dd>
          <dt>G-L1 flow</dt><dd>${flowLinks || "—"}</dd>
          <dt>残余缺口</dt><dd>${disp.gap || m.gap || m.future_gap || "—"}</dd>
          <dt>规划波次</dt><dd>${
            m.future_wave
              ? `<a href="#/wave/${m.future_wave}">${m.future_wave}</a> · ${m.future_gap || ""}`
              : "—"
          }</dd>
        </dl>
        <h2>源文档（真值 · 勿在本页改结论）</h2>
        <div class="sources">${srcLinks || "—"}</div>
        ${(disp.paths || m.paths || [])
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
    const mermaidBlock =
      mermaidPanelHtml(
        DATA.eng_l0_mermaid,
        "点击图中高亮节点进入对应 flow / 模块 · 与首页同款 Mermaid 交互"
      ) || `<p class="error">缺 eng_l0_mermaid · 请重新执行 build_site.py</p>`;
    return shell(
      "eng",
      `
      <section class="panel" style="grid-column:1/-1">
        <h1>工程图谱 · ${g.title || "00_main"}</h1>
        <p class="muted">${g.source_yaml_path || ""} · 真值 tech_graph · Mermaid 可点钻取</p>
        ${mermaidBlock}
        <details class="chip-backup">
          <summary>节点列表（备用 · chip）</summary>
          <div class="chip-row">${engL0ChipBackupHtml(nodes)}</div>
        </details>
        <details class="chip-backup">
          <summary>边列表（${(g.edges || []).length}）</summary>
          <ul class="edge-list muted">
            ${(g.edges || [])
              .filter(
                (e) =>
                  !ENG_L0_DEMO_HIDDEN.has(e.from || e.source) &&
                  !ENG_L0_DEMO_HIDDEN.has(e.to || e.target)
              )
              .slice(0, 40)
              .map((e) => {
                const from =
                  ENG_L0_DEMO_LABEL[e.from || e.source] || e.from || e.source;
                const to = ENG_L0_DEMO_LABEL[e.to || e.target] || e.to || e.target;
                return `<li class="mono">${from} → ${to}${
                  e.label ? " · " + e.label : ""
                }</li>`;
              })
              .join("")}
          </ul>
        </details>
        <p style="margin-top:1rem">
          <a href="#/eng/modules">一级模块表 →</a>
          · <a href="#/eng/l2">G-L2 索引 →</a>
        </p>
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
        <p><a href="#/eng/l0">← 工程图谱</a></p>
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

  // W1 源文档查看器：只渲染 build 白名单拷入 dist/docs/ 的 MD；mermaid 代码块就地渲染。
  async function renderDoc(root, params) {
    const path = params.path || "";
    const docs = DATA.docs_index || [];
    const back = '<p><a href="#/doc">← 源文档索引</a></p>';
    if (!path) {
      const list = docs
        .map((d) => '<li><a href="#/doc?path=' + encodeURIComponent(d.path) + '">' + escapeHtml(d.path) + "</a></li>")
        .join("");
      root.innerHTML = shell(
        "eng",
        '<section class="panel" style="grid-column:1/-1">' + back +
        '<h1>源文档（W1 白名单）</h1><p class="muted">全文复制自白名单路径进 dist；真值仍在仓内源文件，本页只读。</p>' +
        '<ul class="doclist">' + list + "</ul></section>"
      );
      return;
    }
    const hit = docs.find((d) => d.path === path);
    if (!hit) {
      const isReferenced = (DATA.host_modules || []).some((m) => (m.sources || []).includes(path));
      const reason = isReferenced
        ? "该路径被源链引用，但未进入 W1 dist 白名单，不提供查看。"
        : "该路径不在 W1 白名单内，不进入 dist、不提供查看。";
      root.innerHTML = shell(
        "eng",
        '<section class="panel" style="grid-column:1/-1">' + back +
        '<h1>拒绝</h1><p class="error">' + reason + "</p>" +
        '<p class="mono">' + escapeHtml(path) + "</p></section>"
      );
      return;
    }
    root.innerHTML = shell(
      "eng",
      '<section class="panel" style="grid-column:1/-1">' + back +
      '<h1 class="mono" style="font-size:0.95rem">' + escapeHtml(path) + '</h1><p class="muted">加载中…</p></section>'
    );
    try {
      const res = await fetch("./" + hit.dist);
      if (!res.ok) throw new Error("HTTP " + res.status);
      const text = await res.text();
      if (window.marked && !window.marked._docGfmSet) {
        try {
          marked.use({ gfm: true });
          window.marked._docGfmSet = true;
        } catch (_) {}
      }
      const body = window.marked ? marked.parse(text) : "<pre>" + escapeHtml(text) + "</pre>";
      root.innerHTML = shell(
        "eng",
        '<section class="panel" style="grid-column:1/-1">' + back +
        '<h1 class="mono" style="font-size:0.95rem">' + escapeHtml(path) + '</h1><div class="md">' + body + "</div></section>"
      );
      root.querySelectorAll("code.language-mermaid").forEach((code) => {
        const src = code.textContent;
        const pre = code.closest("pre");
        const wrapper = document.createElement("div");
        wrapper.className = "mermaid-viewer clickable-mermaid doc-inline-mermaid";
        wrapper.setAttribute("data-mermaid-ready", "0");
        wrapper.setAttribute("data-zoom", "1");
        wrapper.innerHTML =
          '<div class="mermaid-viewport" tabindex="0" title="空白处拖拽平移 · 滚轮缩放">' +
          '<div class="mermaid-stage"><div class="mermaid">' + escapeHtml(src) + "</div></div></div>";
        pre.replaceWith(wrapper);
      });
      await mountMermaid(root);
    } catch (err) {
      root.innerHTML = shell(
        "eng",
        '<section class="panel" style="grid-column:1/-1">' + back +
        '<h1 class="mono" style="font-size:0.95rem">' + escapeHtml(path) + '</h1><p class="error">加载失败：' + escapeHtml(String(err.message || err)) + "</p></section>"
      );
    }
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
    else if (parts[0] === "doc") {
      void renderDoc(root, params);
      return;
    }
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
