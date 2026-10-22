# -*- coding: utf-8 -*-
"""
vizkit.py — 图形语法的「构造 DSL + 校验器」（同时给人、agent 与 CI 使用）。

为什么要有它
------------
直接让 AI 手写 viz spec 的 JSON，字段名容易拼错、坐标容易出框、表达式容易引错变量。
本模块把「写图」变成**调用有签名的构造函数**，并在**构造后立即校验**：

    import vizkit as vk
    spec = vk.spec(view=[0, 14, 1.5, 3.9], layers=[
        vk.axis(xlab="年", ylab="资金"),
        vk.line(fn="P*(1+r)^t", from_=[0, 30], stroke=vk.PAPER.accent),
        vk.text(0.5, 3.4, "复利：时间是朋友还是敌人"),
    ], theme="paper")
    rep = vk.validate(spec)          # → Report(ok=True/False, errors=[...], warnings=[...])
    if not rep.ok: print(rep.format())

校验回路（agent 的标准用法）
--------------------------
    生成 spec → validate → 有 error 就按 report 里的 fix 提示重生成 → 直到 ok
    `python vizkit.py check spec.json` 也可直接跑（退出码可入 CI）。

校验项（都是实际踩过的坑）
------------------------
  E1 顶层结构：view / layers / theme 是否合法
  E2 图元名未知
  E3 图元必填字段缺失或类型不对
  E4 表达式引用了未定义的变量（params / scalars / steps / 内置之外）
  E5 世界坐标越界（card / node / region / point 超出 view，或卡片互相压住）
  E6 文本溢出画布（按字符宽度估算）
  W1 同一水平带上的文本互相遮挡（标签堆叠）
  W2 该用 equalAspect 的场景没用（棋盘格/坐标图会变形）
  W3 steps 缺少 note
"""
import json
import math
import re
import sys

# =====================================================================
# 一、主题令牌（与 viz.js 的 THEMES 保持一致）
# =====================================================================
class Palette:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def get(self, name, default=None):
        return getattr(self, name, default)

    def __getitem__(self, name):
        return getattr(self, name)


# 深色：解题器的画板
DARK = Palette(
    bg="#0f172a", panel="#1e293b", panelEdge="#334155", axis="#94a3b8", grid="#334155",
    text="#e2e8f0", dim="#94a3b8", muted="#64748b", onFill="#f1f5f9", halo="rgba(15,23,42,.82)",
    accent="#2dd4bf", accent2="#a78bfa", good="#10b981", warn="#f59e0b", bad="#ef4444",
    series=["#2dd4bf", "#a78bfa", "#f59e0b", "#60a5fa", "#f472b6", "#34d399", "#fb923c"],
    ramp=["#166534", "#15803d", "#22c55e", "#86efac"],
)

# 浅色：书的插图（纸感、印刷友好）
PAPER = Palette(
    bg="#ffffff", panel="#f7f4ee", panelEdge="#d8d2c6", axis="#8a8177", grid="#ece7de",
    text="#1f1b16", dim="#7d756a", muted="#a89f92", onFill="#1f1b16", halo="rgba(255,255,255,.9)",
    accent="#b45309", accent2="#6d28d9", good="#15803d", warn="#b45309", bad="#b91c1c",
    series=["#b45309", "#6d28d9", "#0f766e", "#1d4ed8", "#be123c", "#4d7c0f", "#c2410c"],
    ramp=["#14532d", "#15803d", "#65a30d", "#bef264"],
)

THEMES = {"dark": DARK, "paper": PAPER}

# =====================================================================
# 二、表达式：变量名提取（与 viz.js 的白名单保持一致）
# =====================================================================
KNOWN_FUNCS = {"sqrt", "abs", "min", "max", "pow", "sign", "floor", "ceil", "round",
               "log", "log2", "log10", "exp", "sinh", "cosh"}
KNOWN_CONSTS = {"PI", "E", "true", "false", "null", "undefined"}
# 「看起来像表达式」才求值（与 viz.js 的 resolve 规则一致）：纯 ASCII 符号串
EXPR_RE = re.compile(r"^[\s\dA-Za-z_+\-*/().^,%<>=!?:|&]*$")
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def looks_like_expr(s):
    return isinstance(s, str) and bool(EXPR_RE.match(s)) and bool(IDENT_RE.search(s) or re.search(r"\d", s))


def expr_identifiers(s):
    if not isinstance(s, str):
        return set()
    return {m.group(0) for m in IDENT_RE.finditer(s)}


# =====================================================================
# 三、构造器（图层）
# =====================================================================
GEOM_NAMES = {"axis", "grid", "bar", "line", "point", "node", "edge", "arrow",
              "card", "region", "text", "matrix", "glyph", "timeline", "array", "linear"}

KNOWN_FIELDS = {  # 每个图元的「已知字段」，未知字段会告警（拼错字段名的兜底）
    "axis": {"geom", "xRange", "yRange", "xticks", "yticks", "xlab", "ylab", "xn", "yn", "xfmt", "yfmt", "when"},
    "grid": {"geom", "xRange", "yRange", "xticks", "yticks", "xn", "yn", "x", "y", "color", "when"},
    "bar": {"geom", "data", "width", "fill", "fillBy", "palette", "baseline", "orient", "labelOpt", "when"},
    "line": {"geom", "fn", "from", "n", "data", "stroke", "width", "dash", "area", "fill", "baseline", "when"},
    "point": {"geom", "data", "r", "fill", "labelColor", "labelSize", "when"},
    "node": {"geom", "data", "r", "fill", "edge", "labelColor", "labelSize", "when"},
    "edge": {"geom", "data", "nodes", "stroke", "width", "directed", "dash", "trim", "nodeR",
             "showWeight", "when"},
    "arrow": {"geom", "data", "nodes", "stroke", "width", "when"},
    "card": {"geom", "data", "fill", "edge", "when"},
    "region": {"geom", "x", "y", "fill", "outline", "stroke", "width", "dash", "label",
               "labelY", "labelColor", "labelSize", "when"},
    "text": {"geom", "x", "y", "text", "align", "size", "color", "dx", "dy", "weight",
             "lineHeight", "halo", "when", "expr"},
    "matrix": {"geom", "values", "rows", "cols", "cellW", "cellH", "origin", "highlight",
               "cellFill", "cellEdge", "hlFill", "hlEdge", "textColor", "colHeaders",
               "rowHeaders", "fontSize", "when"},
    "glyph": {"geom", "data", "size", "fill", "fillBy", "palette", "edge", "stroke",
              "fontSize", "labelColor", "when"},
    "timeline": {"geom", "data", "tRange", "y", "axis", "palette", "when"},
    "array": {"geom", "data", "origin", "step", "barW", "shape", "fill", "colorOf", "pointers",
              "pointerColor", "baseline", "state", "when"},
    "linear": {"geom", "data", "mode", "origin", "y", "cellW", "cellH", "highlight",
               "hlFill", "fill", "showIndex", "when"},
}

