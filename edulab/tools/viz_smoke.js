/*!
 * viz_smoke.js — viz.js 的**执行级**冒烟测试（Node + stub DOM/canvas）。
 *
 * 为什么需要它
 *   `vizkit.validate()` 是**静态**校验：只检查图层数据（出界/重叠/颜色），
 *   **从不执行 JS**。于是 renderer 本身坏掉时会出现诡异组合：
 *       数据全对 + 闸门全绿 + 页面全白
 *   实际踩过的坑（2026-10）：`Renderer.resize` 末尾写着
 *       this.W = rect.width;  // rect 从未定义
 *   每次 resize 抛 ReferenceError，书稿 36 张图全部挂不上，
 *   而静态闸门一路绿灯 —— 因为它压根不跑 JS。
 *
 * 这个 harness 把渲染路径真的执行一遍，专抓**只有跑起来才知道**的错：
 *   未定义标识符、类型错误、NaN 坐标、步骤回放/参数绑定里的异常，
 *   以及「逐档推进但每档画出来的东西完全一样」（步骤绑定没生效）。
 *
 * 判据
 *   1. 不抛异常；逻辑尺寸 W/H 有限且 > 0（挡住 `rect` 那类静默残留）
 *   2. 必须真的产生绘制调用（挡住「没崩但空画布」）
 *   3. 逐档回放**每档画面指纹必须互不相同**（挡住「画布纹丝不动」）
 *      指纹 = 方法调用参数 + 属性赋值（fillStyle/strokeStyle 等）——
 *      图形元素常靠改颜色表达「当前高亮哪一项」，漏掉属性赋值会误判静止
 *   4. 参数端点（min/max）全部走一遍不炸；`Viz.audit()` 宽度同样合法
 *
 * 用法
 *   node viz_smoke.js --viz <viz.js 路径> --specs <specs.json>
 *   specs.json 形如 { "fig-id": <spec 对象>, ... }
 *
 * 输出：单行 JSON（stdout）。stderr 留给 node 自身的报错。
 * 退出码：全部通过 0，任一失败 1。
 */
"use strict";

const fs = require("fs");
const path = require("path");

// ==================== 参数 ====================
function arg(name, dflt) {
  const i = process.argv.indexOf(name);
  return i >= 0 && process.argv[i + 1] ? process.argv[i + 1] : dflt;
}
const VIZ_PATH = arg("--viz", "");
const SPECS_PATH = arg("--specs", "");
if (!VIZ_PATH || !SPECS_PATH) {
  process.stderr.write("usage: node viz_smoke.js --viz <viz.js> --specs <specs.json>\n");
  process.exit(2);
}

// ==================== stub：DOM / canvas ====================
// 真实尺寸用书页 canvas 的宽度（与 vizkit.PAGE_CANVAS_W 对齐，由调用方给出）
const STUB_W = Number(arg("--w", "694"));
const STUB_H = Number(arg("--h", "400"));
const STUB_DPR = Number(arg("--dpr", "2"));   // 刻意用 2，走一遍高分屏路径

const DRAW_OPS = ["stroke", "fill", "fillText", "fillRect", "strokeRect", "drawImage",
  "fillStroke", "clip", "arc", "beginPath", "moveTo", "lineTo", "closePath", "rect",
  "quadraticCurveTo", "bezierCurveTo", "translate", "scale", "rotate", "setTransform"];

function makeCtx(canvas) {
  // Proxy：未登记的方法一律当作可调用；已赋值的属性按原值返回。
  const store = {
    canvas: canvas,
    // measureText 必须返回**像样的宽度** —— renderer 用它做标注避让与溢出判断。
    measureText: (s) => ({ width: String(s == null ? "" : s).length * 7.2 }),
    createLinearGradient: () => ({ addColorStop() {} }),
    createRadialGradient: () => ({ addColorStop() {} }),
    createPattern: () => null,
    getImageData: (x, y, w, h) => ({ data: new Uint8ClampedArray(Math.max(1, w * h * 4)), width: w, height: h }),
  };
  let drawCalls = 0;
  // 画面指纹：逐档回放时用来判断「这一档真的画出了不同的东西」。
  // 与 page_smoke.js 同一条纪律 —— 只验「不抛异常」会漏掉「画布纹丝不动」。
  const SEED = 2166136261 >>> 0;
  let hash = SEED;
  const counted = new Set(DRAW_OPS);
  return new Proxy(store, {
    get(t, k) {
      if (k === "ctxDrawCalls") return drawCalls;
      if (k === "__resetHash") return function () { hash = SEED; };
      if (k === "__getHash") return function () { return hash; };
      if (k in t) return t[k];
      return function () {
        const args = Array.prototype.slice.call(arguments);
        if (counted.has(String(k))) drawCalls++;
        hash = hashCall(hash, String(k), args);
        return undefined;
      };
    },
    set(t, k, v) {
      t[k] = v;
      // **属性赋值也要进指纹**：图形元素常靠改 fillStyle/strokeStyle/lineWidth 表达
      // 「当前档高亮哪个」，坐标不动。只哈希方法参数会把这类动画误判成静止。
      if (typeof k === "string" && k !== "canvas") hash = hashCall(hash, "=" + k, [v]);
      return true;
    },
    has() { return true; },
  });
}

