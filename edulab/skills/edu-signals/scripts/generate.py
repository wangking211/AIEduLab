#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate.py — 把结构化数据注入 template/board.html，产出单页「信号与系统」交互网页。

按 MIT 6.003 的知识点组织；全部数值由 lib/signal_kernel.py 驱动
（连续/离散卷积、傅里叶级数与 Gibbs 极限、采样与混叠、时宽频宽积、
RC 低通的频率响应、一阶离散系统的极点与稳定性），**不手写数字**。

**卷积与部分和都是真跑**：离散卷积由逐项相乘求和得到，傅里叶部分和由实际
求和得到，Gibbs 极限由数值积分 Si(π) 得到 —— 凡有解析式的一律与解析式对照。

依赖 sympy：
    python scripts/generate.py <题型key> [输出.html]
    python scripts/generate.py list
    python scripts/generate.py all <输出目录>
    python scripts/generate.py random [seed] [输出.html]
"""

import math
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
PLACEHOLDER = "__LESSON_DATA__"

sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))
sys.path.insert(0, str(SKILL_DIR / "lib"))

import signal_kernel as K                    # noqa: E402
from skillkit import cli                     # noqa: E402

# =====================================================================
# 读数表达式 ↔ 内核 的对账机制
# =====================================================================

_MATHENV = {
    "sqrt": math.sqrt, "abs": abs, "min": min, "max": max, "pow": pow,
    "sign": lambda x: (x > 0) - (x < 0), "floor": math.floor, "ceil": math.ceil,
    "PI": math.pi, "E": math.e,
    "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "asin": math.asin, "acos": math.acos, "atan": math.atan,
    "exp": math.exp, "log": math.log,
}


def _find_ternary(s):
    """找第一个三目 `?` 及其所在括号组边界（支持任意深度嵌套）。"""
    depth, q, qdepth = 0, -1, 0
    for i, ch in enumerate(s):
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "?":
            q, qdepth = i, depth
            break
    if q < 0:
        return None
    depth, nest, colon = qdepth, 0, -1
    for i in range(q + 1, len(s)):
        ch = s[i]
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        elif ch == "?" and depth == qdepth:
            nest += 1
        elif ch == ":" and depth == qdepth:
            if nest == 0:
                colon = i
                break
            nest -= 1
    if colon < 0:
        raise ValueError(f"三目表达式缺冒号：{s!r}")
    lo, d = -1, 0
    for i in range(q - 1, -1, -1):
        if s[i] == ")":
            d += 1
        elif s[i] == "(":
            if d == 0:
                lo = i
                break
            d -= 1
    if lo < 0:
        hi = len(s)
    else:
        d, hi = 0, -1
        for i in range(lo, len(s)):
            if s[i] == "(":
                d += 1
            elif s[i] == ")":
                d -= 1
                if d == 0:
                    hi = i
                    break
        if hi < 0:
            raise ValueError(f"括号不配对：{s!r}")
    return lo, q, colon, hi


def _js_to_py(expr):
    """把三目 `a?b:c` 翻成 Python 的 `b if a else c`（供构建期对账）。"""
    while True:
        f = _find_ternary(expr)
        if f is None:
            return expr
        lo, q, colon, hi = f
        base = lo + 1 if lo >= 0 else 0
        cond, yes, no = expr[base:q], expr[q + 1:colon], expr[colon + 1:hi]
        inner = f"({_js_to_py(yes)} if {_js_to_py(cond)} else {_js_to_py(no)})"
        expr = expr[:base] + inner + expr[hi:]


def _jseval(expr, **env):
    return eval(_js_to_py(expr.replace("^", "**")), {"__builtins__": {}}, {**_MATHENV, **env})


def _agree(label, expr, want, tol=1e-9, **env):
    got = _jseval(expr, **env)
    if abs(float(got) - float(want)) > tol:
        raise AssertionError(
            f"读数表达式与内核不一致（{label}）：\n"
            f"  表达式 {expr!r}\n  按表达式算 = {got!r}\n  内核给出   = {want!r}")
    return got


def ro(rid, label, expr, digits=4, unit=None):
    d = {"id": rid, "label": label, "type": "expr", "expr": expr, "digits": digits}
    if unit:
        d["unit"] = unit
    return d


def ro_status(rid, label, expr, rhs=0, op="==", ok="成立", bad="不成立"):
    return {"id": rid, "label": label, "type": "status", "expr": expr,
            "rhs": rhs, "op": op, "okText": ok, "badText": bad}


# =====================================================================
# 1) 连续卷积：矩形 * 矩形 = 三角形
# =====================================================================
def build_convolution() -> dict:
    t0 = 0.5
    EXPR_C = "max(0,1-abs(t))"
    EXPR_OV = "max(0,min(0.5,t+0.5)-max(-0.5,t-0.5))"
    for t in (-1.0, -0.5, 0.0, 0.3, 0.5, 1.0, 1.5):
        _agree(f"(x*g)(t={t})", EXPR_C, K.conv_rect_rect(t), tol=1e-12, t=t)
        ov = max(0.0, min(0.5, t + 0.5) - max(-0.5, t - 0.5))
        _agree(f"重叠长度(t={t})", EXPR_OV, ov, tol=1e-12, t=t)
    _agree("峰值在 t=0", EXPR_C, K.conv_rect_rect(0.0), tol=1e-12, t=0.0)
    assert abs(K.conv_rect_rect(t0) - 0.5) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "convolve", "t": "t",
                  "caption": "上：两个脉冲的重叠（黄 = 乘积）；下：卷积值随 t 的轨迹"},
        "param": {"name": "t", "label": "滑动位置 $t$", "min": -1.5, "max": 1.5,
                  "step": 0.05, "value": t0, "unit": "", "standard": t0,
                  "ticks": ["-1.5", "0", "0.5 (题设)", "1.5"]},
        "readouts": [
            ro("c", "$(x*g)(t)$", EXPR_C, 5),
            ro("ov", "两脉冲的重叠长度", EXPR_OV, 4),
            ro("peak", "峰值（在 t=0）", "1", 3),
            ro_status("over", "是否还有重叠", EXPR_OV, 0, ">",
                      "仍在重叠，卷积值 > 0", "已完全错开，卷积值为 0"),
        ],
        "constant": {"of": "area", "label": "卷积曲线下的面积恒为 1×1 = 1（面积相乘）"},
    }
    lesson = {
        "language": "zh-CN", "title": "连续卷积：滑动求重叠面积",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>$x(t)$ 与 $g(t)$ 都是宽度 $1$、高度 $1$ 的矩形脉冲。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出卷积定义，并求 $(x*g)(t)$；</li>"
            "<li>拖动滑块，为什么结果是一条三角形而不是矩形？</li>"
            "<li>卷积曲线的面积等于什么？</li></ol>"),
        "answerLabel": "$(x*g)(t)$",
        "answer": "$(x*g)(t) = \\max(0,\\,1-|t|)$ —— 底宽 2、顶点 1 的三角形",
    }
    steps = [
        {"title": "卷积的定义：翻转、平移、相乘、积分",
         "content": ("<p>$(x*g)(t) = \\displaystyle\\int_{{-\\infty}}^{{\\infty}} "
                     "x(\\tau)\\,g(t-\\tau)\\,d\\tau$。</p>"
                     "<p>四步口诀：把 $g$ **翻转**成 $g(-\\tau)$、**平移** $t$ 得 $g(t-\\tau)$、"
                     "与 $x(\\tau)$ **相乘**、再**积分**。"
                     "图上粉色脉冲就是翻转平移后的 $g$，黄色区是乘积。</p>"
                     "<p>几何直观：**卷积就是两个函数的重叠面积随 $t$ 的变化**。</p>")},
        {"title": "为什么是三角形",
         "content": ("<p>两个等宽矩形的重叠长度随 $t$ 线性变化：</p>"
                     "<p>$t=-1$ 时刚接触（重叠 0）→ $t=0$ 时完全重合（重叠 1，最大）"
                     "→ $t=1$ 时再次分离。</p>"
                     "<p>重叠长度 $\\ell(t) = \\max(0,\\,1-|t|)$，而两个高度都是 1，"
                     "所以面积（= 卷积值）就等于 $\\ell(t)$ —— 一条三角形。</p>")},
        {"title": "面积相乘的规律",
         "content": ("<p>$\\displaystyle\\int (x*g)(t)\\,dt = "
                     "\\left(\\int x\\right)\\left(\\int g\\right)$ —— "
                     "卷积的总面积等于两个函数面积之积。</p>"
                     "<p>本例两个面积都是 1，所以三角形面积也是 1。"
                     "这与概率里「两个独立变量之和的分布是各自密度的卷积」是同一件事。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 2) 离散卷积
# =====================================================================
def build_discrete() -> dict:
    n0 = 2
    X, H = [1, 2, 3, 1], [1, 1, 1]
    y = K.discrete_conv(X, H)
    assert [int(v) for v in y] == [1, 3, 6, 6, 4, 1]
    # y[n] 的分段闭式（对 n=0..5）
    EXPR_Y = "n==0?1:(n==1?3:(n==2?6:(n==3?6:(n==4?4:1))))"
    for n in range(6):
        _agree(f"y[n={n}]", EXPR_Y, int(y[n]), tol=1e-12, n=n)
    _agree("输出长度 = 4+3−1", "4+3-1", len(y), tol=1e-12)
    _agree("Σ输出 = Σx·Σh", "(1+2+3+1)*3", int(sum(y)), tol=1e-12)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "dconv", "n": "n",
                  "caption": "上：x[k]（蓝）与翻转平移后的 h[n−k]（粉）；下：输出 y[m]"},
        "param": {"name": "n", "label": "输出下标 $n$", "min": 0, "max": 5, "step": 1,
                  "value": n0, "unit": "", "standard": n0,
                  "ticks": ["0", "2 (题设)", "5"]},
        "readouts": [
            ro("yn", "$y[n]$", EXPR_Y, 0),
            ro("len", "输出长度 $L_x+L_h-1$", "4+3-1", 0),
            ro("sum", "$\\sum y = (\\sum x)(\\sum h)$", "(1+2+3+1)*3", 0),
            ro_status("rise", "输出是否已过峰值（n ≥ 3）", "n-3", 0, ">=",
                      "已过峰值（后半段下降）", "仍在上升段"),
        ],
        "constant": {"of": "len", "label": "输出长度恒为 6 = 4+3−1（与 n 无关）"},
    }
    lesson = {
        "language": "zh-CN", "title": "离散卷积：逐项相乘再求和",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>$x = [1,2,3,1]$（$k=0,1,2,3$），$h = [1,1,1]$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求 $y[n] = \\sum_k x[k]h[n-k]$；</li>"
            "<li>输出长度是多少？为什么？</li>"
            "<li>$h = [1,1,1]$ 这个系统在做什么？</li></ol>"),
        "answerLabel": "完整输出",
        "answer": "$y = [1,\\,3,\\,6,\\,6,\\,4,\\,1]$",
    }
    steps = [
        {"title": "和连续卷积只差一步：积分换成求和",
         "content": ("<p>$y[n] = \\displaystyle\\sum_{{k}} x[k]\\,h[n-k]$ —— "
                     "同样是**翻转、平移、相乘、求和**。</p>"
                     "<p>图上粉色柱是翻转平移后的 $h$：它在纵向上「滑动」经过蓝色的 $x$，"
                     "每停一格就把重叠的那些乘积加起来。</p>")},
        {"title": "逐项算一遍",
         "content": ("<p>$n=2$ 时：$h[2-k]$ 与 $x[k]$ 重叠的乘积是 "
                     "$x[0]h[2]+x[1]h[1]+x[2]h[0] = 1+2+3 = 6$。</p>"
                     "<p>逐个 $n$ 算完得 $[1,3,6,6,4,1]$。"
                     "注意输出比输入**两边各长了 $L_h-1$**：长度为 $4+3-1 = 6$。</p>")},
        {"title": "卷积就是「系统的记忆」",
         "content": ("<p>$h = [1,1,1]$ 的 $y[n] = x[n]+x[n-1]+x[n-2]$ —— "
                     "一个**三点滑动平均**（每输入一个样本，输出把它和前面两个加起来）。</p>"
                     "<p>所以 $h$ 叫**脉冲响应**：给系统一个单位冲激，它的输出就是 $h$。"
                     "线性时不变系统的全部行为都由 $h$ 决定，输出永远是 "
                     "$y = x*h$ —— 这正是卷积在信号处理里的中心地位。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 3) 傅里叶级数与 Gibbs 现象
# =====================================================================
def build_fourier() -> dict:
    N0 = 11
    g = K.gibbs_limit()
    _agree("Gibbs 极限 2Si(π)/π", "1.1789797", g, tol=1e-6)
    # 项数 = 不超过 N 的奇数个数
    _agree("谐波项数", "floor((n+1)/2)", (N0 + 1) // 2, tol=1e-12, n=N0)
    _agree("跳跃幅度", "2", K.square_jump(), tol=1e-12)
    _agree("方波平台值", "1", K.square_partial(0.25, 999), tol=2e-3)
    assert g > 1.0 and abs(g - 1.1789797) < 1e-6

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "fseries", "N": "n",
                  "caption": "灰虚线是理想方波；黄线是部分和；红点标出当前峰值"},
        "param": {"name": "n", "label": "最高谐波次数 $N$", "min": 1, "max": 41, "step": 2,
                  "value": N0, "unit": "", "standard": N0,
                  "ticks": ["1", "11 (题设)", "41"]},
        "readouts": [
            ro("terms", "谐波项数", "floor((n+1)/2)", 0),
            ro("gibbs", "过冲极限 $2\\operatorname{Si}(\\pi)/\\pi$", "1.1789797", 6),
            ro("plat", "方波平台值", "1", 2),
            ro_status("npk", "当前谐波数是否够多（N ≥ 11）", "n", 11, ">=",
                      "足够多：波形已接近方波，但过冲仍在", "谐波偏少"),
        ],
        "constant": {"of": "gibbs", "label": "过冲极限恒为 1.17898 —— 谐波再多也不降到 1"},
    }
    lesson = {
        "language": "zh-CN", "title": "傅里叶级数与 Gibbs 现象",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>周期为 $1$ 的方波（前半周 $+1$、后半周 $-1$）的傅里叶级数是</p>"
            "<p>$x(t) = \\dfrac{4}{\\pi}\\displaystyle\\sum_{{k\\ \\text{odd}}} "
            "\\dfrac{\\sin(2\\pi k t)}{k}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>为什么只取奇次谐波？</li>"
            "<li>拖动滑块增加谐波数，波形怎样变化？</li>"
            "<li>跳变附近的过冲会随谐波增多而消失吗？</li></ol>"),
        "answerLabel": "过冲的极限值",
        "answer": "$\\lim_{N\\to\\infty} \\max S_N(t) = "
                  "\\dfrac{2\\operatorname{Si}(\\pi)}{\\pi} \\approx 1.17898$",
    }
    steps = [
        {"title": "为什么只有奇次谐波",
         "content": ("<p>方波是**奇函数**且**半波反对称**（$x(t+1/2) = -x(t)$）。"
                     "奇对称去掉了所有余弦项，半波反对称去掉了所有偶次正弦项。</p>"
                     "<p>所以只剩奇次正弦。这也是为什么级数收敛得慢 ——"
                     "只剩 $1/k$ 量级的项，跳变处必然留下明显痕迹。</p>")},
        {"title": "Gibbs 现象",
         "content": ("<p>把滑块从 $N=1$ 加到 $41$：波形越来越方，但跳变左右两侧"
                     "**始终有一个凸起**，而且它的高度不降反升到一个固定极限。</p>"
                     "<p>这个极限是 $\\dfrac{{2}}{{\\pi}}\\displaystyle\\int_0^{{\\pi}}"
                     "\\dfrac{{\\sin u}}{{u}}du = \\dfrac{{2\\operatorname{{Si}}(\\pi)}}{{\\pi}}"
                     "\\approx 1.17898$ —— 比 $1$ 高约 $17.9\\%$。</p>"
                     "<p>原因：级数是**逐点收敛**的，但在跳变处不一致收敛；"
                     "增多谐波只是把过冲**挤窄**，不会削平。</p>")},
        {"title": "这件事的实际后果",
         "content": ("<p>用有限带宽的信道传输方波，接收端必然出现过冲与振铃 ——"
                     "这不是设备不好，而是傅里叶级数的数学必然。</p>"
                     "<p>工程上的对策是**限制跳变速率**（升余弦滚降、加窗），"
                     "牺牲一点带宽换取过冲消失。理解 Gibbs 现象是理解这些折中的前提。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 4) 采样与混叠
# =====================================================================
def build_sampling() -> dict:
    fs0, f0 = 2.0, 1.2
    EXPR_FA = "abs(((1.2%fs+fs/2)%fs)-fs/2)"
    for fs in (0.6, 1.0, 1.2, 2.0, 2.4, 3.0, 4.0):
        _agree(f"表观频率(fs={fs})", EXPR_FA, K.aliased_freq(f0, fs), tol=1e-12, fs=fs)
    _agree("奈奎斯特界限 2f₀", "2*1.2", 2.4, tol=1e-12)
    # 注意：f₀=1.2 的奈奎斯特率是 2.4，所以 fs=2.0 **会**混叠（折叠到 0.8）；
    # 只有 fs ≥ 2.4 才不混叠。这里把三种情形都钉住。
    _agree("fs=3.0 时不混叠", EXPR_FA, f0, tol=1e-12, fs=3.0)
    _agree("fs=2.4 时恰在边界（仍得 1.2）", EXPR_FA, f0, tol=1e-12, fs=2.4)
    _agree("fs=2.0 < 2.4 时混叠到 0.8", EXPR_FA, 2.0 - f0, tol=1e-12, fs=2.0)
    assert abs(K.aliased_freq(f0, 3.0) - f0) < 1e-12
    assert abs(K.aliased_freq(f0, 1.0) - 0.2) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "alias", "fs": "fs",
                  "caption": "上：真实信号与采样点；下：由采样点看到（表观）的信号"},
        "param": {"name": "fs", "label": "采样率 $f_s$", "min": 0.6, "max": 4.0,
                  "step": 0.05, "value": fs0, "unit": "", "standard": fs0,
                  "ticks": ["0.6", "2.0 (题设)", "2.4 (奈奎斯特)", "4.0"]},
        "readouts": [
            ro("fa", "表观（折叠）频率", EXPR_FA, 5),
            ro("nyq", "奈奎斯特界限 $2f_0$", "2*1.2", 2),
            ro("ratio", "采样率 / 信号频率", "fs/1.2", 3),
            ro_status("ok", "是否满足采样定理", "fs-2*1.2", 0, ">",
                      "满足（f_s > 2f₀）：可还原", "不满足：发生混叠"),
        ],
        "constant": {"of": "f0", "label": "信号频率恒为 f₀ = 1.2（改变 f_s 不动它）"},
    }
    lesson = {
        "language": "zh-CN", "title": "采样定理与混叠",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>真实信号 $x(t) = \\cos(2\\pi f_0 t)$，$f_0 = 1.2$，用采样率 $f_s$ 采样。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>满足采样定理的条件是什么？</li>"
            "<li>拖动滑块把 $f_s$ 降到 $1.0$，看到的还是原来的信号吗？</li>"
            "<li>为什么「看到的频率」总是落在 $[0, f_s/2]$ 内？</li></ol>"),
        "answerLabel": "采样定理的要求",
        "answer": "$f_s > 2f_0 = 2.4$",
    }
    steps = [
        {"title": "采样定理",
         "content": ("<p>若信号最高频率为 $f_{{max}}$，则只要 "
                     "$f_s > 2f_{{max}}$，样本就能**唯一**确定原信号。"
                     "$2f_{{max}}$ 叫奈奎斯特率。</p>"
                     "<p>图上：把滑块拖到 $2.4$ 以上才会恢复绿色 —— 本题 $f_0 = 1.2$，"
                     "所以奈奎斯特率是 **$2.4$ 而不是 $2$**，"
                     "$f_s = 2.0$ 时其实已经在混叠（表观频率被折到 $0.8$）。"
                     "等号 $f_s = 2f_0$ 是临界情形，工程上取严格大于。</p>")},
        {"title": "为什么会混叠",
         "content": ("<p>采样把频率 $f$ 与 $f + k f_s$ 变成**同一串样本** ——"
                     "因为 $\\cos(2\\pi(f+kf_s)t)$ 在 $t = m/f_s$ 处与 "
                     "$\\cos(2\\pi f t)$ 取值完全相同。</p>"
                     "<p>所以高频成分会「折」回低频。折叠公式把任意频率映射到 "
                     "$[0, f_s/2]$：先把 $f$ 对 $f_s$ 取模，再关于 $f_s/2$ 反射。</p>"
                     "<p>$f_0=1.2$、$f_s=1.0$ 时表观频率变成 $0.2$ ——"
                     "一条慢得多的波。这就是车轮在视频里倒转的原理。</p>")},
        {"title": "抗混叠滤波",
         "content": ("<p>混叠的可怕之处是**不可逆**：一旦折进来，就无法从样本里"
                     "区分原本是 $0.2$ 还是 $1.2$。</p>"
                     "<p>所以实际采样前必须加**抗混叠低通滤波器**，"
                     "把 $f_s/2$ 以上的成分先滤掉 —— 宁可丢高频，也不要混叠。"
                     "这与上一节的 Gibbs 现象共同构成「带宽与保真」的基本折中。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 5) 时宽频宽积
# =====================================================================
def build_spectrum() -> dict:
    tau0 = 1.0
    EXPR_X0 = "tau"
    EXPR_FZ = "1/tau"
    EXPR_PROD = "tau*(1/tau)"
    for tau in (0.3, 0.5, 1.0, 2.0, 2.5):
        _agree(f"X(0)(τ={tau})", EXPR_X0, K.rect_spectrum(0.0, tau), tol=1e-12, tau=tau)
        _agree(f"第一零点(τ={tau})", EXPR_FZ, 1.0 / tau, tol=1e-12, tau=tau)
        _agree(f"时宽×第一零点(τ={tau})", EXPR_PROD, 1.0, tol=1e-12, tau=tau)
        _agree(f"X(第一零点)=0(τ={tau})", "tau*0", K.rect_spectrum(1.0 / tau, tau), tol=1e-12, tau=tau)
    assert abs(K.mainlobe_width(tau0) - 2.0) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "fdomain", "tau": "tau",
                  "caption": "上：时域矩形脉冲；下：频谱 τ·sinc(τf) 与其第一对零点"},
        "param": {"name": "tau", "label": "脉冲宽度 $\\tau$", "min": 0.3, "max": 2.5,
                  "step": 0.05, "value": tau0, "unit": "", "standard": tau0,
                  "ticks": ["0.3", "1.0 (题设)", "2.5"]},
        "readouts": [
            ro("x0", "直流分量 $X(0) = \\tau$", EXPR_X0, 4),
            ro("fz", "第一零点 $1/\\tau$", EXPR_FZ, 4),
            ro("prod", "时宽 × 第一零点", EXPR_PROD, 6),
            ro("mlw", "主瓣宽度 $2/\\tau$", "2/tau", 4),
            ro_status("inv", "是否满足时宽频宽互易（乘积 = 1）", EXPR_PROD, 1, "==",
                      "乘积恒为 1：时域越窄、频域越宽", "乘积不为 1"),
        ],
        "constant": {"of": "prod", "label": "时宽 × 第一零点恒为 1 —— 时频互易"},
    }
    lesson = {
        "language": "zh-CN", "title": "时宽频宽积：时频互易",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>矩形脉冲 $x(t) = \\operatorname{{rect}}(t/\\tau)$ 的频谱是 "
            "$X(f) = \\tau\\,\\operatorname{{sinc}}(\\tau f)$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>频谱的第一对零点在哪里？</li>"
            "<li>拖动滑块改变 $\\tau$，时域与频域各怎么变？</li>"
            "<li>为什么「时宽 × 第一零点」是个常数？</li></ol>"),
        "answerLabel": "第一零点与乘积",
        "answer": "第一零点 $f = 1/\\tau$，故 $\\tau \\times (1/\\tau) = 1$ 恒成立",
    }
    steps = [
        {"title": "从时域算到频域",
         "content": ("<p>$X(f) = \\displaystyle\\int_{{-\\tau/2}}^{{\\tau/2}} "
                     "e^{{-j2\\pi f t}}dt = \\tau\\,\\dfrac{{\\sin(\\pi\\tau f)}}{{\\pi\\tau f}} "
                     "= \\tau\\,\\operatorname{{sinc}}(\\tau f)$。</p>"
                     "<p>积分结果里 $\\tau$ 出现在**两个地方**：系数 $\\tau$ 与 "
                     "自变量 $\\tau f$。前者决定幅度，后者决定**宽度**。</p>")},
        {"title": "时频互易",
         "content": ("<p>$\\operatorname{{sinc}}(\\tau f)$ 的零点在 $\\tau f = \\pm1,\\pm2,\\dots$，"
                     "所以第一零点是 $f = 1/\\tau$。</p>"
                     "<p>于是 $\\tau \\times (1/\\tau) = 1$ —— **常数**。"
                     "时域压窄 $\\tau$，频域主瓣就展宽 $1/\\tau$（反之亦然）。"
                     "把滑块从小拖到大，可以直观看到两个面板此消彼长。</p>")},
        {"title": "这就是不确定性原理的信号版本",
         "content": ("<p>更一般地，任何信号的「时间宽度 × 带宽」都有一个由形状决定的"
                     "下界；对高斯脉冲可以取到等号，这就是海森堡不确定性原理的数学内核。</p>"
                     "<p>工程含义：想要**短脉冲**（时间分辨率高）就必须接受**宽频带**"
                     "（频率分辨率低）。雷达、通信、音频压缩里处处是这个折中。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 6) RC 低通的频率响应
# =====================================================================
def build_filter() -> dict:
    RCms0 = 1.0
    EXPR_FC = "1/(2*PI*RCms*1e-3)"
    EXPR_MAGFC = "1/sqrt(1+pow(2*PI*(1/(2*PI*RCms*1e-3))*RCms*1e-3,2))"
    for rms in (0.1, 0.5, 1.0, 5.0, 10.0):
        _agree(f"f_c(RCms={rms})", EXPR_FC, K.rc_cutoff(1.0, rms * 1e-3), tol=1e-9, RCms=rms)
        _agree(f"|H(f_c)|(RCms={rms})", EXPR_MAGFC,
               K.rc_mag(K.rc_cutoff(1.0, rms * 1e-3), 1.0, rms * 1e-3), tol=1e-12, RCms=rms)
    _agree("截止处恒为 1/√2", "1/sqrt(2)", 1 / math.sqrt(2), tol=1e-12)
    _agree("截止处相位恒为 −45°", "-45", -45.0, tol=1e-12)
    assert abs(K.rc_mag(K.rc_cutoff(1000, 1e-6), 1000, 1e-6) - 1 / math.sqrt(2)) < 1e-12

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "freqresp", "RC": "RCms*1e-3",
                  "caption": "黄线是幅频 |H(f)|（对数频率轴）；紫点是截止频率"},
        "param": {"name": "RCms", "label": "时间常数 $RC$（ms）", "min": 0.1, "max": 10,
                  "step": 0.1, "value": RCms0, "unit": "ms", "standard": RCms0,
                  "ticks": ["0.1", "1 (题设)", "10"]},
        "readouts": [
            ro("fc", "截止频率 $f_c = 1/(2\\pi RC)$", EXPR_FC, 3, "Hz"),
            ro("magc", "截止处 $|H(f_c)|$", EXPR_MAGFC, 6),
            ro("phc", "截止处相位（度）", "-45", 1),
            ro("mag10", "10 倍截止处的 $|H|$", "1/sqrt(1+pow(10,2))", 6),
            ro_status("low", "是否低通（直流增益为 1）", "1", 1, "==",
                      "是低通：直流全通过", "不是低通"),
        ],
        "constant": {"of": "magc", "label": "截止处 |H| 恒为 1/√2 ≈ 0.7071，相位恒为 −45°"},
    }
    lesson = {
        "language": "zh-CN", "title": "RC 低通的频率响应",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>RC 低通电路，$R = 1\\ \\mathrm{{k\\Omega}}$、$C = 1\\ \\mu\\mathrm{{F}}$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>写出 $H(f)$ 与 $|H(f)|$，求截止频率；</li>"
            "<li>为什么叫「截止」频率？那里的 $|H|$ 是多少？</li>"
            "<li>拖动滑块改变时间常数，$-3\\mathrm{{dB}}$ 点在图上怎么移动？</li></ol>"),
        "answerLabel": "截止频率",
        "answer": "$f_c = \\dfrac{1}{2\\pi RC} \\approx 159.15$ Hz，"
                  "此时 $|H| = 1/\\sqrt{2}$、相位 $-45^\\circ$",
    }
    steps = [
        {"title": "分压给出频率响应",
         "content": ("<p>输出取电容电压，分压得</p>"
                     "<p>$H(f) = \\dfrac{{1/(j2\\pi f C)}}{{R + 1/(j2\\pi f C)}} "
                     "= \\dfrac{{1}}{{1 + j2\\pi f RC}}$。</p>"
                     "<p>取模：$|H(f)| = \\dfrac{{1}}{{\\sqrt{{1+(2\\pi f RC)^2}}}}$ —— "
                     "频率越高，分母越大，输出越小。这就是「低通」。</p>")},
        {"title": "截止频率的来历",
         "content": ("<p>令 $2\\pi f RC = 1$ 得 $f_c = \\dfrac{{1}}{{2\\pi RC}}$，"
                     "此时 $|H| = 1/\\sqrt2$，功率减半，即 $-3\\,\\mathrm{{dB}}$。</p>"
                     "<p>相位 $\\angle H = -\\arctan(2\\pi f RC)$，"
                     "在 $f_c$ 处恰为 $-45^\\circ$。这两个数**与 $R$、$C$ 的具体取值无关**"
                     "—— 只要 $f$ 是「以 $f_c$ 为单位」量的。</p>")},
        {"title": "对数频率轴与斜率",
         "content": ("<p>横轴用 $\\log f$ 后，$f \\gg f_c$ 的衰减变成直线："
                     "频率每升十倍，$|H|$ 降十倍，即 **−20 dB/十倍频**。</p>"
                     "<p>这就是 Bode 图的画法。$-3\\mathrm{{dB}}$ 点（紫点）随滑块左右移动，"
                     "但曲线形状始终不变 —— 整个系统只有一个时间常数，"
                     "它把「快」与「慢」的频率分开。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 7) 离散系统：极点与稳定性
# =====================================================================
def build_discrete_sys() -> dict:
    a0 = 0.8
    EXPR_H8 = "pow(a,8)"
    for a in (-1.2, -0.5, 0.0, 0.5, 0.8, 1.0, 1.2):
        _agree(f"h[8](a={a})", EXPR_H8, K.disc_impulse(a, 8), tol=1e-12, a=a)
        _agree(f"|a|(a={a})", "abs(a)", abs(a), tol=1e-12, a=a)
    _agree("极点就是 a", "a", K.disc_pole(a0), tol=1e-12, a=a0)
    _agree("稳定判据 |a| < 1", "1-abs(a)", 1 - abs(a0), tol=1e-12, a=a0)
    assert K.disc_stable(0.8) and not K.disc_stable(1.0)

    board = {
        "view": {"xRange": [0, 10], "yRange": [0, 6]},
        "scene": {"kind": "zplane", "a": "a",
                  "caption": "左：z 平面上的极点与单位圆；右：脉冲响应 h[n] = aⁿ"},
        "param": {"name": "a", "label": "反馈系数 $a$", "min": -1.2, "max": 1.2,
                  "step": 0.05, "value": a0, "unit": "", "standard": a0,
                  "ticks": ["-1.2", "-1", "0", "0.8 (题设)", "1", "1.2"]},
        "readouts": [
            ro("pole", "极点 $z = a$", "a", 3),
            ro("abs", "$|a|$", "abs(a)", 3),
            ro("h8", "$h[8] = a^8$", EXPR_H8, 6),
            ro_status("stable", "是否稳定（|a| < 1）", "1-abs(a)", 0, ">",
                      "稳定：极点在单位圆内，h[n] 衰减", "不稳定：极点在圆外，h[n] 发散"),
        ],
        "constant": {"of": "pole", "label": "极点固定在实轴 z=a 上 —— 它决定一切"},
    }
    lesson = {
        "language": "zh-CN", "title": "离散系统：极点与稳定性",
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            "<p>一阶离散系统 $y[n] = a\\,y[n-1] + x[n]$。</p>"
            "<ol class='list-decimal pl-5 space-y-1'>"
            "<li>求脉冲响应 $h[n]$；</li>"
            "<li>极点在哪里？$a$ 取什么值时系统稳定？</li>"
            "<li>拖动滑块让 $a$ 越过 $-1$，脉冲响应为什么开始振荡？</li></ol>"),
        "answerLabel": "脉冲响应与稳定条件",
        "answer": "$h[n] = a^n$；极点 $z = a$；稳定 $\\iff |a| < 1$",
    }
    steps = [
        {"title": "脉冲响应：喂一个冲激看输出",
         "content": ("<p>令 $x[n] = \\delta[n]$（只在 $n=0$ 为 1），逐拍算：</p>"
                     "<p>$h[0]=1$、$h[1]=a$、$h[2]=a^2$、$\\dots$ 即 $h[n] = a^n$。</p>"
                     "<p>图上右侧的柱状就是它。$|a|<1$ 时衰减到 0，$|a|>1$ 时发散 ——"
                     "**稳定与否只由 $a$ 决定**。</p>")},
        {"title": "极点与单位圆",
         "content": ("<p>对 $y[n] = ay[n-1]+x[n]$ 做 z 变换得 "
                     "$H(z) = \\dfrac{{1}}{{1-az^{{-1}}}} = \\dfrac{{z}}{{z-a}}$，"
                     "极点在 $z = a$。</p>"
                     "<p>**稳定性判据**：所有极点在单位圆内（$|z|<1$）。"
                     "这里就是 $|a|<1$，与刚才的结论一致。左图的单位圆就是这条判据的几何形态。</p>")},
        {"title": "负极点为什么振荡",
         "content": ("<p>$a<0$ 时 $h[n] = a^n$ 交替变号（$+,−,+,−\\dots$），"
                     "所以输出看起来在振荡 —— 频率最高（每拍翻转一次）。"
                     "$a=-1$ 时它等幅振荡，永不衰减，正好落在稳定边界上。</p>"
                     "<p>连续系统里「实部管衰减、虚部管振荡」；离散系统里"
                     "「模长管衰减、幅角管振荡」—— 单位圆就是分界。"
                     "这与 `edu-ode-dynamics` 的相平面分类是同一件事的两个版本。</p>")},
    ]
    return {"lesson": lesson, "steps": steps, "board": board}


# =====================================================================
# 注册
# =====================================================================
REGISTRY = {
    "convolution": build_convolution,
    "discrete": build_discrete,
    "fourier": build_fourier,
    "sampling": build_sampling,
    "spectrum": build_spectrum,
    "filter": build_filter,
    "discrete_sys": build_discrete_sys,
}


def _random_build(seed=None):
    import random as _r
    rng = _r.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="信号与系统 · 交互学习", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