# `data` 数组里**每个元素**允许的字段。来源是 viz.js 里各 GEOMS 函数实际读的
# `d.xxx` —— 不是猜的。拼错一个字段名（`x` 写成 `xcoord`）的后果很隐蔽：渲染器
# 读到 undefined，那个点直接不画（或画到 NaN），图还在、只是少了个东西，看图发现
# 不了。图层级的 KNOWN_FIELDS 抓不到这种情况，因为它只看顶层键。
DATA_FIELDS = {
    "point":    {"x", "y", "r", "fill", "label", "labelColor"},
    "node":     {"x", "y", "r", "fill", "edge", "on", "shape", "text", "textColor",
                 "label", "labelColor"},
    "edge":     {"u", "v", "on", "color", "width", "dash", "directed", "w", "wcolor",
                 "label", "labelColor"},
    "arrow":    {"from", "to", "dir", "on", "color", "width"},
    "card":     {"id", "x", "y", "w", "h", "label", "sub", "edge", "fill", "on"},
    "glyph":    {"x", "y", "shape", "on", "fill", "label"},
    "bar":      {"x", "y", "w", "base", "y0", "fill", "label"},
    "timeline": {"t", "label", "fill", "side"},
    "array":    {"v"},
    "linear":   {"id", "val", "next"},
}

REQUIRED = {
    "axis": [], "grid": [],
    "bar": ["data"], "line": ["fn|data"], "point": ["data"],
    "node": ["data"], "edge": ["data"], "arrow": ["data", "nodes"], "card": ["data"],
    "region": ["x", "y"], "text": ["x", "y", "text"],
    "matrix": [], "glyph": ["data"], "timeline": ["data", "tRange"], "array": ["data"], "linear": ["data"],
}


def _clean(d):
    return {k: v for k, v in d.items() if v is not None}


def layer(geom, when=None, **kw):
    assert geom in GEOM_NAMES, f"未知图元 {geom}；可用：{sorted(GEOM_NAMES)}"
    d = {"geom": geom}
    d.update(_clean(kw))
    if when is not None and when is not True:
        d["when"] = when
    return d


def axis(when=None, **kw): return layer("axis", when, **kw)
def grid(when=None, **kw): return layer("grid", when, **kw)
def bar(when=None, **kw): return layer("bar", when, **kw)
def point(when=None, **kw): return layer("point", when, **kw)
def node(when=None, **kw): return layer("node", when, **kw)
def edge(when=None, **kw): return layer("edge", when, **kw)
def arrow(when=None, **kw): return layer("arrow", when, **kw)
def card(when=None, **kw): return layer("card", when, **kw)
def region(when=None, **kw): return layer("region", when, **kw)
def matrix(when=None, **kw): return layer("matrix", when, **kw)
def glyph(when=None, **kw): return layer("glyph", when, **kw)
def timeline(when=None, **kw): return layer("timeline", when, **kw)
def array(when=None, **kw): return layer("array", when, **kw)
def linear(when=None, **kw): return layer("linear", when, **kw)


def text(x, y, t, align="left", size=None, color=None, dx=0, dy=0, weight="bold",
         when=None, expr=False, **kw):
    """文字图层。t 默认**原样显示**（"1/2"、"-3" 不会被当表达式）；要动态文本写 expr=True。"""
    return layer("text", when, x=x, y=y, text=t, align=align, size=size,
                 color=color, dx=dx, dy=dy, weight=weight,
                 expr=(True if expr else None), **kw)


def line(when=None, **kw):
    if "from_" in kw:
        kw["from"] = kw.pop("from_")
    kw.pop("from_", None)
    return layer("line", when, **kw)


def card_item(x, y, w, h, label, sub=None, edge=None, fill=None, id=None, on=True):
    """构一张流程卡片（card 图元的 data 元素）。"""
    d = {"id": id or f"c{abs(hash((x, y, label))) % 100000}", "x": x, "y": y, "w": w, "h": h,
         "label": label, "sub": sub, "on": on}
    if edge is not None:
        d["edge"] = edge
    if fill is not None:
        d["fill"] = fill
    return d


def node_item(id, x, y, label=None, on=True, **kw):
    d = {"id": id, "x": x, "y": y, "on": on}
    if label is not None:
        d["label"] = label
    d.update(kw)
    return d


def step(note, **kw):
    """一步（steps 元素）：note 是必填的同学能看懂的一句话。"""
    d = {"note": note}
    d.update(kw)
    return d


def steps(*notes_or_dicts):
    out = []
    for i, s in enumerate(notes_or_dicts):
        if isinstance(s, dict):
            s.setdefault("k", i + 1)
            out.append(s)
        else:
            out.append({"k": i + 1, "note": str(s)})
    return out


def when(k):
    """按步骤序号显示的条件表达式（第 k 步及之后可见）。"""
    return f"k >= {k}"


