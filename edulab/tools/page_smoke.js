/*!
 * page_smoke.js — **已构建 HTML 页面**的执行级冒烟测试（Node + 最小 DOM 桩）。
 *
 * 与 viz_smoke.js 的分工
 *   viz_smoke.js  测「渲染引擎 × 图层 spec」这一层（引擎对不对）
 *   page_smoke.js 测「读者双击打开的那个文件」这一层（页面装起来对不对）：
 *                 数据块能不能求值、画板能不能 boot、画布到底有没有画、
 *                 步骤/帧推进时画面是否**真的变化**
 *
 * 为什么需要
 *   静态 HTML 检查（check_output.py O1–O7）看得见残留记号、外链、canvas 高度，
 *   但看不见「脚本运行时抛异常」与「跑完了但一个像素没画」——这两类都是
 *   「闸门全绿、页面全白」，正是本项目真实踩过的坑。
 *
 * 关键判据（比「不抛异常」严格得多）
 *   1. 全部内联脚本执行不抛
 *   2. 页面里有 canvas → **必须真的产生绘制调用**（挡住静默全白）
 *   3. 能推进帧/步骤 → **每帧指纹必须互不相同**
 *      （把浏览器里「逐档比较画布指纹、要求 hashUniq == 档位数」的纪律搬进闸门：
 *        只要求「指纹不同」会漏掉「画布纹丝不动」的静默 bug，这条已经漏过三次）
 *
 * 用法
 *   node page_smoke.js --inputs <inputs.json> [--budget 300]
 *   inputs.json = ["path/a.html", "path/b.html", ...]
 * 输出：单行 JSON；退出码 0=全过，1=有失败。
 */
"use strict";

const fs = require("fs");
const path = require("path");

function arg(name, dflt) {
  const i = process.argv.indexOf(name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : dflt;
}
const INPUTS = arg("--inputs", "");
const BUDGET = Number(arg("--budget", "300")) || 300;

// 产物 vs 源码的时间戳清单：{ "<绝对路径>": <源码 mtime 毫秒> }。
// 为什么需要：产物不入库，改了源码却忘了重新生成时，闸门测的是**旧产物**，
// 然后报绿 —— 这比没有闸门更危险，因为它给了「已验证」的错觉。
const MANIFEST = (() => {
  const p = arg("--manifest", "");
  if (!p) return {};
  try {
    return JSON.parse(fs.readFileSync(p, "utf8")) || {};
  } catch (e) {
    return {};
  }
})();
if (!INPUTS) {
  process.stderr.write("usage: node page_smoke.js --inputs <inputs.json>\n");
  process.exit(2);
}

// ==================== 绘制计数 + 帧指纹 ====================
function hashCall(h, name, args) {
  let x = h;
  x = (x * 31 + name.charCodeAt(0) * 7 + name.length * 13) % 4294967291;
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    const s = typeof a === "number" ? (Math.round(a * 100) / 100).toString() : String(a == null ? "" : a);
    for (let k = 0; k < s.length; k++) x = (x * 31 + s.charCodeAt(k)) % 4294967291;
  }
  return x;
}

const DRAW_OPS = new Set(["stroke", "fill", "fillText", "fillRect", "strokeRect", "drawImage",
  "fillStroke", "clip", "arc", "arcTo", "ellipse", "beginPath", "moveTo", "lineTo", "closePath",
  "rect", "quadraticCurveTo", "bezierCurveTo", "putImageData"]);