function hashCall(h, name, args) {
  let x = h;
  x = (x * 31 + name.charCodeAt(0) * 7 + name.length * 13) % 4294967291;
  for (let i = 0; i < args.length; i++) {
    const a = args[i];
    let v;
    if (a === null) v = 0;
    else if (a === undefined) v = 1;
    else if (typeof a === "number") v = isFinite(a) ? Math.round(a * 1000) : (isNaN(a) ? 2 : 3);
    else if (typeof a === "string") v = a.length * 17 + (a.charCodeAt(0) || 0) * 3;
    else v = 4;
    x = (x * 33 + (v % 100003)) % 4294967291;
  }
  return x >>> 0;
}

function makeCanvas() {
  const el = {
    width: 0,
    height: 0,
    style: {},
    parentElement: null,
    getContext(kind) {
      if (kind === "2d") { if (!el._ctx) el._ctx = makeCtx(el); return el._ctx; }
      return null;   // 本项目只用 2D；返回 null 让调用方显式暴露
    },
    getBoundingClientRect() { return { width: STUB_W, height: el.style.height ? parseFloat(el.style.height) : STUB_H, top: 0, left: 0 }; },
    addEventListener() {},
    removeEventListener() {},
    dispatchEvent() { return true; },
    clientWidth: STUB_W,
    clientHeight: STUB_H,
    _ctx: null,
  };
  // 父容器：resize() 从它读内容盒宽度与已声明高度
  el.parentElement = {
    clientWidth: STUB_W + 40,     // 多给 40，让 padding 减法有真实效果
    clientHeight: STUB_H,
    getBoundingClientRect() { return { width: STUB_W + 40, height: STUB_H, top: 0, left: 0 }; },
    getComputedStyle: null,
    style: {},
  };
  return el;
}

// ---- 安装到 globalThis ----
globalThis.document = {
  createElement(tag) {
    if (tag === "canvas") return makeCanvas();
    return { innerHTML: "", style: {}, appendChild() {}, addEventListener() {}, querySelectorAll: () => [], querySelector: () => null };
  },
  getElementById() { return null; },
  querySelector() { return null; },
  querySelectorAll() { return []; },
  addEventListener() {},
  removeEventListener() {},
  documentElement: { style: {} },
};
globalThis.getComputedStyle = function () {
  // 只要能被 parseFloat 解析即可；刻意留一点 padding 让减法被真正执行
  return {
    paddingLeft: "0px", paddingRight: "0px", paddingTop: "0px", paddingBottom: "0px",
    getPropertyValue() { return "0px"; },
  };
};
globalThis.devicePixelRatio = STUB_DPR;
globalThis.addEventListener = function () {};
globalThis.removeEventListener = function () {};
globalThis.matchMedia = function () { return { matches: false, addEventListener() {} }; };
if (typeof globalThis.requestAnimationFrame === "undefined") {
  globalThis.requestAnimationFrame = function (fn) { fn(0); return 0; };
}

// ==================== 载入 viz.js ====================
const vizSrc = fs.readFileSync(VIZ_PATH, "utf8");
// 用 Function 而非 require：viz.js 是 IIFE，本身不是模块。
// 直接 eval 到当前作用域，IIFE 会把 Viz 挂到 globalThis 上。
try {
  // eslint-disable-next-line no-new-func
  new Function(vizSrc)();
} catch (e) {
  process.stdout.write(JSON.stringify({
    fatal: String((e && e.stack) || e),
    results: [],
    summary: { total: 0, passed: 0, failed: 0 },
  }));
  process.exit(1);
}