# =====================================================================
# 四、顶层 spec
# =====================================================================
def spec(layers, view, theme="dark", steps_=None, params=None, scalars=None,
         readouts=None, equal_aspect=False, bg=None, title=None):
    """
    view: [x0, x1, y0, y1] 或 {"xRange":[...], "yRange":[...], ...}
    """
    if isinstance(view, (list, tuple)):
        assert len(view) == 4, "view 用 [x0, x1, y0, y1] 四元组"
        v = {"xRange": [view[0], view[1]], "yRange": [view[2], view[3]]}
    else:
        v = dict(view)
    if equal_aspect:
        v["equalAspect"] = True
    out = {"theme": theme, "view": v, "layers": list(layers)}
    if steps_:
        out["steps"] = list(steps_)
    if params:
        out["params"] = list(params)
    if scalars:
        out["scalars"] = list(scalars)
    if readouts:
        out["readouts"] = list(readouts)
    if bg:
        out["bg"] = bg
    if title:
        out["title"] = title
    return out


# =====================================================================
# 五、校验器
# =====================================================================
CHA_WIDTH = 1.0      # 中文字符宽度 / 字号
ASCII_WIDTH = 0.56   # ASCII 字符宽度 / 字号

# 书页里 canvas 的**真实**内容宽度（CSS 像素）。这个数不是估的，是量出来的：
#   page.html  的 <main class="max-w-[720px]"> 减去它自己的左右 padding，
#   figure .figbox 再减去左右 padding 9.6px 与 1px 边框 → 693.8。
# 早先这里写 783（"正文列宽"），宽了 13%，等于所有越界/重叠检查都在一个比
# 真实画布宽 13% 的虚拟画布上做 —— 只会漏报，不会报错，所以长期没人发现。
# 校验口径必须跟着实测走：改了页面版式就改这个数，并用 check_output.py 复量。
PAGE_CANVAS_W = 693.8


def est_text_width(s, size):
    """按**最宽的一行**估宽。

    多行标签（含 `\\n`）若把所有字符加在一起算，等于把两行叠成一行，宽度会翻倍。
    图上的标注大多是两行（年代 / 事件），所以这不是边角情况：fig-timeline 的
    「公元前 6 世纪\\n发现 √2 不可通约」被算成 147px，真值约 78px —— 于是 E6 报
    文本冲出左边界，而实际留白还有 20 多像素。
    """
    best = 0.0
    for line in str(s).split("\n"):
        w = 0.0
        for ch in line:
            w += (CHA_WIDTH if ord(ch) > 0x2E80 else ASCII_WIDTH) * size
        best = max(best, w)
    return best


# ---- when 条件的互斥判定（W1 用）----
# viz.js 的 drawScene 逐层门控：`when` 为假时**整层不画**（viz.js:719-721）。
# 所以两个互斥门控的文本永远不会同屏，把它们报成「同一水平带互相遮挡」是假阳性。
# 这里只认**闭区间**写法（== / >= / <=），认不出的一律当作「可能同屏」——
# 宁可多报一条，也不放过真的遮挡。
_WHEN_RE = re.compile(r"^\s*k\s*(==|>=|<=)\s*(-?\d+(?:\.\d+)?)\s*$")


def _when_span(w):
    """把 when 条件解析成 k 的闭区间 (lo, hi)；None 表示「认不出」。

    区间端点为 None 表示该侧无界。空条件 = 永远可见，由 _when_exclusive 先处理。
    """
    if not isinstance(w, str):
        return None
    m = _WHEN_RE.match(w)
    if not m:
        return None
    op, v = m.group(1), float(m.group(2))
    if op == "==":
        return (v, v)
    if op == ">=":
        return (v, None)
    return (None, v)          # "<="


def _when_exclusive(a, b):
    """两个 when 条件是否**不可能同时成立**（于是两层不会同屏）。

    认不出的写法返回 False（保守：照旧参与遮挡检测）。
    """
    if a is None or b is None:
        return False                      # 任一层永远可见
    sa, sb = _when_span(a), _when_span(b)
    if sa is None or sb is None:
        return False
    (la, ha), (lb, hb) = sa, sb
    lo = la if lb is None else (lb if la is None else max(la, lb))
    hi = ha if hb is None else (hb if ha is None else min(ha, hb))
    if lo is None or hi is None:
        return False                      # 至少一侧无界 → 必有交集
    return lo > hi


class Report:
    def __init__(self):
        self.errors = []
        self.warnings = []
        # 本校验器**没能读懂**的输入。与 errors 的区别：
        # errors = 读懂了，而且它是错的；
        # unread = 根本没读懂，于是「没有报错」不代表「它是对的」。
        # 不把这两件事分开，读者会把「0 错误」当成「全对」——而残缺模型上的
        # 几何检查恰恰最容易给出这种假的安全感。
        self.unread = []

    def err(self, code, where, msg, fix=""):
        self.errors.append({"code": code, "where": where, "msg": msg, "fix": fix})

    def warn(self, code, where, msg, fix=""):
        self.warnings.append({"code": code, "where": where, "msg": msg, "fix": fix})

    def blind(self, where, why):
        """记一处「读不懂」。不参与 ok 判定，但必须出现在报告里。"""
        self.unread.append({"where": where, "why": why})

    @property
    def ok(self):
        return not self.errors

    def format(self):
        if self.ok and not self.warnings and not self.unread:
            return "✓ 校验通过（无错误、无警告）"
        lines = []
        for e in self.errors:
            lines.append(f"[ERROR {e['code']}] {e['where']}: {e['msg']}")
            if e["fix"]:
                lines.append(f"        ↳ 修法：{e['fix']}")
        for w in self.warnings:
            lines.append(f"[WARN  {w['code']}] {w['where']}: {w['msg']}")
            if w["fix"]:
                lines.append(f"        ↳ 修法：{w['fix']}")
        if self.unread:
            lines.append(f"[BLIND     ] {len(self.unread)} 处未能解析 —— "
                         f"下面的检查结论**不覆盖**这些地方：")
            for u in self.unread:
                lines.append(f"        · {u['where']}: {u['why']}")
        return "\n".join(lines)

    def to_dict(self):
        return {"ok": self.ok, "errors": self.errors,
                "warnings": self.warnings, "unread": self.unread}