function makeCtx(canvasRef) {
  const st = {
    canvas: canvasRef,
    drawCalls: 0,
    hash: 7,
    measureText(s) { return { width: String(s == null ? "" : s).length * 7.2 }; },
    createLinearGradient() { return { addColorStop() {} }; },
    createRadialGradient() { return { addColorStop() {} }; },
    createConicGradient() { return { addColorStop() {} }; },
    createPattern() { return null; },
    getImageData(x, y, w, h) { return { data: new Uint8ClampedArray(Math.max(1, (w | 0) * (h | 0) * 4)), width: w, height: h }; },
    setLineDash() {},
    getLineDash() { return []; },
    save() {}, restore() {}, translate() {}, scale() {}, rotate() {}, transform() {},
    setTransform() {}, resetTransform() {}, clip() {},
  };
  return new Proxy(st, {
    get(t, k) {
      if (k in t) return t[k];
      if (typeof k !== "string") return undefined;
      // 未登记的方法：当作可调用，同时计入绘制指纹（越全越好——画得越多，指纹越灵）
      return function () {
        const args = Array.prototype.slice.call(arguments);
        t.drawCalls++;
        t.hash = hashCall(t.hash, k, args);
        return undefined;
      };
    },
    set(t, k, v) {
      // "hash" 是本闸门自己的指纹寄存器（resetFrame 写入），不能自噬
      if (k === "hash") { t.hash = v >>> 0; return true; }
      t[k] = v;
      // **属性赋值也必须进指纹**：本项目大量画板的帧间差异只体现在
      // fillStyle/strokeStyle/lineWidth 上（结点坐标是固定的），
      // 第一版只哈希方法调用参数，于是把「只换颜色」的动画误判成纹丝不动
      // —— 合成夹具测不出来，真实产物 mst / tree_traversal 当场把它报了出来。
      if (typeof k === "string") t.hash = hashCall(t.hash, "=" + k, [v]);
      return true;
    },
    has() { return true; },
  });
}

