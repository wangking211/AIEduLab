#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_geometry.py —— 几何 lint（viz spec 层的第二道版式闸门）。

`vizkit.validate` 已经管住：越界点、卡片出界、文本溢出画布、文本互压、
equalAspect、steps 缺 note。这份 lint 补的是**它明确漏掉的那几类**：

    G1  非有限坐标（NaN / ±Inf）——validate 的 `px < -2 or px > W+2` 在
        NaN 下全部为假，于是**静默通过**。一个算错的坐标就这样进了产物。
    G2  line / arrow / edge 的**端点**根本不做越界检查（validate 只对
        card / region / node / point / glyph / timeline 做），一条画出画布
        外的连线不会被任何人发现。
    G3  卡片互相压住——validate 第 445 行把 cardboxes 收集起来，**然后
        从未使用**。收集了不用，等于这道检查只是"看起来做了"。
    G4  文本压在**实心图元**上（W1 只比文本↔文本，标签盖住节点/卡片这种
        最刺眼的遮挡反而不查）。只查 node 与 card：刻度值本来就要压在自己
        的点上，把 point 也算进来只会全是误报。
    G5  **同一帧**画在同一坐标的标记。分步 buildup 会把同一个锚点在互斥的
        帧各画一遍（k==1 / k==2 / k>=3），那不是重叠 —— 所以先代入 k 求值
        判定两个 when 是否真的可共存，共存才报。

    python edulab/tools/check_geometry.py           # 闸门（错误即非零）
    python edulab/tools/check_geometry.py -v        # 连警告一起打印