def _ident_ctx(spec_):
    """收集表达式里允许出现的标识符：参数名 + 标量名 + 各步的键 + 内置。"""
    ok = set(KNOWN_FUNCS) | KNOWN_CONSTS | {"x"}
    for p in spec_.get("params") or []:
        if p.get("name"):
            ok.add(p["name"])
    for s in spec_.get("scalars") or []:
        if s.get("name"):
            ok.add(s["name"])
    for st in spec_.get("steps") or []:
        for k in st:
            if not k.startswith("__"):
                ok.add(k)
    return ok


def _check_expr(r, expr, where, allowed):
    if not looks_like_expr(expr):
        return
    unknown = expr_identifiers(expr) - allowed
    if unknown:
        r.err("E4", where,
              f"表达式 {expr!r} 引用了未定义的变量：{', '.join(sorted(unknown))}",
              f"把变量加进 params/scalars 或 steps，或改用这些已知名：{', '.join(sorted(allowed - KNOWN_FUNCS - KNOWN_CONSTS)[:8])}…")


def _pix(v, spec_):
    """把 view 换算成像素函数（与 viz.js 的 Renderer.compute 一致）。"""
    W = v.get("W", 800)
    H = v.get("H", 350)
    # 用来评估文本是否溢出时，需要画布尺寸；validate 会传进来
    return W, H