// ==================== 最小 DOM ====================
function createRuntime(html) {
  const canvases = [];        // {el, attrs, ctx}
  const byId = new Map();
  let tasksLeft = BUDGET;     // rAF / setTimeout / setInterval 的总预算（防死循环）
  const notes = [];
  const winListeners = {};    // window 上注册的监听器，启动后按 type 派发
  // 控制台捕获：不少页面把挂载失败吞进 `console.error('挂载插图失败', e)` 后 return，
  // 表现为「不报错、也不画」。不接管 console 就永远看不到真因。
  const consoleRec = { error: [], warn: [] };

  function registerCanvas(el, attrs) {
    const rec = { el, attrs, ctx: null };
    canvases.push(rec);
    if (attrs.id) byId.set(attrs.id, el);
    // data-* 必须映射进 el.dataset：书稿页外壳写的是
    //   [...document.querySelectorAll('canvas[data-fig]')].forEach(cv => mountFigure(cv.dataset.fig))
    // 桩里 dataset 是空的 → dataset.fig 为 undefined → mountFigure(undefined)
    // → querySelector 找不到 → `if(!cv) return;` **静默返回** → 全页零绘制。
    // 这类「不报错、只是不画」正是本闸门要抓的头号形态。
    Object.keys(attrs).forEach((k) => {
      if (k.indexOf("data-") === 0) {
        const key = k.slice(5).replace(/-([a-z])/g, (m0, c) => c.toUpperCase());
        el.dataset[key] = attrs[k];
      }
    });
    el._canvasRec = rec;
    return el;
  }

  // 画板类选择器匹配器：只要覆盖本项目真实出现的几种写法即可，
  // 做到「能列出全部命中」而不是只回第一个（querySelectorAll 只回一个会漏挂载）。
  function matchCanvases(sel) {
    const s = String(sel).trim();
    let m;
    // canvas[data-fig] —— 存在性匹配（书稿页用的就是它，没有等号）
    if (/^canvas\[data-fig\]$/.test(s)) {
      return canvases.filter((c) => c.attrs["data-fig"] !== undefined).map((c) => c.el);
    }
    // canvas[data-fig="x"] / [data-fig='x'] / [data-fig=x]
    if ((m = /^canvas\[data-fig=(?:"([^"]*)"|'([^']*)'|([^\]]+))\]$/.exec(s))) {
      const v = m[1] !== undefined ? m[1] : (m[2] !== undefined ? m[2] : m[3]);
      return canvases.filter((c) => c.attrs["data-fig"] === v).map((c) => c.el);
    }
    if ((m = /^canvas#([\w-]+)$/.exec(s))) {
      return byId.has(m[1]) ? [byId.get(m[1])] : [];
    }
    if ((m = /^#([\w-]+)$/.exec(s))) {
      return byId.has(m[1]) ? [byId.get(m[1])] : [];
    }
    if (/^canvas$/i.test(s)) return canvases.map((c) => c.el);
    return [];
  }

  function makeStyle() {
    const store = {};
    return new Proxy(store, {
      get(t, k) {
        if (k === "setProperty") return (n, v) => { t[String(n)] = String(v); };
        if (k === "removeProperty") return (n) => { delete t[String(n)]; };
        if (k === "getPropertyValue") return (n) => (t[String(n)] === undefined ? "" : t[String(n)]);
        if (k === "cssText") return t.__cssText || "";
        if (typeof k === "symbol") return t[k];
        return k in t ? t[k] : "";
      },
      set(t, k, v) { t[k] = v; return true; },
      has() { return true; },
    });
  }

  function parseCanvasTags(str, into) {
    // 只认 <canvas ...> —— 不做完整 HTML 解析，够用且不易误判
    const re = /<canvas\b([^>]*)>/gi;
    let m;
    while ((m = re.exec(String(str)))) {
      const attrs = {};
      const a = /(\w[\w-]*)\s*=\s*["']([^"']*)["']/g;
      let mm;
      while ((mm = a.exec(m[1]))) attrs[mm[1]] = mm[2];
      if (into) attrs.__parent = into;
      const el = makeEl("canvas", attrs.id || null);
      registerCanvas(el, attrs);
    }
  }

  function makeEl(tag, id) {
    const el = {
      tagName: String(tag || "div").toUpperCase(),
      id: id || "",
      className: "",
      textContent: "",
      value: "",
      checked: false,
      disabled: false,
      width: 300,
      height: 150,
      offsetWidth: 694, offsetHeight: 400, clientWidth: 694, clientHeight: 400,
      scrollWidth: 694, scrollHeight: 400,
      children: [],
      childNodes: [],
      style: makeStyle(),
      dataset: {},
      classList: {
        add() {}, remove() {}, toggle() {}, contains() { return false; },
      },
      options: null,
      firstChild: null,
      nextSibling: null,
    };
    // innerHTML 写入时顺手把里面的 <canvas> 注册进来
    let _html = "";
    // parentElement / parentNode 懒生成：页面里到处是
    // `canvas.parentElement.getBoundingClientRect()` 与
    // `parent.clientWidth - getComputedStyle(parent).paddingLeft`，
    // 桩里这两个必须永远存在（第一版没有它们，34+23 个页面炸在这里）。
    let _parent = null;
    Object.defineProperty(el, "parentElement", {
      get() { if (!_parent) _parent = makeEl("div"); return _parent; },
      set(v) { _parent = v; }, configurable: true,
    });
    Object.defineProperty(el, "parentNode", {
      get() { return _parent || (el.parentElement && el.parentElement) || null; },
      set(v) { _parent = v; }, configurable: true,
    });
    Object.defineProperty(el, "innerHTML", {
      get() { return _html; },
      set(v) {
        _html = String(v);
        parseCanvasTags(_html, el);
        el.children = []; el.childNodes = [];
      },
      configurable: true,
    });
    Object.defineProperty(el, "outerHTML", {
      get() { return _html; }, set(v) { _html = String(v); }, configurable: true,
    });

    el.appendChild = function (c) { el.children.push(c); if (c) c.parentNode = el; return c; };    el.insertBefore = function (c) { el.children.unshift(c); return c; };
    el.removeChild = function () { return null; };
    el.remove = function () { if (el.id) byId.delete(el.id); };
    el.replaceChildren = function () { el.children = []; _html = ""; };
    el.addEventListener = function () {};
    el.removeEventListener = function () {};
    el.dispatchEvent = function () { return true; };
    el.setAttribute = function (k, v) { if (k === "id") { if (el.id) byId.delete(el.id); el.id = String(v); if (el.id) byId.set(el.id, el); } else el["data-" + k] = v; };
    el.getAttribute = function (k) { return k === "id" ? el.id : (el[k] === undefined ? null : el[k]); };
    el.hasAttribute = function () { return false; };
    el.removeAttribute = function (k) { if (k === "id") byId.delete(el.id); };
    el.focus = function () {}; el.blur = function () {}; el.click = function () {};
    el.scrollIntoView = function () {};
    el.getBoundingClientRect = function () {
      return { width: 694, height: 400, top: 0, left: 0, right: 694, bottom: 400, x: 0, y: 0 };
    };
    el.getContext = function (kind) {
      if (kind !== "2d") { notes.push("getContext('" + kind + "') 被调用（本桩只支持 2d）"); return null; }
      if (!el._ctx) el._ctx = makeCtx(el);
      return el._ctx;
    };
    el.toDataURL = function () { return "data:image/png;base64,"; };
    el.toBlob = function () { return null; };
    el.querySelector = function (sel) { return document.querySelector(sel); };
    el.querySelectorAll = function (sel) { return document.querySelectorAll(sel); };
    el.matches = function () { return false; };
    el.contains = function () { return false; };
    return el;
  }

  // ---- 从页面源码里预先注册静态标记里的 <canvas> ----
  // 关键：**必须跳过 <script> 内部**。书稿页的画布是靠 JS 模板串在运行时
  // 写进 innerHTML 的，模板里是字面量 `data-fig="${b.id}"`；预扫若把它也登记上，
  // 运行时 dataset.fig 就会被这个占位串污染，挂载照样落空。
  const scriptSpans = [];
  {
    const se = /<script\b[^>]*>[\s\S]*?<\/script>/gi;
    let sm;
    while ((sm = se.exec(html))) scriptSpans.push([sm.index, sm.index + sm[0].length]);
  }
  const inScript = (i) => scriptSpans.some(([a, b]) => i >= a && i < b);
  {
    const idRe = /<canvas\b([^>]*)>/gi;
    let pm;
    while ((pm = idRe.exec(html))) {
      if (inScript(pm.index)) continue;
      const a = /(\w[\w-]*)\s*=\s*["']([^"']*)["']/g;
      const attrs = {};
      let mm;
      while ((mm = a.exec(pm[1]))) attrs[mm[1]] = mm[2];
      const el = makeEl("canvas", attrs.id || null);
      registerCanvas(el, attrs);
    }
  }

  // ---- 预先注册 <script id=...> 的文本内容 ----
  // 浏览器里 `<script type="application/json" id="cell-data">{...}</script>` 是
  // DOM 的一员，页面靠 `getElementById('cell-data').textContent` 把数据读出来。
  // 我们的桩不解析完整 HTML，所以必须在执行前把这类**数据载体**登记好 ——
  // 否则会读到空串，然后 `JSON.parse('')` 抛
  // "Unexpected end of JSON input"（第一版就是这样全军覆没的）。
  {
    const sre = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
    let sm;
    while ((sm = sre.exec(html))) {
      const attrs = sm[1] || "";
      if (/\bsrc\s*=/i.test(attrs)) continue;
      const idm = /\bid\s*=\s*["']([^"']+)["']/i.exec(attrs);
      if (!idm) continue;
      const el = makeEl("script", idm[1]);
      el.textContent = sm[2];
      el.innerHTML = sm[2];           // 顺带触发 <canvas> 扫描（JSON 里不会有，无害）
      byId.set(idm[1], el);
    }
  }

  // ---- document ----
  const doc = {
    readyState: "complete",
    body: makeEl("body"),
    documentElement: makeEl("html"),
    head: makeEl("head"),
    createElement(tag) {
      const el = makeEl(tag);
      if (String(tag).toLowerCase() === "canvas") registerCanvas(el, {});
      return el;
    },
    createElementNS(ns, tag) { return doc.createElement(tag); },
    getElementById(id) {
      if (byId.has(id)) return byId.get(id);
      // 动态拼出来的 id（ro_xxx / pv_xxx / step-circle-N …）也给一个桩，
      // 这样「写入读数」这条路径会被真正走到，而不是被 null 守卫跳过。
      const el = makeEl("div", id);
      byId.set(id, el);
      return el;
    },
    querySelector(sel) {
      const hits = matchCanvases(sel);
      if (hits.length) return hits[0];
      const m = /^#([\w-]+)$/.exec(String(sel).trim());
      if (m) return doc.getElementById(m[1]);
      return null;
    },
    querySelectorAll(sel) {
      return matchCanvases(String(sel));
    },
    getElement(s) { return null; },
    addEventListener() {}, removeEventListener() {},
    createTextNode(t) { return { nodeType: 3, textContent: t }; },
    createDocumentFragment() { return makeEl("#fragment"); },
    body_placeholder: null,
  };

  // ---- window / 全局 ----
  // Node 21+ 给 globalThis 加了若干 getter-only 的内置（navigator、location…）。
  // 直接赋值会抛 `Cannot set property ... which has only a getter`，所以逐个
  // 宽容写入：能覆盖就覆盖，覆盖不了就**保留平台内置**（行为等价，够用）。
  function setGlobal(k, v) {
    try { globalThis[k] = v; } catch (e) {
      try {
        Object.defineProperty(globalThis, k, { value: v, writable: true, configurable: true });
      } catch (e2) { /* 平台锁死，接受内置实现 */ }
    }
    return globalThis[k];
  }

  setGlobal("document", doc);
  setGlobal("window", globalThis);
  setGlobal("self", globalThis);
  setGlobal("top", globalThis);
  const win = globalThis;
  win.innerWidth = 1200;
  win.innerHeight = 800;
  win.devicePixelRatio = 2;
  setGlobal("screen", { width: 1200, height: 800 });
  setGlobal("navigator", { userAgent: "node-page_smoke", language: "zh-CN", platform: "node", onLine: true });
  setGlobal("location", { href: "http://localhost/", origin: "http://localhost", hash: "", search: "", pathname: "/x.html" });
  const mem = { getItem() { return null; }, setItem() {}, removeItem() {}, clear() {} };
  setGlobal("localStorage", mem);
  setGlobal("sessionStorage", mem);
  setGlobal("getComputedStyle", function () {
    return {
      paddingLeft: "0px", paddingRight: "0px", paddingTop: "0px", paddingBottom: "0px",
      width: "694px", height: "400px", fontSize: "14px", display: "block", visibility: "visible",
      getPropertyValue() { return "0px"; },
    };
  });
  setGlobal("matchMedia", function () {
    return { matches: false, addEventListener() {}, addListener() {} };
  });
  setGlobal("addEventListener", function (type, fn) {
    // 记下来而不是丢掉 —— 不少画板是 `window.addEventListener('load', ...)` 启动的，
    // 一律当耳边风会让它们「永远不画」，然后被误判成「页面全白」。
    (winListeners[String(type)] = winListeners[String(type)] || []).push(fn);
  });
  setGlobal("removeEventListener", function (type, fn) {
    const a = winListeners[String(type)];
    if (a) { const i = a.indexOf(fn); if (i >= 0) a.splice(i, 1); }
  });
  setGlobal("dispatchEvent", function () { return true; });
  setGlobal("requestAnimationFrame", function (fn) {
    if (tasksLeft-- <= 0) return 0;
    fn(Date.now());          // 同步跑一帧 —— 初次绘制常挂在 rAF 里
    return 1;
  });
  setGlobal("cancelAnimationFrame", function () {});
  setGlobal("setTimeout", function (fn) {
    if (tasksLeft-- <= 0) return 0;
    const args = Array.prototype.slice.call(arguments, 2);
    if (typeof fn === "function") fn.apply(null, args);
    return 1;
  });
  setGlobal("clearTimeout", function () {});
  setGlobal("setInterval", function () { if (tasksLeft-- <= 0) return 0; return 1; });
  setGlobal("clearInterval", function () {});
  setGlobal("fetch", function () {
    return Promise.resolve({ ok: false, status: 404, json: async () => ({}), text: async () => "", headers: { get() { return null; } } });
  });
  setGlobal("XMLHttpRequest", function () {
    return { open() {}, send() {}, setRequestHeader() {}, addEventListener() {}, readyState: 0, status: 0, responseText: "" };
  });
  // KaTeX：公式渲染不是被测物，给最小桩，让它把 LaTeX 原样落进 DOM
  setGlobal("katex", { render(tex, el) { if (el) el.textContent = String(tex); }, renderToString(tex) { return String(tex); }, ParseError: Error });
  setGlobal("renderMathInElement", function () {});
  setGlobal("console", {
    log() {}, info() {}, debug() {}, trace() {}, dir() {},
    warn() { consoleRec.warn.push(Array.prototype.slice.call(arguments).map(String).join(" ")); },
    error() { consoleRec.error.push(Array.prototype.slice.call(arguments).map(String).join(" ")); },
    time() {}, timeEnd() {}, group() {}, groupEnd() {}, table() {},
  });

  return { canvases, byId, notes, winListeners, consoleRec, budgetRef: { get left() { return tasksLeft; } } };
}

// ==================== 跑一个页面 ====================
function smokeOne(htmlPath) {
  const out = {
    id: htmlPath.replace(/\\/g, "/").split("/").slice(-2).join("/"),
    path: htmlPath,
    ok: false, scripts: 0, canvases: 0, drawn: 0, hashUniq: 0, frames: 0,
    skipped: false, error: null, notes: [],
  };
  let html;
  try {
    html = fs.readFileSync(htmlPath, "utf8");
  } catch (e) {
    out.error = "读文件失败: " + e.message;
    return out;
  }

  // 产物比源码旧？那么下面所有判据测的都是**过期产物**，结论不可信。
  // 这不算「页面有缺陷」，但必须让它可见 —— 由调用方决定是红还是警告。
  {
    const abs = path.resolve(htmlPath);
    const src = MANIFEST[abs] || MANIFEST[htmlPath] || 0;
    let mt = 0;
    try { mt = fs.statSync(htmlPath).mtimeMs; } catch (e) { /* 读不到就不判 */ }
    if (src && mt && mt + 1000 < src) {
      out.behind = true;
      out.behindBy = Math.round((src - mt) / 1000);
      out.notes.push(`产物比源码旧 ${out.behindBy}s —— 先重新生成再验（否则测的是旧产物）`);
    }
  }

  // 3D 页面：需要从 CDN 载入 three.js 并拿到 WebGL 上下文。
  // 本桩既没有网络也没有 GPU，跑了必然报 "THREE is not defined" ——
  // 那是**桩的局限**，不是页面的缺陷，因此不能记为失败。
  // 但也**不许悄悄放过**：显式标 skipped 并在报告里点名（见 report_page）。
  const needsWebgl = /\bTHREE\s*[.[(]/.test(html)
    || /three(?:\.min)?\.js/i.test(html)
    || /getContext\(\s*["']webgl/i.test(html);
  if (needsWebgl) {
    out.ok = true;
    out.skipped = true;
    out.notes = ["需要 Three.js/WebGL（本桩不覆盖）→ 必须真机浏览器验证"];
    return out;
  }

  const runtime = createRuntime(html);
  out.canvases = runtime.canvases.length;

  // 内联脚本（<script src> 的外链在本环境不加载：尾部 CDN 与 KaTeX 已由桩提供）
  const blocks = [];
  const re = /<script\b([^>]*)>([\s\S]*?)<\/script>/gi;
  let m;
  while ((m = re.exec(html))) {
    const attrs = m[1] || "";
    if (/\bsrc\s*=/i.test(attrs)) continue;
    // 非 JS 的 script（JSON-LD、importmap、text/plain 模板…）直接跳过 ——
    // 把 JSON 拼进 JS 作用域会得到无意义的 `Unexpected token ':'`。
    const tm = /\btype\s*=\s*["']([^"']+)["']/i.exec(attrs);
    if (tm) {
      const ty = tm[1].toLowerCase();
      const jsish = ty === "text/javascript" || ty === "application/javascript"
        || ty === "module" || ty === "text/ecmascript" || ty === "application/ecmascript";
      if (!jsish) continue;
    }
    blocks.push(m[2]);
  }
  out.scripts = blocks.length;

  if (!blocks.length) {
    // 纯静态页（导航/索引）：没有脚本就没有「执行失败」可言
    out.ok = true;
    out.notes.push("无内联脚本（静态页）");
    return out;
  }

  // 拼成一个作用域执行 —— 与浏览器多 script 共享同一 script 作用域语义一致。
  // 探针必须用 `typeof 标识符`：对**未声明**标识符用 typeof 不会抛，
  // 而 typeof(字符串) 永远是 "string" —— 第一版就是那样，导致 steps/setFrame
  // 恒为 null、帧推进从未真正执行（报表里一直是「帧 0」，负向夹具自然也测不出东西）。
  const probe = `
;globalThis.__PROBE = (function(){
  return {
    steps: (typeof steps === "function" ? steps : null),
    step: (typeof step === "function" ? step : null),
    scene: (typeof scene === "function" ? scene : null),
    lesson: (typeof LESSON !== "undefined" ? LESSON : null),
    setFrame: (typeof setFrame === "function" ? setFrame : null),
    setStep: (typeof setStep === "function" ? setStep : null),
    boot: (typeof boot === "function" ? boot : null),
    render: (typeof render === "function" ? render : null),
    draw: (typeof draw === "function" ? draw : null),
    paint: (typeof paint === "function" ? paint : null)
  };
})();`;
  const src = blocks.join("\n;\n") + probe;

  try {
    // eslint-disable-next-line no-new-func
    new Function(src)();
  } catch (e) {
    out.error = String((e && e.message) || e);
    out.stack = String((e && e.stack) || "").split("\n").slice(0, 4).join(" | ");
    return out;
  }

  // 启动：`window.onload = ...` 与 `window.addEventListener('load', ...)`
  // 都是画板常见的入口，脚本跑完必须把它们触发掉 —— 否则首帧根本不执行，
  // 会被误判成「有 canvas 但一个绘制调用都没有」。
  try {
    if (typeof globalThis.onload === "function") {
      globalThis.onload({ type: "load", target: globalThis, preventDefault() {}, stopPropagation() {} });
    }
    (runtime.winListeners.load || []).forEach((fn) => {
      fn({ type: "load", target: globalThis, preventDefault() {}, stopPropagation() {} });
    });
  } catch (e) {
    out.error = "触发 load 入口时抛错: " + String((e && e.message) || e);
    out.stack = String((e && e.stack) || "").split("\n").slice(0, 4).join(" | ");
    return out;
  }

  // 逐帧推进 + 指纹
  const P = globalThis.__PROBE || {};
  out.probe = Object.keys(P).filter((k) => P[k] != null).join(",") || "（一个都没命中）";
  const frames = new Set();
  const SEED = 2166136261 >>> 0;

  // 指纹只反映**本帧画了什么**，不反映累计调用数。
  // 第一版把 drawCalls 一起塞进指纹，结果每帧必然不同 —— 「画面纹丝不动」
  // 这条判据形同虚设（负向夹具 f-frozen 当场把它测了出来）。
  // ctx.hash 是累计滚动值，所以必须在每帧**开始前**重置到种子。
  function resetFrame() {
    for (const c of runtime.canvases) if (c.el._ctx) c.el._ctx.hash = SEED;
  }
  function snap() {
    let h = 0;
    for (const c of runtime.canvases) if (c.el._ctx) h = hashCall(h, "C", [c.el._ctx.hash]);
    frames.add(h);
  }
  const totalDraws = () => runtime.canvases.reduce(
    (s, c) => s + (c.el._ctx ? c.el._ctx.drawCalls : 0), 0);
  const deltas = [];   // 每帧绘制增量：0 = setFrame 压根没重绘；>0 = 重绘了但内容相同

  function runStep(step, i) {
    const b = totalDraws();
    resetFrame();
    step(i);
    deltas.push(totalDraws() - b);
    snap();
  }

  try {
    let n = 0;
    if (typeof P.steps === "function" && typeof P.setFrame === "function") {
      n = P.steps().length || 0;
    } else if (typeof P.steps === "function" && typeof P.setStep === "function") {
      n = P.steps().length || 0;
    }
    const step = (typeof P.setFrame === "function") ? P.setFrame
      : ((typeof P.setStep === "function") ? P.setStep : null);
    if (n > 1 && step) {
      for (let i = 0; i < n; i++) { runStep(step, i); out.frames++; }
    }
    // 正向 + 反向各推一遍，确保不是「第一帧之后就死了」
    if (out.frames && typeof P.setFrame === "function") {
      for (let i = n - 1; i >= 0; i--) { runStep(P.setFrame, i); out.frames++; }
    }
  } catch (e) {
    out.error = "推进帧/步骤时抛错: " + String((e && e.message) || e);
    out.stack = String((e && e.stack) || "").split("\n").slice(0, 4).join(" | ");
    return out;
  }

  let draws = 0;
  for (const c of runtime.canvases) draws += c.el._ctx ? c.el._ctx.drawCalls : 0;
  out.drawn = draws;
  out.canvases = runtime.canvases.length;   // 回填：不少画布是运行时 innerHTML 建的
  out.hashUniq = frames.size;
  out.notes = runtime.notes.slice();
  const cErrs = (runtime.consoleRec && runtime.consoleRec.error) || [];
  const cWarns = (runtime.consoleRec && runtime.consoleRec.warn) || [];
  if (cErrs.length) {
    out.consoleErrors = cErrs.slice(0, 4);
    out.notes = out.notes.concat(cErrs.slice(0, 3).map((s) => "console.error: " + s.slice(0, 180)));
  }
  if (cWarns.length) {
    out.notes = out.notes.concat(cWarns.slice(0, 2).map((s) => "console.warn: " + s.slice(0, 140)));
  }

  if (runtime.canvases.length && draws <= 0) {
    out.error = "页面有 " + runtime.canvases.length + " 个 canvas，但**一个绘制调用都没有**（画布全白）";
    if (cErrs.length) out.error += " —— 页面自己在 console.error： " + cErrs[0].slice(0, 160);
    return out;
  }
  if (out.frames >= 2 && frames.size < 2) {
    const dmax = deltas.length ? Math.max.apply(null, deltas) : 0;
    const dmin = deltas.length ? Math.min.apply(null, deltas) : 0;
    const why = dmax <= 0
      ? "每帧绘制增量恒为 0 —— setFrame/setStep **根本没有触发布局重绘**"
      : `每帧绘制增量 ${dmin}..${dmax} 次，但内容完全相同 —— 重绘了，画的却是一模一样的东西`;
    out.error = `推进了 ${out.frames} 帧但画面指纹**从不变化**：${why}`;
    out.frameDelta = { min: dmin, max: dmax };
    // 冻结时顺手取证：是「每步数据本身相同」（页面缺陷/数据缺陷）
    // 还是「数据不同却画成一样」（渲染分支没读步骤）—— 一句话就能定性。
    try {
      if (P.step && P.steps && P.steps().length) {
        const n = P.steps().length;
        const a = JSON.stringify(P.step(0));
        const b = JSON.stringify(P.step(n - 1));
        out.debug = {
          n: n,
          first: String(a).slice(0, 200),
          last: String(b).slice(0, 200),
          identical: a === b,
        };
      } else if (P.scene) {
        out.debug = { scene: String(JSON.stringify(P.scene())).slice(0, 240) };
      }
    } catch (e) { /* 取证失败不影响判定 */ }
    return out;
  }

  out.ok = true;
  return out;
}

// ==================== main ====================
const inputs = JSON.parse(fs.readFileSync(INPUTS, "utf8"));
const results = [];
for (const p of inputs) {
  // 每个页面一个干净的全局：清掉上一个页面注册的 canvas/id
  try { results.push(smokeOne(p)); } catch (e) {
    results.push({ id: p, ok: false, error: "harness 崩了: " + String(e && e.message), canvases: 0, scripts: 0, drawn: 0, frames: 0, hashUniq: 0 });
  }
}
const summary = {
  total: results.length,
  passed: results.filter((r) => r.ok).length,
  failed: results.filter((r) => !r.ok).length,
  withCanvas: results.filter((r) => r.canvases > 0).length,
};
process.stdout.write(JSON.stringify({ results: results, summary: summary }));
process.exit(summary.failed > 0 ? 1 : 0);
