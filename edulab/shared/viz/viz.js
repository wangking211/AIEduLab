/*!
 * viz.js — 教学图解「图形语法」引擎（单文件、零依赖、Canvas 2D）
 *
 * 目标：把各科手写的 drawXxx 函数，换成**声明式图层描述**——
 *   { view, layers:[ {geom, ...} ], params, scalars, steps }
 * 引擎负责：坐标系、刻度、绘制、标注避让、步骤回放、参数绑定、越界审计。
 *
 * 设计原则
 *  1. 单文件、无外部依赖 → 生成器可整段内联进自包含 HTML。
 *  2. 声明式：新题型只写数据 + 选图元，不写绘制代码。
 *  3. 数据里的字符串一律当**表达式**求值（绑定到 params/scalars/当前步），
 *     所以滑块与步骤回放天然生效。
 *  4. 标注统一走 annot()：像素偏移 + 靠边自动翻转 → 不会出框、不会叠字。
 *  5. audit() 可离线检查越界/遮挡，供 CI 与自检使用。
 *
 * 用法
 *   const viz = Viz.mount(canvasEl, spec);
 *   viz.setStep(3); viz.setParam('n', 100); viz.render();
 *   const report = Viz.audit(canvasEl, spec);
 */
(function (global) {
  "use strict";

  // ==================== 主题（深色仪表盘 / 浅色纸感书页）====================
  const THEMES = {
    // 深色：解题器的画板
    dark: {
      bg: "#0f172a", panel: "#1e293b", panelEdge: "#334155",
      axis: "#94a3b8", grid: "#334155", text: "#e2e8f0", dim: "#94a3b8", muted: "#64748b",
      accent: "#2dd4bf", accent2: "#a78bfa", good: "#10b981", warn: "#f59e0b", bad: "#ef4444",
      onFill: "#f1f5f9", halo: "rgba(15,23,42,.82)",
      series: ["#2dd4bf", "#a78bfa", "#f59e0b", "#60a5fa", "#f472b6", "#34d399", "#fb923c"],
      ramp: ["#166534", "#15803d", "#22c55e", "#86efac"],
      primary: "#0d9488", secondary: "#7c3aed", emphasis: "#f59e0b",
      ok: "#10b981", err: "#e11d48", neutral: "#64748b",
    },
    // 浅色：书的插图（纸感、印刷友好）
    paper: {
      bg: "#ffffff", panel: "#f7f4ee", panelEdge: "#d8d2c6",
      axis: "#8a8177", grid: "#ece7de", text: "#1f1b16", dim: "#7d756a", muted: "#a89f92",
      accent: "#b45309", accent2: "#6d28d9", good: "#15803d", warn: "#b45309", bad: "#b91c1c",
      onFill: "#1f1b16", halo: "rgba(255,255,255,.9)",
      series: ["#b45309", "#6d28d9", "#0f766e", "#1d4ed8", "#be123c", "#4d7c0f", "#c2410c"],
      ramp: ["#14532d", "#15803d", "#65a30d", "#bef264"],
      primary: "#b45309", secondary: "#6d28d9", emphasis: "#a16207",
      ok: "#15803d", err: "#b91c1c", neutral: "#78716c",
    },
  };

  // ==================== 设计令牌（design tokens）====================
  const T = {
    color: THEMES.dark,
    font: { family: 'system-ui,-apple-system,"PingFang SC","Microsoft YaHei",sans-serif', size: { xs: 10, sm: 11, md: 12, lg: 14, xl: 18, xxl: 24 } },
    space: { xs: 2, sm: 4, md: 8, lg: 14, xl: 22 },
    mark: { barW: 0.62, dotR: 5, nodeR: 15, lineW: 2.6, hair: 1.2, cellPad: 0.06 },
  };

  // ==================== 表达式求值 ====================
  const MATH = {
    sqrt: Math.sqrt, abs: Math.abs, min: Math.min, max: Math.max, pow: Math.pow,
    sign: Math.sign, floor: Math.floor, ceil: Math.ceil, round: Math.round,
    log: Math.log, log2: Math.log2, log10: Math.log10, exp: Math.exp,
    sinh: Math.sinh, cosh: Math.cosh, PI: Math.PI, E: Math.E,
  };
  const _cache = {};
  function evalExpr(expr, env) {
    if (typeof expr !== "string") return expr;
    const scope = Object.assign({}, MATH, env);
    const names = Object.keys(scope);
    const key = expr + "|" + names.join(",");
    let fn = _cache[key];
    if (!fn) {
      try { fn = Function(...names, '"use strict";return (' + expr.replace(/\^/g, "**") + ");"); }
      catch (e) { fn = () => NaN; }
      _cache[key] = fn;
    }
    try {
      const v = fn(...names.map((n) => scope[n]));
      // 既支持数值表达式，也支持布尔条件（如 when:"k >= 3"）
      return (typeof v === "number" || typeof v === "boolean") ? v : NaN;
    }
    catch (e) { return NaN; }
  }
  /** 深度解析：字符串若能求值则换成数值，否则原样返回（中文标签安全）。 */
  function resolve(v, env, deep) {
    if (typeof v === "string") {
      // 只对"像表达式"的串求值，避免把中文/说明文字误当表达式
      if (!/^[\s\dA-Za-z_+\-*/().^,%<>=!?:]*$/.test(v)) return v;
      const x = evalExpr(v, env);
      return isFinite(x) ? x : v;
    }
    if (deep && Array.isArray(v)) return v.map((z) => resolve(z, env, true));
    if (deep && v && typeof v === "object") {
      const o = {};
      for (const k in v) o[k] = resolve(v[k], env, true);
      return o;
    }
    return v;
  }

  // ==================== 数值格式 ====================
  function fmt(x, d) {
    if (x === null || x === undefined || !isFinite(x)) return "—";
    if (d == null) d = 2;
    let s = Number(x).toFixed(d);
    if (s === "-" + (0).toFixed(d)) s = (0).toFixed(d);
    return s;
  }
  const fmtInt = (x) => (!isFinite(x) ? "—" : Math.round(x).toLocaleString("zh-CN"));
  function fmtTick(v, step) {
    const av = Math.abs(v);
    if (av >= 10000) return +(v / 10000).toFixed(2) + "万";
    if (av >= 1 || v === 0) return String(+v.toFixed(6));
    const d = Math.max(0, Math.min(4, -Math.floor(Math.log10(Math.abs(step || av))) + 1));
    return (+v.toFixed(d)).toString();
  }
  /** 1/2/2.5/5/10 × 10^k 的"漂亮"刻度 */
  function niceTicks(a, b, n) {
    n = n || 5;
    const span = b - a;
    if (!(span > 0) || !isFinite(span)) return { step: 1, values: [] };
    const raw = span / n, mag = Math.pow(10, Math.floor(Math.log10(raw))), norm = raw / mag;
    const cand = [1, 2, 2.5, 5, 10];
    let best = cand[0];
    for (const c of cand) if (Math.abs(c - norm) < Math.abs(best - norm)) best = c;
    const step = best * mag, values = [];
    for (let v = Math.ceil(a / step) * step; v <= b + step * 1e-9; v += step) values.push(Math.round(v / step) * step);
    return { step, values };
  }

  // ==================== 场景状态（params + scalars + 当前步）====================
  function makeState(spec, ctl) {
    const env = Object.assign({}, ctl.params);
    (spec.scalars || []).forEach((s) => { env[s.name] = evalExpr(s.expr, env); });
    const step = (spec.steps && spec.steps[ctl.step]) || {};
    const merged = Object.assign({}, env, step);
    // step 里的字符串也解析（数组/对象深解析，便于 steps 直接写表达式）
    const S = {};
    for (const k in merged) S[k] = resolve(merged[k], env, true);
    S.__env = env;
    S.__step = ctl.step;
    S.__nsteps = spec.steps ? spec.steps.length : 0;
    return S;
  }

  // ==================== 渲染器 ====================
  function Renderer(canvas, spec) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.spec = spec;
    this.theme = spec.theme || "dark";
    this.C = THEMES[this.theme] || THEMES.dark;
    this.view = Object.assign({ xRange: [0, 1], yRange: [0, 1], pad: { l: 58, r: 14, b: 34, t: 16 }, equalAspect: false }, spec.view || {});
    if (spec.equalAspect) this.view.equalAspect = true;
    this.W = 0; this.H = 0; this.scX = 1; this.scY = 1; this.ox = 0; this.oy = 0;
    this._boxes = [];   // 供审计：记录绘制过的图元包围盒
  }
  Renderer.prototype.resize = function () {
    // 容器**边框盒**的高度 = canvas 高 + figbox 的 padding/border。用它当 canvas 高，
    // 再把结果写回 canvas.style.height，就构成正反馈：每次 resize 图都长高一圈，
    // 无上界（实测 314.4 → 328.8 → 343.2 → 357.6，每次 +14.4px）。
    // 同理，宽度要的是容器**内容盒**：直接写 style.width = 边框盒宽度会让 canvas
    // 溢出 figbox 的左右 padding。
    // 因此：宽取内容盒，高取 canvas 自己已声明的 CSS 高度，且**不回写 style.height**。
    const parent = this.canvas.parentElement;
    const pcs = global.getComputedStyle(parent);
    const contentW = parent.clientWidth - (parseFloat(pcs.paddingLeft) || 0)
                                         - (parseFloat(pcs.paddingRight) || 0);
    const declaredH = this.canvas.getBoundingClientRect().height
                   || parent.getBoundingClientRect().height;
    const dpr = Math.min(global.devicePixelRatio || 1, 2);
    const w = Math.max(1, contentW), h = Math.max(1, declaredH);
    this.canvas.width = Math.round(w * dpr);
    this.canvas.height = Math.round(h * dpr);
    this.canvas.style.width = w + "px";
    this.ctx.setTransform(1, 0, 0, 1, 0, 0);
    this.ctx.scale(dpr, dpr);
    // 逻辑尺寸用 CSS 空间（ctx 已按 dpr 缩放，绘制坐标就是 CSS px）。
    // 这里曾经写成 `rect.width/height` —— 一个**从未定义**的变量，于是 resize 每次
    // 都抛 ReferenceError，整张图挂不上去。而 Python 侧的 validate 只查数据、
    // 不跑 JS，所以静态校验一路绿灯 —— 书稿的插图实际上从未在浏览器里渲染成功过。
    this.W = w; this.H = h;
    this.compute();
  };
  Renderer.prototype.compute = function () {
    const v = this.view, p = v.pad;
    const spanX = v.xRange[1] - v.xRange[0], spanY = v.yRange[1] - v.yRange[0];
    let sx = (this.W - p.l - p.r) / spanX, sy = (this.H - p.t - p.b) / spanY;
    if (v.equalAspect) { const s = Math.min(sx, sy); sx = sy = s; }
    this.scX = sx; this.scY = sy;
    if (v.equalAspect) {
      this.ox = p.l + ((this.W - p.l - p.r) - spanX * sx) / 2 - v.xRange[0] * sx;
      this.oy = p.t + ((this.H - p.t - p.b) - spanY * sy) / 2 + spanY * sy + v.yRange[0] * sy;
    } else {
      this.ox = p.l - v.xRange[0] * sx;
      this.oy = (this.H - p.b) + v.yRange[0] * sy;
    }
  };
  Renderer.prototype.X = function (x) { return this.ox + x * this.scX; };
  Renderer.prototype.Y = function (y) { return this.oy - y * this.scY; };
  // 像素方向长度（用于半径/线宽等与比例尺无关的尺寸）
  Renderer.prototype.ux = function (u) { return u * this.scX; };
  Renderer.prototype.uy = function (u) { return u * this.scY; };

  // ==================== 标注层（避让：像素偏移 + 靠边翻转）====================
  Renderer.prototype.annot = function (px, py, text, opt) {
    opt = opt || {};
    T.color = this.C;
    const ctx = this.ctx, c = this.C;
    const size = opt.size || T.font.size.sm, weight = opt.weight || "bold";
    ctx.font = weight + " " + size + "px " + T.font.family;
    const w = ctx.measureText(text).width;
    const align = opt.align || "center";
    let dx = opt.dx || 0, dy = opt.dy == null ? -T.space.md : opt.dy;
    let a = align;
    // 靠边自动翻转：右边缘右对齐、左边缘左对齐、顶底翻到内侧
    if (!opt.noFlip) {
      if (a === "center" || a == null) {
        if (px + w / 2 > this.W - 3) a = "right";
        else if (px - w / 2 < 3) a = "left";
      }
      if (dy < 0 && py + dy < 12) dy = Math.abs(dy) + size;      // 上方放不下 → 放下方
      if (dy > 0 && py + dy > this.H - 4) dy = -(Math.abs(dy) + 4);
    }
    ctx.textAlign = a; ctx.textBaseline = "middle";
    ctx.fillStyle = opt.color || c.text;
    if (opt.halo !== false) {
      ctx.save();
      ctx.lineWidth = 3.2; ctx.strokeStyle = opt.haloColor || c.halo;
      ctx.strokeText(text, px + dx, py + dy);
      ctx.restore();
    }
    ctx.fillText(text, px + dx, py + dy);
    this._boxes.push({ kind: "text", x: px + dx - (a === "center" ? w / 2 : a === "right" ? w : 0), y: py + dy - size / 2, w: w, h: size });
    return { w, h: size, align: a, dx, dy };
  };
  /** 括注（两个值之间的带箭头/端点标记的线段） */
  Renderer.prototype.bracket = function (x1, y1, x2, y2, label, opt) {
    opt = opt || {};
    T.color = this.C;
    const ctx = this.ctx, col = opt.color || this.C.accent;
    const px1 = this.X(x1), py1 = this.Y(y1), px2 = this.X(x2), py2 = this.Y(y2);
    ctx.strokeStyle = col; ctx.lineWidth = opt.width || 2.2;
    ctx.beginPath(); ctx.moveTo(px1, py1); ctx.lineTo(px2, py2); ctx.stroke();
    const tick = opt.tick || 5;
    const along = Math.abs(px2 - px1) > Math.abs(py2 - py1);
    ctx.beginPath();
    if (along) { ctx.moveTo(px1, py1 - tick); ctx.lineTo(px1, py1 + tick); ctx.moveTo(px2, py2 - tick); ctx.lineTo(px2, py2 + tick); }
    else { ctx.moveTo(px1 - tick, py1); ctx.lineTo(px1 + tick, py1); ctx.moveTo(px2 - tick, py2); ctx.lineTo(px2 + tick, py2); }
    ctx.stroke();
    if (label) {
      const mx = (px1 + px2) / 2, my = (py1 + py2) / 2;
      this.annot(mx, my, label, { color: col, size: T.font.size.sm, dx: along ? 0 : 6, dy: along ? -10 : 0, align: along ? "center" : "left" });
    }
    this._boxes.push({ kind: "bracket", x: Math.min(px1, px2), y: Math.min(py1, py2), w: Math.abs(px2 - px1), h: Math.abs(py2 - py1) });
  };

  // ==================== 图元（geoms）====================
  const GEOMS = {};
  const G = (Renderer.prototype.geom = function (g, S) {
    const fn = GEOMS[g.geom];
    if (!fn) { console.warn("viz: 未知图元 " + g.geom); return; }
    T.color = this.C;              // 同步当前主题（canvas 绘制是同步的，多画布也安全）
    fn.call(this, g, S, this);
  });

  // ---- 坐标轴 ----
  GEOMS.axis = function (g) {
    const ctx = this.ctx, c = T.color, v = this.view;
    const xr = g.xRange || v.xRange, yr = g.yRange || v.yRange;
    const ax = this.X(xr[0]), ay = this.Y(yr[0]);
    ctx.strokeStyle = c.axis; ctx.lineWidth = 1.5;
    ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(this.X(xr[1]), ay); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(ax, ay); ctx.lineTo(ax, this.Y(yr[1])); ctx.stroke();
    const xtRaw = g.xticks === false ? [] : (Array.isArray(g.xticks) ? g.xticks : niceTicks(xr[0], xr[1], g.xn || 5));
    const ytRaw = g.yticks === false ? [] : (Array.isArray(g.yticks) ? g.yticks : niceTicks(yr[0], yr[1], g.yn || 5));
    // 注意：数组自带 .values 方法，不能用 xt.values || xt 来判断
    const xs = Array.isArray(xtRaw) ? xtRaw : (xtRaw.values || []);
    const ys = Array.isArray(ytRaw) ? ytRaw : (ytRaw.values || []);
    const xstep = Array.isArray(xtRaw) ? 1 : (xtRaw.step || 1);
    const ystep = Array.isArray(ytRaw) ? 1 : (ytRaw.step || 1);
    ctx.font = "normal " + T.font.size.xs + "px " + T.font.family; ctx.fillStyle = c.dim;
    ctx.textAlign = "center"; ctx.textBaseline = "top";
    xs.forEach((t) => ctx.fillText(g.xfmt ? g.xfmt(t) : fmtTick(t, xstep), this.X(t), ay + 7));
    ctx.textAlign = "right"; ctx.textBaseline = "middle";
    ys.forEach((t) => ctx.fillText(g.yfmt ? g.yfmt(t) : fmtTick(t, ystep), ax - 6, this.Y(t)));
    if (g.xlab) {
      ctx.font = "bold " + T.font.size.sm + "px " + T.font.family;
      ctx.fillStyle = c.dim; ctx.textAlign = "center"; ctx.textBaseline = "top";
      ctx.fillText(g.xlab, (ax + this.X(xr[1])) / 2, ay + T.space.xl);
    }
    if (g.ylab) {
      ctx.save(); ctx.translate(ax - 34, (ay + this.Y(yr[1])) / 2); ctx.rotate(-Math.PI / 2);
      ctx.font = "bold " + T.font.size.sm + "px " + T.font.family;
      ctx.fillStyle = c.dim; ctx.textAlign = "center"; ctx.textBaseline = "bottom";
      ctx.fillText(g.ylab, 0, 0); ctx.restore();
    }
  };

  // ---- 网格线 ----
  GEOMS.grid = function (g) {
    const ctx = this.ctx, v = this.view;
    const xr = g.xRange || v.xRange, yr = g.yRange || v.yRange;
    if (g.x !== false) {
      const xt = Array.isArray(g.xticks) ? g.xticks : niceTicks(xr[0], xr[1], g.xn || 5).values;
      ctx.strokeStyle = g.color || T.color.grid; ctx.lineWidth = 1;
      xt.forEach((t) => { ctx.beginPath(); ctx.moveTo(this.X(t), this.Y(yr[0])); ctx.lineTo(this.X(t), this.Y(yr[1])); ctx.stroke(); });
    }
    if (g.y !== false) {
      const yt = Array.isArray(g.yticks) ? g.yticks : niceTicks(yr[0], yr[1], g.yn || 5).values;
      ctx.strokeStyle = g.color || T.color.grid; ctx.lineWidth = 1;
      yt.forEach((t) => { ctx.beginPath(); ctx.moveTo(this.X(xr[0]), this.Y(t)); ctx.lineTo(this.X(xr[1]), this.Y(t)); ctx.stroke(); });
    }
  };

  // ---- 条形 ----
  GEOMS.bar = function (g, S) {
    const ctx = this.ctx;
    const data = (g.data || []).map((d) => (typeof d === "number" ? { x: 0, y: d } : d));
    const horiz = g.orient === "h";
    data.forEach((d) => {
      const w = (d.w != null ? d.w : (g.width != null ? g.width : T.mark.barW));
      const v = d.y, base = d.base != null ? d.base : (g.baseline != null ? g.baseline : 0);
      let col = d.fill || (g.fillBy ? (g.palette || T.color.ramp)[d[g.fillBy]] : g.fill) || T.color.accent;
      if (typeof col === "function") col = col(d, S);
      ctx.fillStyle = col;
      if (horiz) {
        const x0 = this.X(base), x1 = this.X(v), yc = this.Y(d.y0 != null ? d.y0 : 0);
        const bh = this.uy(w) * 0.5;
        ctx.fillRect(Math.min(x0, x1), yc - bh / 2, Math.abs(x1 - x0), bh);
        this._boxes.push({ kind: "bar", x: Math.min(x0, x1), y: yc - bh / 2, w: Math.abs(x1 - x0), h: bh });
      } else {
        const xc = this.X(d.x), y0 = this.Y(base), y1 = this.Y(v);
        const bw = this.ux(w) * 0.5;
        ctx.fillRect(xc - bw, Math.min(y0, y1), bw * 2, Math.abs(y1 - y0));
        this._boxes.push({ kind: "bar", x: xc - bw, y: Math.min(y0, y1), w: bw * 2, h: Math.abs(y1 - y0) });
      }
      if (d.label && g.labelOpt !== false) {
        const opt = typeof d.label === "object" ? d.label : { text: d.label };
        const px = horiz ? this.X(v) : this.X(d.x), py = horiz ? this.Y(d.y0 != null ? d.y0 : 0) : this.Y(v);
        this.annot(px, py, String(opt.text), { dx: opt.dx != null ? opt.dx : (horiz ? 7 : 0), dy: opt.dy != null ? opt.dy : (horiz ? 0 : -9), align: opt.align || (horiz ? "left" : "center"), color: opt.color, size: opt.size });
      }
    });
  };

  // ---- 折线 / 曲线 ----
  GEOMS.line = function (g, S) {
    const ctx = this.ctx;
    let pts = [];
    if (g.fn) {
      const xr = g.from || this.view.xRange, n = g.n || 240;
      for (let i = 0; i <= n; i++) {
        const x = xr[0] + (xr[1] - xr[0]) * i / n;
        const y = evalExpr(String(g.fn), Object.assign({}, S.__env, { x }));
        if (isFinite(y)) pts.push([x, y]);
      }
    } else {
      pts = (g.data || []).filter((p) => isFinite(p[0]) && isFinite(p[1]));
    }
    if (pts.length < 2) return;
    ctx.strokeStyle = g.stroke || T.color.accent;
    ctx.lineWidth = g.width || T.mark.lineW;
    ctx.lineJoin = "round"; ctx.lineCap = "round";
    ctx.setLineDash(g.dash ? [5, 4] : []);
    ctx.beginPath();
    pts.forEach((p, i) => { i ? ctx.lineTo(this.X(p[0]), this.Y(p[1])) : ctx.moveTo(this.X(p[0]), this.Y(p[1])); });
    ctx.stroke(); ctx.setLineDash([]);
    if (g.area) {
      const base = g.baseline != null ? g.baseline : this.view.yRange[0];
      ctx.lineTo(this.X(pts[pts.length - 1][0]), this.Y(base));
      ctx.lineTo(this.X(pts[0][0]), this.Y(base)); ctx.closePath();
      ctx.fillStyle = g.fill || "rgba(45,212,191,.14)"; ctx.fill();
    }
  };

  // ---- 点 ----
  GEOMS.point = function (g, S) {
    const ctx = this.ctx;
    (g.data || []).forEach((d) => {
      const r = d.r != null ? d.r : (g.r != null ? g.r : T.mark.dotR);
      ctx.fillStyle = d.fill || g.fill || T.color.accent;
      ctx.beginPath(); ctx.arc(this.X(d.x), this.Y(d.y), r, 0, 7); ctx.fill();
      if (d.label) this.annot(this.X(d.x), this.Y(d.y), String(d.label), { dy: -(r + 6), color: d.labelColor || g.labelColor, size: g.labelSize });
    });
  };

  // ---- 节点（树/图/流程）----
  GEOMS.node = function (g, S) {
    const ctx = this.ctx;
    const R = g.r != null ? g.r : T.mark.nodeR;
    (g.data || []).forEach((d) => {
      const px = this.X(d.x), py = this.Y(d.y);
      const on = d.on !== false;
      const fill = typeof d.fill === "function" ? d.fill(d, S) : (d.fill || g.fill || T.color.panel);
      ctx.globalAlpha = on ? 1 : 0.28;
      if (d.shape === "square") {
        ctx.fillStyle = fill; ctx.fillRect(px - R, py - R, R * 2, R * 2);
        ctx.strokeStyle = d.edge || g.edge || T.color.panelEdge; ctx.lineWidth = 1.6;
        ctx.strokeRect(px - R, py - R, R * 2, R * 2);
      } else {
        ctx.beginPath(); ctx.arc(px, py, d.r != null ? d.r : R, 0, 7);
        ctx.fillStyle = fill; ctx.fill();
        ctx.strokeStyle = d.edge || g.edge || T.color.panelEdge; ctx.lineWidth = 1.8; ctx.stroke();
      }
      if (d.text != null) {
        ctx.globalAlpha = on ? 1 : 0.35;
        ctx.font = "bold " + T.font.size.md + "px " + T.font.family;
        ctx.fillStyle = d.textColor || T.color.onFill; ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(String(d.text), px, py);
      }
      ctx.globalAlpha = 1;
      if (d.label) this.annot(px, py, String(d.label), { dy: -(R + 9), color: d.labelColor || g.labelColor || T.color.text, size: g.labelSize || T.font.size.sm });
      this._boxes.push({ kind: "node", x: px - R, y: py - R, w: R * 2, h: R * 2 });
    });
  };

  // ---- 边 ----
  GEOMS.edge = function (g, S) {
    const ctx = this.ctx;
    const at = {};
    (g.nodes || []).forEach((n) => { at[n.id] = n; });
    (g.data || []).forEach((d) => {
      const a = at[d.u] || d.u, b = at[d.v] || d.v;
      if (!a || !b || a.x == null || b.x == null) return;
      let x1 = this.X(a.x), y1 = this.Y(a.y), x2 = this.X(b.x), y2 = this.Y(b.y);
      const R = g.nodeR != null ? g.nodeR : T.mark.nodeR;
      // 缩到节点边缘，避免线压住圆
      const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy) || 1;
      if (g.trim !== false) { x1 += dx / L * R; y1 += dy / L * R; x2 -= dx / L * R; y2 -= dy / L * R; }
      const on = d.on !== false;
      ctx.globalAlpha = on ? 1 : 0.22;
      ctx.strokeStyle = d.color || g.stroke || T.color.panelEdge;
      ctx.lineWidth = d.width || g.width || 1.8;
      ctx.setLineDash(d.dash || g.dash ? [5, 4] : []);
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke(); ctx.setLineDash([]);
      if (g.directed || d.directed) {
        const ang = Math.atan2(y2 - y1, x2 - x1);
        ctx.beginPath();
        ctx.moveTo(x2, y2);
        ctx.lineTo(x2 - 11 * Math.cos(ang - 0.4), y2 - 11 * Math.sin(ang - 0.4));
        ctx.lineTo(x2 - 11 * Math.cos(ang + 0.4), y2 - 11 * Math.sin(ang + 0.4));
        ctx.closePath(); ctx.fillStyle = d.color || g.stroke || T.color.panelEdge; ctx.fill();
      }
      ctx.globalAlpha = 1;
      if (d.w != null && g.showWeight) {
        ctx.font = "bold " + T.font.size.xs + "px " + T.font.family;
        ctx.fillStyle = d.wcolor || T.color.warn; ctx.textAlign = "center"; ctx.textBaseline = "middle";
        ctx.fillText(String(d.w), (x1 + x2) / 2, (y1 + y2) / 2 - 8);
      }
      if (d.label) this.annot((x1 + x2) / 2, (y1 + y2) / 2, String(d.label), { dy: -9, color: d.labelColor || T.color.dim, size: T.font.size.xs });
    });
  };

  // ---- 流程连线（带方向的节点间连线，支持 h/v/vu）----
  GEOMS.arrow = function (g, S) {
    const at = {};
    (g.nodes || []).forEach((n) => { at[n.id] = n; });
    const ctx = this.ctx;
    (g.data || []).forEach((e) => {
      const a = at[e.from], b = at[e.to];
      if (!a || !b) return;
      let x1, y1, x2, y2;
      const dir = e.dir || "h";
      if (dir === "v") { x1 = this.X(a.x + a.w / 2); y1 = this.Y(a.y); x2 = this.X(b.x + b.w / 2); y2 = this.Y(b.y + b.h); }
      else if (dir === "vu") { x1 = this.X(a.x + a.w / 2); y1 = this.Y(a.y + a.h); x2 = this.X(b.x + b.w / 2); y2 = this.Y(b.y); }
      else { x1 = this.X(a.x + a.w); y1 = this.Y(a.y + a.h / 2); x2 = this.X(b.x); y2 = this.Y(b.y + b.h / 2); }
      const on = e.on !== false;
      const col = e.color || g.stroke || T.color.muted;
      ctx.globalAlpha = on ? 1 : 0.3;
      ctx.strokeStyle = col; ctx.lineWidth = e.width || g.width || 1.8;
      ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
      const ang = Math.atan2(y2 - y1, x2 - x1);
      ctx.beginPath();
      ctx.moveTo(x2, y2);
      ctx.lineTo(x2 - 11 * Math.cos(ang - 0.4), y2 - 11 * Math.sin(ang - 0.4));
      ctx.lineTo(x2 - 11 * Math.cos(ang + 0.4), y2 - 11 * Math.sin(ang + 0.4));
      ctx.closePath(); ctx.fillStyle = col; ctx.fill();
      ctx.globalAlpha = 1;
      if (e.label) {
        const mx = dir === "h" ? (x1 + x2) / 2 : x1 + 30, my = dir === "h" ? (y1 + y2) / 2 : (y1 + y2) / 2;
        this.annot(mx, my, String(e.label), { dy: dir === "h" ? -9 : 0, color: e.labelColor || (on ? T.color.good : T.color.dim), size: T.font.size.xs });
      }
    });
  };

  // ---- 流程节点（矩形卡片）----
  GEOMS.card = function (g, S) {
    const ctx = this.ctx;
    (g.data || []).forEach((n) => {
      const x = this.X(n.x), yTop = this.Y(n.y + n.h), w = this.ux(n.w), h = this.uy(n.h);
      const on = n.on !== false;
      ctx.globalAlpha = on ? 1 : 0.5;
      ctx.fillStyle = typeof n.fill === "function" ? n.fill(n, S) : (n.fill || g.fill || T.color.panel);
      ctx.fillRect(x, yTop, w, h);
      ctx.strokeStyle = n.edge || g.edge || (on ? T.color.good : T.color.panelEdge);
      ctx.lineWidth = on ? 2.4 : 1.5;
      ctx.strokeRect(x, yTop, w, h);
      ctx.globalAlpha = 1;
      const hasSub = n.sub != null && n.sub !== "";
      ctx.font = (on ? "bold " : "") + T.font.size.md + "px " + T.font.family;
      ctx.fillStyle = T.color.text; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(String(n.label), x + w / 2, yTop + h / 2 + (hasSub ? -6 : 0));
      if (hasSub) {
        ctx.font = T.font.size.xs + "px " + T.font.family; ctx.fillStyle = T.color.dim;
        ctx.fillText(String(n.sub), x + w / 2, yTop + h / 2 + 10);
      }
      this._boxes.push({ kind: "card", x, y: yTop, w, h, id: n.id, on, label: n.label });
    });
  };

  // ---- 高亮区域 / 嵌套框 ----
  GEOMS.region = function (g, S) {
    const ctx = this.ctx;
    const x0 = this.X(g.x[0]), x1 = this.X(g.x[1]);
    const y0 = g.y ? this.Y(g.y[0]) : 0, y1 = g.y ? this.Y(g.y[1]) : this.H;
    const X = Math.min(x0, x1), Y = Math.min(y0, y1), W = Math.abs(x1 - x0), H = Math.abs(y1 - y0);
    if (g.fill) { ctx.fillStyle = g.fill; ctx.fillRect(X, Y, W, H); }
    if (g.outline || g.stroke) {
      ctx.strokeStyle = g.stroke || T.color.accent;
      ctx.lineWidth = g.width || 1.6;
      ctx.setLineDash(g.dash ? [6, 4] : []);
      ctx.strokeRect(X, Y, W, H);
      ctx.setLineDash([]);
    }
    if (g.label) this.annot((x0 + x1) / 2, g.labelY != null ? this.Y(g.labelY) : (y0 + y1) / 2, g.label, { color: g.labelColor, size: g.labelSize });
  };

  // ---- 文字（世界坐标定位，支持 \n 换行；引擎负责靠边翻转）----
  // 注意：text 的内容**默认原样显示**，不做表达式求值——因为 "1/2"、"-3"、"(a)" 这类
  // 数学标签极其常见，自动求值会把它们变成 0.5、-3、NaN。要动态文本请显式写 expr:true。
  GEOMS.text = function (g, S) {
    const px = this.X(resolve(g.x, S)), py = this.Y(resolve(g.y, S));
    const raw = g.expr ? String(resolve(g.text, S)) : String(g.text == null ? "" : g.text);
    const lines = raw.split("\n");
    const size = g.size != null ? g.size : T.font.size.sm;
    const lh = g.lineHeight != null ? g.lineHeight : size * 1.45;
    const total = (lines.length - 1) * lh;
    const align = g.align || "left";
    if (lines.length === 1) {
      this.annot(px, py, lines[0], { align: align, size: size, color: g.color, dx: g.dx || 0, dy: g.dy == null ? 0 : g.dy, weight: g.weight, halo: g.halo });
    } else {
      lines.forEach((ln, i) => {
        const yy = py - total / 2 + i * lh + (g.dy || 0);
        this.annot(px, yy, ln, { align: align, size: size, color: g.color, dx: g.dx || 0, dy: 0, weight: g.weight, halo: g.halo, noFlip: i > 0 });
      });
    }
  };

  // ---- 矩阵 / 表格（DP 表、哈希桶、棋盘格）----
  GEOMS.matrix = function (g, S) {
    const ctx = this.ctx;
    const vals = g.values || [];
    const nr = g.rows != null ? g.rows : vals.length;
    const nc = g.cols != null ? g.cols : (vals[0] ? vals[0].length : 0);
    const cw = g.cellW != null ? g.cellW : 1, ch = g.cellH != null ? g.cellH : 1;
    const ox = g.origin ? g.origin[0] : 0, oy = g.origin ? g.origin[1] : 0;
    const hl = g.highlight || [];
    const same = (a, b) => a && b && a[0] === b[0] && a[1] === b[1];
    for (let r = 0; r < nr; r++) {
      for (let c = 0; c < nc; c++) {
        const x = this.X(ox + c * cw), yTop = this.Y(oy + (nr - r) * ch);
        const w = this.ux(cw), h = this.uy(ch);
        const on = hl.some((q) => same(q, [r, c]));
        const v = (vals[r] || [])[c];
        ctx.fillStyle = on ? (g.hlFill || "rgba(45,212,191,.28)") : (g.cellFill || T.color.panel);
        ctx.fillRect(x, yTop, w, h);
        ctx.strokeStyle = on ? (g.hlEdge || T.color.accent) : (g.cellEdge || T.color.panelEdge);
        ctx.lineWidth = on ? 2.2 : 1;
        ctx.strokeRect(x, yTop, w, h);
        if (v != null && v !== "") {
          ctx.font = (on ? "bold " : "") + T.font.size.sm + "px " + T.font.family;
          ctx.fillStyle = on ? "#ffffff" : (g.textColor || T.color.text);
          ctx.textAlign = "center"; ctx.textBaseline = "middle";
          ctx.fillText(String(v), x + w / 2, yTop + h / 2);
        }
        this._boxes.push({ kind: "cell", x, y: yTop, w, h });
      }
    }
    // 表头
    const hf = g.fontSize || T.font.size.xs;
    ctx.font = "bold " + hf + "px " + T.font.family; ctx.fillStyle = T.color.dim;
    (g.colHeaders || []).forEach((t, c) => {
      ctx.textAlign = "center"; ctx.textBaseline = "bottom";
      ctx.fillText(String(t), this.X(ox + (c + 0.5) * cw), this.Y(oy + nr * ch) - 3);
    });
    (g.rowHeaders || []).forEach((t, r) => {
      ctx.textAlign = "right"; ctx.textBaseline = "middle";
      ctx.fillText(String(t), this.X(ox) - 4, this.Y(oy + (nr - r - 0.5) * ch));
    });
  };

  // ---- 位/小方块（位运算、比特、格子图）----
  GEOMS.glyph = function (g, S) {
    const ctx = this.ctx;
    const size = g.size != null ? g.size : 0.6;
    (g.data || []).forEach((d) => {
      const x = this.X(d.x + (1 - size) / 2), yTop = this.Y(d.y + size);
      const w = this.ux(size), h = this.uy(size);
      const on = d.on !== false;
      let fill = d.fill || g.fill || T.color.panel;
      if (g.fillBy && d[g.fillBy] != null) fill = (g.palette || T.color.series)[d[g.fillBy] % (g.palette || T.color.series).length];
      ctx.fillStyle = on ? fill : "rgba(100,116,139,.25)";
      if (d.shape === "circle") { ctx.beginPath(); ctx.arc(x + w / 2, yTop + h / 2, Math.min(w, h) / 2, 0, 7); ctx.fill(); }
      else ctx.fillRect(x, yTop, w, h);
      if (g.stroke !== false) {
        ctx.strokeStyle = g.edge || T.color.panelEdge; ctx.lineWidth = 1;
        if (d.shape === "circle") { ctx.beginPath(); ctx.arc(x + w / 2, yTop + h / 2, Math.min(w, h) / 2, 0, 7); ctx.stroke(); }
        else ctx.strokeRect(x, yTop, w, h);
      }
      if (d.label != null) this.annot(x + w / 2, yTop + h / 2, String(d.label), { dy: 0, size: g.fontSize || T.font.size.sm, color: g.labelColor || T.color.onFill, halo: false });
      this._boxes.push({ kind: "glyph", x, y: yTop, w, h });
    });
  };

  // ---- 时间轴 ----
  GEOMS.timeline = function (g, S) {
    const ctx = this.ctx;
    const y = g.y != null ? g.y : 0;
    const ev = (g.data || []).slice().sort((a, b) => a.t - b.t);
    ctx.strokeStyle = g.axis || T.color.axis; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(this.X(g.tRange[0]), this.Y(y)); ctx.lineTo(this.X(g.tRange[1]), this.Y(y)); ctx.stroke();
    ev.forEach((e, i) => {
      const px = this.X(e.t), py = this.Y(y);
      ctx.fillStyle = e.fill || (g.palette || T.color.series)[i % (g.palette || T.color.series).length];
      ctx.beginPath(); ctx.arc(px, py, 6, 0, 7); ctx.fill();
      const up = e.side !== "down";
      this.annot(px, py, e.label, { dy: up ? -(T.space.xl) : T.space.xl, align: "center", color: T.color.text, size: T.font.size.sm });
      ctx.strokeStyle = T.color.panelEdge; ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(px, py + (up ? -6 : 6)); ctx.lineTo(px, py + (up ? -14 : 14)); ctx.stroke();
    });
  };

  // ---- 步进条形（排序/查找的数组）----
  // data: [{v, i}]，g.state = {cmp:[i,j], swap:[i,j], sorted:[..], pivot:i, range:[lo,hi], found:i, mid:i}
  GEOMS.array = function (g, S) {
    const ctx = this.ctx;
    const st = g.state || {};
    const items = g.data || [];
    const maxV = Math.max(1, ...items.map((d) => d.v));
    const base = g.baseline != null ? g.baseline : 0;
    const has = (id, list) => Array.isArray(list) && list.includes(id);
    items.forEach((d, i) => {
      const v = d.v;
      let col = g.fill || T.color.neutral;
      if (g.colorOf) col = g.colorOf(i, v, st, S);
      const x = this.X(g.origin ? g.origin[0] + i * (g.step || 1) : i * (g.step || 1));
      const w = this.ux((g.barW != null ? g.barW : 0.72) * (g.step || 1));
      const y0 = this.Y(base), y1 = this.Y(v);
      ctx.fillStyle = col;
      ctx.fillRect(x - w / 2, Math.min(y0, y1), w, Math.abs(y1 - y0));
      // 数值
      ctx.font = "bold " + T.font.size.sm + "px " + T.font.family;
      ctx.fillStyle = T.color.onFill; ctx.textAlign = "center"; ctx.textBaseline = "top";
      ctx.fillText(String(v), x, Math.min(y0, y1) - 15);
      // 下标
      ctx.font = T.font.size.xs + "px " + T.font.family; ctx.fillStyle = T.color.dim;
      ctx.textBaseline = "top";
      ctx.fillText(String(i), x, y0 + 5);
      this._boxes.push({ kind: "abar", x: x - w / 2, y: Math.min(y0, y1), w, h: Math.abs(y1 - y0) });
    });
    // 指针（i / j / mid / lo / hi）
    const ptrs = g.pointers || {};
    Object.keys(ptrs).forEach((name) => {
      const idx = ptrs[name];
      if (idx == null || idx < 0 || idx >= items.length) return;
      const x = this.X(g.origin ? g.origin[0] + idx * (g.step || 1) : idx * (g.step || 1));
      const y0 = this.Y(base);
      this.annot(x, y0 + 22, name, { dy: 0, color: g.pointerColor || T.color.warn, size: T.font.size.sm });
    });
  };

  // ---- 一维容器（栈 / 队列 / 链表）----
  // data: [{id, val, next}]，g.mode: 'stack' | 'queue' | 'list'
  GEOMS.linear = function (g, S) {
    const ctx = this.ctx;
    const items = g.data || [];
    const cw = g.cellW != null ? g.cellW : 1, chh = g.cellH != null ? g.cellH : 0.7;
    const oy = g.y != null ? g.y : 0.5;
    const hl = g.highlight || [];
    const vert = g.mode === "stack";
    items.forEach((d, i) => {
      const x = this.X((g.origin ? g.origin[0] : 0) + (vert ? 0 : i * cw));
      const yTop = this.Y(oy + (vert ? (i + 1) * chh : chh));
      const w = this.ux(cw), h = this.uy(chh);
      const on = hl.includes(i) || hl.includes(d.id);
      ctx.fillStyle = on ? (g.hlFill || "rgba(45,212,191,.30)") : (g.fill || T.color.panel);
      ctx.fillRect(x, yTop, w, h);
      ctx.strokeStyle = on ? T.color.accent : T.color.panelEdge; ctx.lineWidth = on ? 2.2 : 1.2;
      ctx.strokeRect(x, yTop, w, h);
      ctx.font = "bold " + T.font.size.md + "px " + T.font.family;
      ctx.fillStyle = T.color.text; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText(String(d.val != null ? d.val : d), x + w / 2, yTop + h / 2);
      if (g.showIndex) this.annot(x + w / 2, yTop + h, String(i), { dy: 12, size: T.font.size.xs, color: T.color.dim });
      this._boxes.push({ kind: "cell", x, y: yTop, w, h });
    });
    // 链表 next 指针
    if (g.mode === "list") {
      const byId = {}; items.forEach((d, i) => { byId[d.id] = i; });
      ctx.strokeStyle = T.color.accent2; ctx.lineWidth = 1.6;
      items.forEach((d, i) => {
        if (d.next == null) return;
        const j = byId[d.next]; if (j == null) return;
        const x1 = this.X((g.origin ? g.origin[0] : 0) + (i + 1) * cw), x2 = this.X((g.origin ? g.origin[0] : 0) + j * cw);
        const y = this.Y(oy + chh * 1.5);
        ctx.beginPath(); ctx.moveTo(x1, y); ctx.lineTo(x2, y); ctx.stroke();
      });
    }
  };

  // 统一绘制入口（mount 与 audit 共用；audit 也能正确应用主题）
  Renderer.prototype.drawScene = function (S) {
    T.color = this.C;
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.W, this.H);
    this._boxes = [];
    ctx.fillStyle = this.spec.bg || this.C.bg;
    ctx.fillRect(0, 0, this.W, this.H);
    (this.spec.layers || []).forEach((g) => {
      if (g.when != null) {
        // when 可以是函数，也可以是声明式条件表达式（如 "k >= 3"），后者可 JSON 序列化
        const ok = typeof g.when === "function" ? g.when(S) : !!evalExpr(String(g.when), S);
        if (!ok) return;
      }
      this.geom(g, S);
    });
    if (this.spec.onRender) this.spec.onRender(this, S);
  };

  // ==================== 挂载 / 交互 ====================
  function mount(canvas, spec) {
    const r = new Renderer(canvas, spec);
    const ctl = { params: {}, step: 0, spec: spec };
    (spec.params || []).forEach((p) => { ctl.params[p.name] = p.value; });

    r.render = function () {
      const S = makeState(spec, ctl);
      if (spec.steps) {
        // 允许步骤里改写视图范围
        const sv = spec.steps[ctl.step] || {};
        if (sv.__view) { Object.assign(r.view, sv.__view); r.compute(); }
        if (sv.__viewReset) { Object.assign(r.view, spec.view || {}); if (spec.equalAspect) r.view.equalAspect = true; r.compute(); }
      }
      r.drawScene(S);
    };
    r.setStep = function (i) { ctl.step = Math.max(0, Math.min((spec.steps ? spec.steps.length : 1) - 1, i)); r.render(); return ctl.step; };
    r.setParam = function (name, v) { ctl.params[name] = v; r.render(); };
    r.state = function () { return makeState(spec, ctl); };
    r.stepCount = function () { return spec.steps ? spec.steps.length : 1; };
    r.currentStep = function () { return ctl.step; };

    const onResize = () => { r.resize(); r.render(); };
    r.resize(); r.render();
    global.addEventListener("resize", onResize);
    r.destroy = () => global.removeEventListener("resize", onResize);
    return r;
  }

  // ==================== 控制台（共享 UI：滑块 + 读数 + 状态灯 + 定值）====================
  function consoleUI(el, spec, viz) {
    const theme = THEMES[spec.theme || viz.theme || "dark"] || THEMES.dark;
    const esc = (s) => String(s == null ? "" : s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
    const wrap = document.createElement("div");
    wrap.innerHTML = (spec.params || []).map((p) => `
      <div class="viz-param">
        <div class="viz-param-head"><span>${esc(p.label || p.name)}</span><span class="viz-pv" id="viz-pv-${p.name}"></span></div>
        <input type="range" id="viz-ps-${p.name}" min="${p.min}" max="${p.max}" step="${p.step || 0.01}" value="${p.value}">
        <div class="viz-param-range"><span>${p.min}${esc(p.unit || "")}</span><span>${p.max}${esc(p.unit || "")}</span></div>
      </div>`).join("")
      + (spec.readouts || []).map((r) => r.highlight
        ? `<div class="viz-rd viz-rd-hl"><span>${esc(r.label)}</span><span id="viz-ro-${r.id}">—</span></div>`
        : `<div class="viz-rd"><span>${esc(r.label)}</span><span id="viz-ro-${r.id}" style="color:${r.color || theme.text}">—</span></div>`).join("")
      + (spec.constant ? `<div class="viz-const"><span>定值指示</span><span id="viz-const">${esc(spec.constant.label || "")}</span></div>` : "");
    el.innerHTML = ""; el.appendChild(wrap);

    function refresh() {
      const S = viz.state();
      (spec.params || []).forEach((p) => {
        const e = document.getElementById("viz-pv-" + p.name);
        if (e) e.textContent = fmt(ctlVal(p), p.digits != null ? p.digits : 2) + (p.unit || "");
      });
      (spec.readouts || []).forEach((rd) => {
        const e = document.getElementById("viz-ro-" + rd.id);
        if (!e) return;
        try {
          if (rd.type === "text") { e.textContent = String(rd.value == null ? "" : resolve(rd.value, S)); return; }
          if (rd.type === "status") {
            const v = evalExpr(rd.expr, S), rhs = rd.rhs != null ? rd.rhs : 0, op = rd.op || ">";
            const ok = op === "<" ? v < rhs - 1e-9 : op === ">" ? v > rhs + 1e-9
              : op === "==" ? Math.abs(v - rhs) < 1e-6 : op === "<=" ? v <= rhs + 1e-9 : v >= rhs - 1e-9;
            e.textContent = ok ? (rd.okText || "满足") : (rd.badText || "不满足");
            e.style.color = ok ? theme.ok : theme.err;
            return;
          }
          const v = evalExpr(rd.expr, S);
          e.textContent = (rd.int ? fmtInt(v) : fmt(v, rd.digits != null ? rd.digits : 2)) + (rd.unit ? " " + rd.unit : "");
        } catch (err) { e.textContent = "—"; }
      });
    }
    function ctlVal(p) { return viz.state()[p.name]; }
    (spec.params || []).forEach((p) => {
      const s = document.getElementById("viz-ps-" + p.name);
      if (s) s.addEventListener("input", () => { viz.setParam(p.name, parseFloat(s.value)); refresh(); if (spec.onChange) spec.onChange(parseFloat(s.value), p.name, viz); });
    });
    refresh();
    return { refresh, reset() { (spec.params || []).forEach((p) => { const s = document.getElementById("viz-ps-" + p.name); if (s) { s.value = p.value; } viz.setParam(p.name, p.value); }); refresh(); } };
  }

  // ==================== 审计（可离线跑，供自检/CI）====================
  function audit(canvas, spec) {
    const r = new Renderer(canvas, spec);
    r.resize();
    const params = {};
    (spec.params || []).forEach((p) => { params[p.name] = p.value; });
    r.drawScene(makeState(spec, { params: params, step: 0 }));
    const out = { width: r.W, height: r.H, overflow: [], outside: [], nodesOutside: 0 };
    r._boxes.forEach((b) => {
      if (b.x < -1 || b.y < -1 || b.x + b.w > r.W + 1 || b.y + b.h > r.H + 1) {
        out.overflow.push({ kind: b.kind, x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.w), h: Math.round(b.h) });
      }
    });
    // 卡片类节点是否落在视图内（世界坐标检查）
    (spec.layers || []).forEach((g) => {
      if (g.geom === "card") (g.data || []).forEach((n) => {
        if (n.x < r.view.xRange[0] - 1e-6 || n.x + n.w > r.view.xRange[1] + 1e-6 ||
            n.y < r.view.yRange[0] - 1e-6 || n.y + n.h > r.view.yRange[1] + 1e-6) {
          out.outside.push({ id: n.id, x: n.x, y: n.y, w: n.w, h: n.h });
        }
      });
    });
    out.ok = out.overflow.length === 0 && out.outside.length === 0;
    return out;
  }

  // ==================== 导出 ====================
  global.Viz = {
    T, THEMES, mount, consoleUI, audit, niceTicks, fmt, fmtInt, fmtTick, evalExpr, resolve,
    geoms: GEOMS, version: "1.0.0",
  };
})(typeof window !== "undefined" ? window : globalThis);