def validate(spec_, W=PAGE_CANVAS_W, H=350):
    # W/H 是预期的画布像素尺寸。默认宽度取实测的书页 canvas 宽（PAGE_CANVAS_W），
    # 而不是随手写的 800 —— 校验口径必须等于真实渲染口径，否则只会漏报不会报错。
    # 本仓库按 W=800、H=350 校验过的图，在真实宽度 693.8 下立刻多出 2 处溢出。
    r = Report()
    if not isinstance(spec_, dict):
        r.err("E1", "spec", "spec 必须是对象", "用 vizkit.spec(...) 构造")
        return r
    theme = spec_.get("theme", "dark")
    if theme not in THEMES:
        r.err("E1", "spec.theme", f"未知主题 {theme!r}", f"可用：{list(THEMES)}")
    view = spec_.get("view")
    if not isinstance(view, dict) or "xRange" not in view or "yRange" not in view:
        r.err("E1", "spec.view", "缺少 view.xRange / view.yRange", "view=[x0,x1,y0,y1]")
        return r
    xr, yr = view["xRange"], view["yRange"]
    if not (isinstance(xr, list) and len(xr) == 2 and xr[1] > xr[0]):
        r.err("E1", "spec.view.xRange", f"xRange 非法：{xr}", "写成递增的 [x0, x1]")
    if not (isinstance(yr, list) and len(yr) == 2 and yr[1] > yr[0]):
        r.err("E1", "spec.view.yRange", f"yRange 非法：{yr}", "写成递增的 [y0, y1]")
    if not r.ok:
        return r
    pad = view.get("pad") or {"l": 58, "r": 14, "b": 34, "t": 16}
    spanx, spany = xr[1] - xr[0], yr[1] - yr[0]
    sx = (W - pad.get("l", 58) - pad.get("r", 14)) / spanx
    sy = (H - pad.get("t", 16) - pad.get("b", 34)) / spany
    if view.get("equalAspect"):
        s = min(sx, sy); sx = sy = s
    if view.get("equalAspect"):
        # 与 viz.js `compute()` 的 equalAspect 分支逐字对齐：等比时两个方向都富余，
        # 富余量要**居中**分掉。漏掉这个居中偏移，所有等比图的坐标映射都会系统性
        # 偏移（宽图偏、窄图不偏），底下的越界/重叠判断就都建在错的坐标上。
        ox = pad.get("l", 58) + ((W - pad.get("l", 58) - pad.get("r", 14)) - spanx * sx) / 2 - xr[0] * sx
        oy = pad.get("t", 16) + ((H - pad.get("t", 16) - pad.get("b", 34)) - spany * sy) / 2 \
             + spany * sy + yr[0] * sy
    else:
        ox = pad.get("l", 58) - xr[0] * sx
        oy = (H - pad.get("b", 34)) + yr[0] * sy
    X = lambda x: ox + x * sx
    Y = lambda y: oy - y * sy

    allowed = _ident_ctx(spec_)
    layers = spec_.get("layers")
    if not isinstance(layers, list) or not layers:
        r.err("E1", "spec.layers", "layers 必须是非空数组", "至少放一个图元")
        return r

    texts = []           # 收集文本位置，做遮挡检测
    cardboxes = []       # 收集卡片，做互相压住检测

    for i, g in enumerate(layers):
        where = f"layers[{i}]"
        if not isinstance(g, dict) or "geom" not in g:
            r.err("E2", where, "图层缺少 geom 字段", "每层都要有 geom")
            r.blind(where, "整层无法识别（缺 geom），本层完全不参与几何检查")
            continue
        geom = g["geom"]
        if geom not in GEOM_NAMES:
            r.err("E2", where, f"未知图元 {geom!r}", f"可用：{sorted(GEOM_NAMES)}")
            r.blind(where, f"图元 {geom!r} 不认识，本层完全不参与几何检查")
            continue
        where = f"layers[{i}]({geom})"
        # 未知字段（拼错兜底）
        unknown = set(g) - KNOWN_FIELDS.get(geom, set())
        if unknown:
            r.warn("E3", where, f"未知字段：{', '.join(sorted(unknown))}",
                   "检查是否把字段名拼错（未知字段会被 viz.js 忽略）")
            # 拼错的字段往往正是坐标/标签所在的那个字段：viz.js 会忽略它，
            # 于是图照画，但画出来的不是作者以为的样子。这种地方必须记进
            # 「未解析」，否则下面的越界/重叠检查是在缺了一块的模型上做结论。
            r.blind(where, f"字段 {', '.join(sorted(unknown))} 不在白名单内，"
                           f"本图元的几何检查不覆盖这些值")
        # data 元素里的未知字段（同上的元素级版本）
        known_item = DATA_FIELDS.get(geom)
        items = g.get("data")
        if known_item is not None and isinstance(items, list):
            for j, d in enumerate(items):
                if not isinstance(d, dict):
                    continue
                extra = set(d) - known_item
                # glyph 支持 fillBy 动态取键（d[g.fillBy]），那个键是合法的
                if geom == "glyph" and isinstance(g.get("fillBy"), str):
                    extra.discard(g["fillBy"])
                if extra:
                    r.warn("E3", f"{where}.data[{j}]",
                           f"元素含未知字段：{', '.join(sorted(extra))}",
                           "检查拼写（渲染器会把未知字段读成 undefined，元素直接不画）")
                    r.blind(f"{where}.data[{j}]",
                            f"字段 {', '.join(sorted(extra))} 渲染器不会读取，"
                            f"该元素参与几何检查时结论不完整")
        # 必填
        for fld in REQUIRED.get(geom, []):
            if "|" in fld:
                if not any(k in g for k in fld.split("|")):
                    r.err("E3", where, f"缺少必填字段：{fld}", "补上该字段")
            elif fld not in g:
                r.err("E3", where, f"缺少必填字段：{fld}", "补上该字段")
        # 表达式校验
        if g.get("when") is not None:
            _check_expr(r, g["when"], where + ".when", allowed)
        if geom == "line" and g.get("fn"):
            _check_expr(r, g["fn"], where + ".fn", allowed | {"x"})
        if geom == "text" and g.get("expr"):
            _check_expr(r, g["text"], where + ".text(expr)", allowed)
        for fld in ("fill", "stroke", "color", "edge"):
            if fld in g:
                _check_expr(r, g[fld], where + f".{fld}", allowed)
        if geom == "bar" and isinstance(g.get("data"), list):
            for d in g["data"]:
                if isinstance(d, dict):
                    for k in ("x", "y", "w", "base"):
                        if k in d:
                            _check_expr(r, d[k], where + f".data.{k}", allowed)

        # ---- 几何越界 ----
        def chk_pt(x, y, tag):
            try:
                px, py = X(float(x)), Y(float(y))
            except Exception:
                # 坐标不是数（字符串、None、NaN 字符串…）就换算不出来。
                # 以前这里静默 return，等于「算不出来的点默认合法」。
                r.blind(where + tag, f"坐标 ({x!r}, {y!r}) 无法换算成像素，未做越界检查")
                return
            if px < -2 or px > W + 2 or py < -2 or py > H + 2:
                r.err("E5", where + tag,
                      f"世界坐标 ({x}, {y}) 落在画布外（像素 {px:.0f},{py:.0f}）",
                      "调整坐标，或把 view 的范围放宽")

        if geom == "card":
            CARD_FIELDS = {"id", "x", "y", "w", "h", "label", "sub", "edge", "fill", "on", "textColor"}
            for d in g.get("data") or []:
                if not isinstance(d, dict):
                    continue
                badf = set(d) - CARD_FIELDS
                if badf:
                    r.warn("E3", where + f"[{d.get('id')}]",
                           f"card 元素里有未知字段：{', '.join(sorted(badf))}",
                           "检查字段名是否拼错（未知字段会被忽略）")
                if not all(k in d for k in ("x", "y", "w", "h", "label")):
                    r.err("E3", where, f"card 元素缺字段：{d}", "需要 x/y/w/h/label")
                    continue
                if d["x"] < xr[0] - 1e-9 or d["x"] + d["w"] > xr[1] + 1e-9 \
                   or d["y"] < yr[0] - 1e-9 or d["y"] + d["h"] > yr[1] + 1e-9:
                    r.err("E5", where + f"[{d.get('id')}]",
                          f"卡片超出 view：x∈[{d['x']},{d['x']+d['w']}] y∈[{d['y']},{d['y']+d['h']}]，"
                          f"view x∈{xr} y∈{yr}",
                          "缩小卡片或放宽 view")
                cardboxes.append((i, d))
                # 文案是否装得下
                need = est_text_width(d.get("label", ""), 12)
                avail = d["w"] * sx - 10
                if need > avail * 1.6:
                    r.warn("E6", where + f"[{d.get('id')}]",
                           f"卡片标题估宽 {need:.0f}px 远超卡片宽 {avail:.0f}px，可能溢出",
                           "缩短文字、加宽卡片，或把细节写进正文")
        elif geom == "node":
            for d in g.get("data") or []:
                if isinstance(d, dict) and "x" in d:
                    chk_pt(d["x"], d["y"], f"[{d.get('id')}]")
        elif geom == "point":
            for d in g.get("data") or []:
                if isinstance(d, dict) and "x" in d:
                    chk_pt(d["x"], d["y"], "")
        elif geom == "region":
            xs, ys = g.get("x"), g.get("y")
            if isinstance(xs, list) and isinstance(ys, list) and len(xs) == 2 and len(ys) == 2:
                for xx, yy in [(xs[0], ys[0]), (xs[1], ys[1])]:
                    chk_pt(xx, yy, "")
            if isinstance(xs, list) and len(xs) == 2 and (xs[0] < xr[0] or xs[1] > xr[1]):
                r.err("E5", where, f"区域 x∈{xs} 超出 view x∈{xr}", "放宽 view 或收窄区域")
        elif geom == "axis":
            # 轴名是 axis 图元自己画的（不是 text 图层），也要登记进来做遮挡检测
            xr2 = g.get("xRange") or xr
            yr2 = g.get("yRange") or yr
            if g.get("xlab"):
                wpx = est_text_width(g["xlab"], 11)
                px = (X(xr2[0]) + X(xr2[1])) / 2
                py = Y(yr2[0]) + 22
                texts.append({"i": i, "t": "[轴名] " + str(g["xlab"]), "l": px - wpx / 2,
                              "r": px + wpx / 2, "y": py, "h": 11, "where": where + ".xlab"})
            if g.get("ylab"):
                # 纵轴名是旋转的竖排文字：单独登记为一块竖条，只与同区域的文本冲突
                wpx = est_text_width(g["ylab"], 11)
                texts.append({"i": i, "t": "[轴名] " + str(g["ylab"]), "l": X(xr2[0]) - 44,
                              "r": X(xr2[0]) - 24, "y": (Y(yr2[0]) + Y(yr2[1])) / 2,
                              "h": wpx, "where": where + ".ylab"})
        elif geom == "text":
            tx, ty = g.get("x"), g.get("y")
            if isinstance(tx, (int, float)) and isinstance(ty, (int, float)):
                size = g.get("size") or 11
                wpx = est_text_width(g.get("text", ""), size)
                px, py = X(tx), Y(ty)
                align = g.get("align", "left")
                left = px if align == "left" else (px - wpx / 2 if align == "center" else px - wpx)
                right = left + wpx
                if left < pad.get("l", 58) * 0.2 or right > W - 3 or py < 3 or py > H - 3:
                    r.err("E6", where,
                          f"文本 {str(g.get('text'))[:18]!r} 估宽 {wpx:.0f}px，"
                          f"横向占 [{left:.0f},{right:.0f}]，画布宽 {W}",
                          "缩短文字 / 换行 \\n / 调整 x 或对齐方式 / 放宽 view")
                texts.append({"i": i, "t": str(g.get("text", "")), "l": left, "r": right,
                              "y": py, "h": size, "where": where})
        elif geom == "glyph":
            gs = g.get("size") or 0.6
            for d in g.get("data") or []:
                if isinstance(d, dict) and "x" in d:
                    # 检查方块的**完整外框**（左下角 + 尺寸），而不是中心
                    chk_pt(d["x"], d["y"], "")
                    chk_pt(d["x"] + gs, d["y"] + gs, "")
        elif geom == "timeline":
            for d in g.get("data") or []:
                if isinstance(d, dict) and "t" in d:
                    chk_pt(d["t"], g.get("y", 0), "")

    # ---- W1 文本遮挡（同一水平带且横向重叠）----
    for a in range(len(texts)):
        for b in range(a + 1, len(texts)):
            A, B = texts[a], texts[b]
            # 两层由 when 互斥 → 永远不会同屏，不构成遮挡（viz.js 逐层门控）
            if A["i"] != B["i"] and _when_exclusive(layers[A["i"]].get("when"),
                                                    layers[B["i"]].get("when")):
                continue
            if abs(A["y"] - B["y"]) > max(A["h"], B["h"]) * 0.7:
                continue
            ov = min(A["r"], B["r"]) - max(A["l"], B["l"])
            if ov > 6:
                r.warn("W1", f"{A['where']} ⇄ {B['where']}",
                       f"两处文本在同一水平带重叠约 {ov:.0f}px：{A['t'][:14]!r} / {B['t'][:14]!r}",
                       "错开 y（上下分层）或错开 x；不要用同心布局放标签")

    # ---- W2 需要等比例却没开 ----
    if not view.get("equalAspect"):
        keys = {"card", "glyph", "matrix"}
        if any(g.get("geom") in ("glyph", "matrix") for g in layers):
            r.warn("W2", "spec.view", "含 glyph/matrix（方块类）但未设 equalAspect，方块会被拉成长方形",
                   "spec(..., equal_aspect=True)")

    # ---- W3 steps 缺 note ----
    for j, st in enumerate(spec_.get("steps") or []):
        if not isinstance(st, dict) or not st.get("note"):
            r.warn("W3", f"steps[{j}]", "该步没有 note，读者看不到这一步在讲什么",
                   "每步都写一句 note")

    return r