退出码可入 CI。范围 = `vizkit` 语法覆盖的产物（书稿全部插图）；
其它技能的画板不走 vizkit 语法，由 check_output.py 从**产物**那一侧兜底。
"""

import json
import math
import operator
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
BOOK = ROOT / "edulab" / "books" / "math-thought"
sys.path.insert(0, str(ROOT / "edulab" / "shared" / "viz"))
sys.path.insert(0, str(BOOK))

import vizkit as vk          # noqa: E402
import figures as FIGS       # noqa: E402

PAGE_CANVAS_W = vk.PAGE_CANVAS_W            # 书页 canvas 真实内容宽度（实测，单一真源在 vizkit）


def figure_sizes():
    """从章节 JSON 里取每个图的高度。"""
    sizes = {}
    for p in sorted((BOOK / "chapters").glob("*.json")):
        ch = json.loads(p.read_text(encoding="utf-8-sig"))
        for b in ch.get("blocks", []):
            if b.get("type") == "figure":
                sizes[b["id"]] = int(b.get("height") or 300)
    return sizes


# ---------------------------------------------------------------- helpers

def finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


WHEN_RE = re.compile(r"^k\s*(==|!=|>=|<=|>|<)\s*(-?\d+)$")
_WHEN_OPS = {"==": operator.eq, "!=": operator.ne, ">=": operator.ge,
             "<=": operator.le, ">": operator.gt, "<": operator.lt}


def _steps_max(spec_):
    """图的总步数 kmax（steps 可能是整数，也可能是步骤数组）。"""
    st = spec_.get("steps")
    if isinstance(st, int):
        return max(0, st)
    if isinstance(st, list):
        ks = [b.get("k") for b in st if isinstance(b, dict) and isinstance(b.get("k"), int)]
        return max(ks) if ks else max(0, len(st))
    return 24


def _when_pred(expr):
    """把 'k >= 3' 之类的层可见性谓词变成可调用；解析不了返回 None。"""
    if expr is None:
        return lambda k: True
    m = WHEN_RE.match(str(expr).strip())
    if not m:
        return None
    op, n = _WHEN_OPS[m.group(1)], int(m.group(2))
    return lambda k: op(k, n)


def _coexist(when_a, when_b, kmax):
    """两个 when 在 0..kmax 内是否存在同一个 k 使它们同时为真。

    任一谓词解析不了就**保守当作共存**（宁可报出来让人看一眼，也不静默放过）。
    """
    fa, fb = _when_pred(when_a), _when_pred(when_b)
    if fa is None or fb is None:
        return True
    return any(fa(k) and fb(k) for k in range(0, kmax + 1))


def walk_numbers(obj, path="", out=None, skip=()):
    """递归收集 (路径, 数值)，跳过指定字段名（size/stroke 等允许非坐标用途）。"""
    if out is None:
        out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in skip:
                continue
            walk_numbers(v, f"{path}.{k}" if path else k, out, skip)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            walk_numbers(v, f"{path}[{i}]", out, skip)
    elif finite(obj):
        out.append((path, obj))
    elif isinstance(obj, float):
        out.append((path, obj))          # NaN / Inf 也记下来
    return out


def as_points(data):
    """把 data 里的条目摊平成 [(x, y), ...]，只认带 x/y 或 t 的字典。"""
    pts = []
    for d in data or []:
        if isinstance(d, dict):
            if "x" in d and "y" in d:
                pts.append((d["x"], d["y"]))
            elif "from" in d and "to" in d:        # arrow/edge: from/to 是 [x,y]
                for k in ("from", "to"):
                    v = d[k]
                    if isinstance(v, (list, tuple)) and len(v) == 2:
                        pts.append((v[0], v[1]))
            elif "t" in d:
                pts.append((d["t"], None))
    return pts


def bbox_of_text(g, X, Y, W):
    """文本在像素空间的横向包围盒 [left, right]，与 validate 同算法。"""
    tx, ty = g.get("x"), g.get("y")
    if not (finite(tx) and finite(ty)):
        return None
    size = g.get("size") or 11
    wpx = vk.est_text_width(str(g.get("text", "")), size)
    px, py = X(tx), Y(ty)
    align = g.get("align", "left")
    left = px if align == "left" else (px - wpx / 2 if align == "center" else px - wpx)
    return [left, left + wpx, py, size]


def mapper(spec_, W, H):
    """与 vizkit.validate 内联同式的世界→像素映射（口径必须一致）。"""
    view = spec_["view"]
    xr, yr = view["xRange"], view["yRange"]
    pad = view.get("pad") or {"l": 58, "r": 14, "b": 34, "t": 16}
    sx = (W - pad.get("l", 58) - pad.get("r", 14)) / (xr[1] - xr[0])
    sy = (H - pad.get("t", 16) - pad.get("b", 34)) / (yr[1] - yr[0])
    if view.get("equalAspect"):
        s = min(sx, sy)
        sx = sy = s
        ox = pad.get("l", 58) + ((W - pad.get("l", 58) - pad.get("r", 14)) - (xr[1] - xr[0]) * sx) / 2 \
             - xr[0] * sx
        oy = pad.get("t", 16) + ((H - pad.get("t", 16) - pad.get("b", 34)) - (yr[1] - yr[0]) * sy) / 2 \
             + (yr[1] - yr[0]) * sy + yr[0] * sy
    else:
        ox = pad.get("l", 58) - xr[0] * sx
        oy = (H - pad.get("b", 34)) + yr[0] * sy
    return (lambda x: ox + x * sx), (lambda y: oy - y * sy), xr, yr


# ---------------------------------------------------------------- checks

def geometry_report(spec_, W, H):
    """返回 (errors, warnings)：每项是 (码, 位置, 说明, 修法)。"""
    errs, warns = [], []
    if not isinstance(spec_, dict) or not isinstance(spec_.get("view"), dict):
        return errs, warns
    view = spec_["view"]
    if "xRange" not in view or "yRange" not in view:
        return errs, warns
    xr, yr = view["xRange"], view["yRange"]
    if not (isinstance(xr, list) and len(xr) == 2 and xr[1] > xr[0]):
        return errs, warns
    if not (isinstance(yr, list) and len(yr) == 2 and yr[1] > yr[0]):
        return errs, warns
    layers = spec_.get("layers") or []
    if not isinstance(layers, list):
        return errs, warns
    X, Y, xr, yr = mapper(spec_, W, H)

    EPS = 1e-9
    texts, boxes, markers, occluders = [], [], [], []

    for i, g in enumerate(layers):
        if not isinstance(g, dict) or "geom" not in g:
            continue
        geom, where = g["geom"], f"layers[{i}]({g['geom']})"

        # ---- G1 非有限坐标 ----
        # size/stroke/width 这些不是坐标，但也无法是 NaN；只放行文本内容本身。
        for path, val in walk_numbers(g, where, skip=("text",)):
            if isinstance(val, float) and not math.isfinite(val):
                errs.append(("G1", f"{path}",
                             f"坐标不是有限数：{val}",
                             "多半是除零或 log(负数)；先在内核里算，再把有限值交给图"))

        # ---- G2 线段/箭头/连线端点越界 ----
        if geom in ("line", "arrow", "edge"):
            raw = g.get("data")
            pts = []
            if isinstance(raw, list):
                for d in raw:
                    if isinstance(d, (list, tuple)) and len(d) == 2 and all(finite(v) for v in d):
                        pts.append((d[0], d[1]))
                    elif isinstance(d, dict):
                        if "x" in d and "y" in d and finite(d["x"]) and finite(d["y"]):
                            pts.append((d["x"], d["y"]))
                        for k in ("from", "to"):
                            v = d.get(k)
                            if isinstance(v, (list, tuple)) and len(v) == 2 \
                               and all(finite(x) for x in v):
                                pts.append((v[0], v[1]))
            for (px, py) in pts:
                if px < xr[0] - EPS or px > xr[1] + EPS or py < yr[0] - EPS or py > yr[1] + EPS:
                    errs.append(("G2", where,
                                 f"端点 ({px}, {py}) 超出 view x∈{xr} y∈{yr}",
                                 "把端点收进 view，或放宽 view —— 画到画布外的线不会有人替你裁"))
        # （曲线飞出 view 的 G7 已删除：viz.js 不裁剪坐标框，曲线略微出框是常态，
        #   渲染器会把它裁在画布边界内，读者看到的只是曲线自然延伸出坐标框一点。
        #   报出来也没有任何可执行的修法 —— 一条没有动作项的检查只会稀释其它告警。）

        # ---- G3 卡片互相压住 ----
        if geom == "card":
            for k, d in enumerate(g.get("data") or []):
                if not isinstance(d, dict) or not all(finite(d.get(k2)) for k2 in ("x", "y", "w", "h")):
                    continue
                if d.get("on") is False:
                    continue
                boxes.append((where, d, d.get("id") or k))

        # ---- G4 文本 vs 实心图元 / G5 重合标记 ----
        if geom == "text" and finite(g.get("x")) and finite(g.get("y")):
            b = bbox_of_text(g, X, Y, W)
            if b:
                texts.append((where, b, str(g.get("text", ""))[:16], i))
        elif geom == "node":
            for d in g.get("data") or []:
                if isinstance(d, dict) and finite(d.get("x")) and finite(d.get("y")):
                    markers.append((where, d["x"], d["y"], d.get("label") or d.get("id"),
                                    g.get("when")))
                    occluders.append((where, d["x"], d["y"], d.get("label") or d.get("id")))
        elif geom == "point":
            # point 只进 G5（重合检测），不进 G4（遮挡检测）：
            # 坐标轴刻度值、单位圆上的 1 / i / -1 这类标签本来就要压在自己的点上，
            # 拿点当遮挡目标，每张图都会报一堆「标签盖住了标签自己」。
            for d in g.get("data") or []:
                if isinstance(d, dict) and finite(d.get("x")) and finite(d.get("y")):
                    markers.append((where, d["x"], d["y"], d.get("label"), g.get("when")))
        elif geom == "matrix" and "data" not in g:
            pass

    # ---- G3 两两卡片 ----
    for a in range(len(boxes)):
        for b in range(a + 1, len(boxes)):
            wa, da, ia = boxes[a]
            wb, db, ib = boxes[b]
            ox = min(da["x"] + da["w"], db["x"] + db["w"]) - max(da["x"], db["x"])
            oy = min(da["y"] + da["h"], db["y"] + db["h"]) - max(da["y"], db["y"])
            if ox > 1e-6 and oy > 1e-6:
                area = ox * oy
                smaller = min(da["w"] * da["h"], db["w"] * db["h"])
                msg = (f"卡片 {ia} 与 {ib} 重叠 {ox:.3g}×{oy:.3g}"
                       f"（占较小者的 {100 * area / max(smaller, 1e-12):.0f}%）")
                if area / max(smaller, 1e-12) > 0.12:
                    errs.append(("G3", f"{wa} ⇄ {wb}", msg,
                                 "卡片是内容的边界，压住即语义冲突 —— 拉开间距或合并为一张"))
                else:
                    warns.append(("G3", f"{wa} ⇄ {wb}", msg, "挪开几个像素即可"))

    # ---- G5 同帧重合的标记 ----
    # 关键：分步 buildup 的图会把同一个锚点在不同帧各画一遍（k==1 / k==2 / k>=3），
    # 这类重绘**互斥**，任何一帧只有一个在画，视觉上不可能重叠 —— 报它就是噪声。
    # 所以先判定两个 when 在步数范围内是否存在同一个 k 让它们同时为真，只有共存才报。
    kmax = _steps_max(spec_)
    for a in range(len(markers)):
        for b in range(a + 1, len(markers)):
            wa, xa, ya, na, ka = markers[a]
            wb, xb, yb, nb, kb = markers[b]
            if abs(xa - xb) > 1e-9 or abs(ya - yb) > 1e-9:
                continue
            if not _coexist(ka, kb, kmax):
                continue
            errs.append(("G5", f"{wa} ⇄ {wb}",
                         f"两个标记在同一帧画在同一坐标 ({xa}, {ya})：{na!r} / {nb!r}"
                         f"（when: {ka!r} 与 {kb!r} 可同时为真）",
                         "同一个点不要画两次；若本就该重合，用一个点加两个标签"))

    # ---- G4 文本盖住实心图元 ----
    for where, b, t, li in texts:
        l, r, py, size = b
        top, bot = py - size, py + size * 0.25
        for w2, mx, my, mn in occluders:
            px, pyy = X(mx), Y(my)
            if l - 4 <= px <= r + 4 and top <= pyy <= bot:
                # 标签**就是**这个节点的标签时不算遮挡（node 自带 label 会另画）
                warns.append(("G4", f"{where} ⇄ {w2}",
                              f"文本 {t!r} 压在标记 {mn!r} 上",
                              "把文本挪到标记外侧（上下分层），或用 dx/dy 留出偏移"))
                break
    # 卡片与文本：直接在世界坐标里比（卡片是世界坐标，文本先反解回世界）
    for where, b, t, li in texts:
        l, r, py, size = b
        for w2, d, cid in boxes:
            x0, x1 = X(d["x"]), X(d["x"] + d["w"])
            y0, y1 = Y(d["y"] + d["h"]), Y(d["y"])
            if l < x1 - 1 and r > x0 + 1 and (py - size) < y1 and (py + size * 0.25) > y0:
                if d.get("label") and str(t).strip() and str(t).strip() == str(d.get("label")).strip():
                    continue          # 就是这张卡的标题，属正常
                warns.append(("G4", f"{where} ⇄ {w2}",
                              f"文本 {t!r} 压在卡片 {cid} 上",
                              "文本移到卡片外，或把它写成卡片的 label"))

    return errs, warns


def _eval_fn(fn, x):
    """安全地算 y=f(x)：只允许极小的算术白名单。"""
    import ast
    allowed = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b,
               ast.Mult: lambda a, b: a * b, ast.Div: lambda a, b: a / b,
               ast.Pow: lambda a, b: a ** b, ast.USub: lambda a: -a,
               ast.UAdd: lambda a: a}
    fun = {"sin": math.sin, "cos": math.cos, "tan": math.tan, "exp": math.exp,
           "log": math.log, "sqrt": math.sqrt, "abs": abs, "pi": math.pi, "e": math.e}

    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.Name):
            if n.id == "x":
                return x
            if n.id in fun:
                return fun[n.id]
            raise ValueError(n.id)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in fun:
            return fun[n.func.id](*(ev(a) for a in n.args))
        if type(n.op) in allowed and hasattr(n, "left"):
            return allowed[type(n.op)](ev(n.left), ev(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in allowed:
            return allowed[type(n.op)](ev(n.operand))
        raise ValueError("no")

    y = ev(ast.parse(str(fn), mode="eval"))
    return y if isinstance(y, (int, float)) and math.isfinite(y) else None


# ---------------------------------------------------------------- main

def main(argv):
    verbose = "-v" in argv or "--verbose" in argv
    sizes = figure_sizes()
    figs = FIGS.build()
    total_err = total_warn = 0
    for fid, spec in figs.items():
        h = sizes.get(fid, 300)
        errs, warns = geometry_report(spec, PAGE_CANVAS_W, h)
        total_err += len(errs)
        total_warn += len(warns)
        tag = "OK  " if not errs else "FAIL"
        print(f"[{tag}] {fid:16s} ({PAGE_CANVAS_W}×{h})  错误 {len(errs)}  警告 {len(warns)}")
        show = errs + (warns if verbose else [])
        for code, where, msg, fix in show:
            print(f"       {code}  {where}")
            print(f"            {msg}")
            print(f"            → {fix}")
    missing = set(figs) - set(sizes)
    if missing:
        print(f"\n⚠ 这些图没有被任何章节引用：{sorted(missing)}")
    print(f"\n合计：{len(figs)} 张图，{total_err} 个错误，{total_warn} 个警告")
    return 1 if total_err else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