const Viz = globalThis.Viz;
if (!Viz || typeof Viz.mount !== "function" || typeof Viz.audit !== "function") {
  process.stdout.write(JSON.stringify({
    fatal: "viz.js 载入后 globalThis.Viz 缺失或不完整",
    results: [],
    summary: { total: 0, passed: 0, failed: 0 },
  }));
  process.exit(1);
}

// ==================== 跑每张图 ====================
const specs = JSON.parse(fs.readFileSync(SPECS_PATH, "utf8"));
const results = [];

for (const id of Object.keys(specs)) {
  const spec = specs[id];
  const r = { id, ok: false, W: 0, H: 0, drawCalls: 0, stepsRun: 0, stepHashes: 0,
              paramsRun: 0, audit: null, error: null };

  let viz = null;
  let canvas = null;
  try {
    canvas = makeCanvas();
    viz = Viz.mount(canvas, spec);

    // 1) 逻辑尺寸必须是真的（`rect` 那类 bug 会让它停在 0 或 undefined）
    if (!isFinite(viz.W) || !isFinite(viz.H) || viz.W <= 0 || viz.H <= 0) {
      throw new Error("renderer 逻辑尺寸非法：W=" + viz.W + " H=" + viz.H);
    }

    // 2) 真的画了东西（空画布也算「没崩」，必须显式挡住）
    r.drawCalls = canvas._ctx ? canvas._ctx.ctxDrawCalls : 0;
    if (r.drawCalls <= 0) throw new Error("渲染路径未产生任何绘制调用（画布全白）");

    // 3) 逐档回放 —— 很多 bug 只在第 2 步之后才露头
    //    同时逐档取画面指纹：只验「不抛异常」会漏掉「推进了但画面纹丝不动」。
    const nSteps = viz.stepCount();
    const stepHashes = [];
    for (let i = 0; i < nSteps; i++) {
      if (canvas._ctx) canvas._ctx.__resetHash();
      viz.setStep(i);
      if (canvas._ctx) stepHashes.push(canvas._ctx.__getHash());
      r.stepsRun++;
    }
    if (nSteps > 1) {
      const uniq = new Set(stepHashes).size;
      r.stepHashes = uniq;
      if (uniq < 2) {
        throw new Error(`逐档回放 ${nSteps} 步，但画面指纹**从不变化**`
                        + `（画布纹丝不动：步骤绑定没生效，或每一步画的是同一张图）`);
      }
    }
    if (nSteps > 1) viz.setStep(0);

    // 4) 参数端点 —— 绑定表达式只在参数变化时才求值
    (spec.params || []).forEach((p) => {
      viz.setParam(p.name, p.min); r.paramsRun++;
      viz.setParam(p.name, p.max); r.paramsRun++;
      if (p.min !== p.value && p.max !== p.value) viz.setParam(p.name, p.value);
    });

    // 5) 用官方 audit 再走一遍（它是给 CI 设计的，也走 resize/drawScene）
    const a = Viz.audit(canvas, spec);
    r.audit = { ok: !!a.ok, overflow: (a.overflow || []).length, outside: (a.outside || []).length };
    if (!isFinite(a.width) || a.width <= 0) throw new Error("audit 得到非法宽度 " + a.width);

    r.W = viz.W; r.H = viz.H;
    r.drawCalls = canvas._ctx.ctxDrawCalls;
    r.ok = true;
  } catch (e) {
    r.error = String((e && e.message) || e);
    r.stack = String((e && e.stack) || "").split("\n").slice(0, 4).join(" | ");
    r.W = viz && isFinite(viz.W) ? viz.W : 0;
    r.H = viz && isFinite(viz.H) ? viz.H : 0;
    r.drawCalls = canvas && canvas._ctx ? canvas._ctx.ctxDrawCalls : 0;
  } finally {
    try { if (viz && viz.destroy) viz.destroy(); } catch (e) { /* 忽略清理失败 */ }
  }
  results.push(r);
}

const summary = {
  total: results.length,
  passed: results.filter((x) => x.ok).length,
  failed: results.filter((x) => !x.ok).length,
  vizVersion: Viz.version || "unknown",
  stub: { w: STUB_W, dpr: STUB_DPR },
};

process.stdout.write(JSON.stringify({ fatal: null, results: results, summary: summary }));
process.exit(summary.failed > 0 ? 1 : 0);