# =====================================================================
# 六、补丁引擎（与书页里的 applyOps 同语义）
# =====================================================================
def _split_path(path):
    return [int(p) if p.lstrip("-").isdigit() else p for p in str(path).split("/") if p != ""]


def get_at(obj, path):
    cur = obj
    for k in _split_path(path):
        cur = cur[k]
    return cur


def set_at(obj, path, value):
    parts = _split_path(path)
    if not parts:
        raise ValueError("空路径")
    cur = obj
    for k in parts[:-1]:
        cur = cur[k]
    cur[parts[-1]] = value
    return obj


def del_at(obj, path):
    parts = _split_path(path)
    cur = obj
    for k in parts[:-1]:
        cur = cur[k]
    del cur[parts[-1]]
    return obj


def append_at(obj, path, value):
    get_at(obj, path).append(value)
    return obj


def apply_ops(spec_, ops):
    """
    对 spec 施加一组补丁操作（不改原对象）。

    op 的形态：
      {"path": "layers/3/data/0/label", "value": "新标题"}          # 改（默认）
      {"path": "layers", "op": "append", "value": {图层}}            # 往数组末尾追加
      {"path": "layers/5", "op": "delete"}                          # 删除
    路径用 `/` 分隔，数字段表示数组下标。
    """
    import copy
    out = copy.deepcopy(spec_)
    for i, op in enumerate(ops):
        if not isinstance(op, dict) or "path" not in op:
            raise ValueError(f"ops[{i}] 非法：需要 {{path, value?}}")
        kind = op.get("op", "set")
        try:
            if kind == "set":
                set_at(out, op["path"], op.get("value"))
            elif kind == "append":
                append_at(out, op["path"], op.get("value"))
            elif kind == "delete":
                del_at(out, op["path"])
            else:
                raise ValueError(f"未知操作 {kind!r}（可用 set/append/delete）")
        except Exception as e:
            raise ValueError(f"ops[{i}] path={op.get('path')!r}（{kind}）应用失败：{e}") from None
    return out


def apply_patch(specs, patch):
    """
    对「多图集合」施加一份补丁包：
      {"figure": "fig-crisis", "ops": [ ... ], "note": "改了什么"}
      或 {"figure": "...", "spec": {全量新 spec}, "note": "整图替换"}
    返回 (新集合, 报告)。
    """
    out = {k: v for k, v in specs.items()}
    fid = patch.get("figure")
    if fid not in out:
        return out, Report_with_err(f"补丁指向不存在的图：{fid!r}")
    if "spec" in patch:
        out[fid] = patch["spec"]
    elif "ops" in patch:
        out[fid] = apply_ops(out[fid], patch["ops"])
    else:
        return out, Report_with_err(f"补丁 {fid!r} 既没有 spec 也没有 ops")
    return out, None


def Report_with_err(msg):
    r = Report()
    r.err("P1", "patch", msg, "检查 figure 名与 patch 结构")
    return r


def validate_patch(specs, patch, W=PAGE_CANVAS_W, H=300):
    """施加补丁 → 校验结果 spec。返回 (新集合, 报告)。出错时集合保持原样。"""
    try:
        new_specs, err = apply_patch(specs, patch)
    except Exception as e:
        return specs, Report_with_err(f"补丁应用失败：{e}")
    if err is not None:
        return specs, err
    rep = validate(new_specs[patch["figure"]], W, H)
    return new_specs, rep


def patch_selftest():
    VIEW = [0, 10, 0, 10]
    base = spec(view=VIEW, theme="paper", layers=[
        text(1, 5, "标题"),
        card(data=[{"id": "a", "x": 1, "y": 1, "w": 2, "h": 1, "label": "A"}]),
    ])
    cases = []
    # 1) 改文字
    p1 = apply_ops(base, [{"path": "layers/0/text", "value": "改过的标题"}])
    cases.append((p1["layers"][0]["text"] == "改过的标题", "set 改文字"))
    # 2) 改嵌套字段
    p2 = apply_ops(base, [{"path": "layers/1/data/0/label", "value": "B"}])
    cases.append((p2["layers"][1]["data"][0]["label"] == "B", "set 改嵌套字段"))
    # 3) 追加图层
    p3 = apply_ops(base, [{"path": "layers", "op": "append",
                           "value": {"geom": "point", "data": [{"x": 5, "y": 5}]}}])
    cases.append((len(p3["layers"]) == 3, "append 追加图层"))
    # 4) 删除图层
    p4 = apply_ops(base, [{"path": "layers/0", "op": "delete"}])
    cases.append((len(p4["layers"]) == 1, "delete 删除图层"))
    # 5) 原对象不被改动
    cases.append((base["layers"][0]["text"] == "标题", "不改动原 spec"))
    # 6) 改完仍是合法 spec
    p5 = apply_ops(base, [{"path": "layers/1/data/0/w", "value": 4}])
    cases.append((validate(p5, 800, 350).ok, "补丁后仍合法"))
    # 7) 补丁把图画坏 → 校验必须抓到
    p6 = apply_ops(base, [{"path": "layers/1/data/0/x", "value": 9.5}])
    cases.append((not validate(p6, 800, 350).ok, "坏补丁能被抓到（E5）"))
    # 8) 指向不存在的图
    _, err = apply_patch({}, {"figure": "nope", "ops": []})
    cases.append((err is not None and not err.ok, "不存在的图名会报错"))

    bad = [c for c in cases if not c[0]]
    for ok, name in cases:
        print(f"  {'✓' if ok else '✗'} {name}")
    print(f"\n{'补丁引擎自测通过 ✓' if not bad else f'{len(bad)} 项失败'}")
    return 1 if bad else 0


# =====================================================================
# 七、自测：故意造错，验证校验器真的能抓到（防止"永远说 OK"）
# =====================================================================
def selftest():
    def codes(rep):
        return {e["code"] for e in rep.errors} | {w["code"] for w in rep.warnings}

    cases = []

    def case(name, spec_, want):
        rep = validate(spec_, W=800, H=350)
        got = codes(rep)
        ok = want in got
        cases.append((ok, name, want, sorted(got)))

    VIEW = [0, 10, 0, 10]

    # E2 未知图元
    case("未知图元", {"theme": "paper", "view": {"xRange": [0, 10], "yRange": [0, 10]},
                     "layers": [{"geom": "triangel", "x": 1}]}, "E2")
    # E3 缺必填字段
    case("缺必填字段", {"theme": "paper", "view": {"xRange": [0, 10], "yRange": [0, 10]},
                        "layers": [{"geom": "text", "x": 1, "y": 1}]}, "E3")
    # E4 表达式引用了未定义变量
    case("未定义变量", {"theme": "paper", "view": {"xRange": [0, 10], "yRange": [0, 10]},
                        "layers": [{"geom": "card", "when": "stepIdx >= 2",
                                    "data": [{"id": "a", "x": 1, "y": 1, "w": 2, "h": 1, "label": "A"}]}]}, "E4")
    # E5 卡片超出 view
    case("卡片越界", {"theme": "paper", "view": {"xRange": [0, 10], "yRange": [0, 10]},
                      "layers": [{"geom": "card",
                                  "data": [{"id": "a", "x": 9, "y": 1, "w": 4, "h": 1, "label": "A"}]}]}, "E5")
    # E6 文本溢出（放在右边缘，必然出框）
    case("文本溢出", {"theme": "paper", "view": {"xRange": [0, 10], "yRange": [0, 10]},
                      "layers": [{"geom": "text", "x": 9.6, "y": 5,
                                  "text": "这一段说明文字放在最右边，必然冲出画布右边缘"}]}, "E6")
    # W1 文本重叠
    case("文本重叠", {"theme": "paper", "view": {"xRange": [0, 10], "yRange": [0, 10]},
                      "layers": [{"geom": "text", "x": 5, "y": 5, "text": "标签甲甲乙"},
                                 {"geom": "text", "x": 5.05, "y": 5.02, "text": "标签丙丁戊"}]}, "W1")

    # W1 的 when 门控：viz.js 逐层门控，互斥的两层永不同屏 —— 报成遮挡就是假阳性。
    # 必须**两边都测**：互斥的不报（否则假阳性淹没真问题），同屏的照报
    # （否则等于把 W1 关掉）。
    def _two(w1, w2):
        lay = [{"geom": "text", "x": 5, "y": 5, "text": "标签甲甲乙"},
               {"geom": "text", "x": 5.05, "y": 5.02, "text": "标签丙丁戊"}]
        for L, w in zip(lay, (w1, w2)):
            if w is not None:
                L["when"] = w
        return validate({"theme": "paper", "view": {"xRange": [0, 10], "yRange": [0, 10]},
                         "layers": lay,
                         "steps": [{"k": 1, "note": "a"}, {"k": 2, "note": "b"},
                                   {"k": 3, "note": "c"}]}, W=800, H=350)

    rep_ex = _two("k == 1", "k == 2")
    cases.append(("W1" not in codes(rep_ex) and rep_ex.ok, "互斥步骤的文本不算遮挡",
                  "无 W1", sorted(codes(rep_ex))))
    rep_co = _two("k >= 1", "k >= 2")
    cases.append(("W1" in codes(rep_co), "同屏的文本照样报 W1",
                  "W1", sorted(codes(rep_co))))
    rep_mix = _two("k >= 2", "k == 1")
    cases.append(("W1" not in codes(rep_mix), "k>=2 与 k==1 判为互斥",
                  "无 W1", sorted(codes(rep_mix))))
    rep_unk = _two("k >= 1 && k <= 3", "k == 2")
    cases.append(("W1" in codes(rep_unk), "认不出的 when 仍参与遮挡检测（保守）",
                  "W1", sorted(codes(rep_unk))))
    # W2 方块类没开等比例
    case("缺 equalAspect", {"theme": "paper", "view": {"xRange": [0, 10], "yRange": [0, 10]},
                            "layers": [{"geom": "glyph", "data": [{"x": 1, "y": 1}]}]}, "W2")
    # W3 步骤缺 note
    case("步骤缺 note", {"theme": "paper", "view": {"xRange": [0, 10], "yRange": [0, 10]},
                         "layers": [{"geom": "text", "x": 1, "y": 1, "text": "x"}],
                         "steps": [{"k": 1}]}, "W3")

    # B1/B2 「读不懂」必须留痕。以前两类都静默通过：元素字段拼错没人管，
    # 坐标不是数就 except 掉 —— 于是「0 错误」被当成「全对」。
    rep_typo = validate({"theme": "paper", "view": {"xRange": [0, 10], "yRange": [0, 10]},
                         "layers": [{"geom": "point", "data": [{"xcoord": 5, "y": 5}]}]},
                        W=800, H=350)
    cases.append((len(rep_typo.unread) >= 1, "元素字段拼错应记入 unread",
                  "unread≥1", f"unread={len(rep_typo.unread)}"))
    rep_badpt = validate({"theme": "paper", "view": {"xRange": [0, 10], "yRange": [0, 10]},
                          "layers": [{"geom": "point", "data": [{"x": "oops", "y": 5}]}]},
                         W=800, H=350)
    cases.append((len(rep_badpt.unread) >= 1, "非数值坐标应记入 unread",
                  "unread≥1", f"unread={len(rep_badpt.unread)}"))

    # 反向用例：一份完全合法的 spec 必须 ok
    good = spec(
        view=[0, 10, 0, 6],
        theme="paper",
        layers=[axis(xlab="时间", ylab="数量"),
                line(fn="100*x", from_=[0, 10], stroke=PAPER.accent),
                text(0.4, 5.4, "增长曲线")],
        steps_=[step("起点"), step("上升")],
    )
    rep_good = validate(good, W=800, H=350)
    cases.append((rep_good.ok and not rep_good.warnings and not rep_good.unread,
                  "合法 spec 应通过（含0警告）", "ok", rep_good.format()[:60]))

    bad = [c for c in cases if not c[0]]
    for ok, name, want, got in cases:
        print(f"  {'✓' if ok else '✗'} {name:22s} 期望 {want:3s}  实得 {got}")
    print(f"\n{'校验器自测通过 ✓' if not bad else f'{len(bad)} 项失败'}")
    return 1 if bad else 0


# =====================================================================
# 七、CLI：python vizkit.py check spec.json
# =====================================================================
def _main(argv):
    if not argv or argv[0] not in ("check", "schema", "selftest", "patch", "patchtest"):
        print("用法:")
        print("  python vizkit.py selftest                      # 自测校验器（8 类错误）")
        print("  python vizkit.py patchtest                     # 自测补丁引擎")
        print("  python vizkit.py schema                        # 打印图元清单")
        print("  python vizkit.py check <spec.json> [W H]       # 校验一份（或多份）spec")
        print("  python vizkit.py patch <spec.json> <patch.json> [out.json]")
        print("                                                 # 施加补丁并校验")
        return 0
    if argv[0] == "patchtest":
        return patch_selftest()
    if argv[0] == "patch":
        spec_ = json.loads(open(argv[1], encoding="utf-8-sig").read())
        patch = json.loads(open(argv[2], encoding="utf-8-sig").read())
        specs = spec_ if "layers" not in spec_ else {patch.get("figure", "_"): spec_}
        new, rep = validate_patch(specs, patch)
        if rep is not None and not rep.ok:
            print("❌ 补丁未通过校验，已拒绝：")
            print(rep.format())
            return 1
        result = new[patch["figure"]] if len(new) == 1 else new
        txt = json.dumps(result, ensure_ascii=False, indent=2)
        if len(argv) > 3:
            open(argv[3], "w", encoding="utf-8-sig").write(txt)
            print(f"written: {argv[3]}（补丁已通过校验）")
        else:
            print(txt)
        return 0
    if argv[0] == "selftest":
        return selftest()
    if argv[0] == "schema":
        for name in sorted(GEOM_NAMES):
            need = REQUIRED.get(name) or []
            print(f"  {name:9s} 必填: {', '.join(need) if need else '—'}")
        return 0
    path = argv[1]
    spec_ = json.loads(open(path, encoding="utf-8-sig").read())
    W = int(argv[2]) if len(argv) > 2 else 800
    H = int(argv[3]) if len(argv) > 3 else 350
    if "layers" in spec_:
        reps = {path: validate(spec_, W, H)}
    else:                                   # 多图文件
        reps = {k: validate(v, W, H) for k, v in spec_.items()}
    bad = 0
    for k, rep in reps.items():
        print(f"— {k}: " + ("OK" if rep.ok else "FAIL"))
        if not rep.ok or rep.warnings:
            print(rep.format())
        if not rep.ok:
            bad += 1
    print(f"\n{'全部通过 ✓' if bad == 0 else f'{bad} 个失败'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
