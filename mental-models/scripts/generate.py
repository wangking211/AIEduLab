# -*- coding: utf-8 -*-
"""
generate.py — 芒格思维模型：注入模板 + 范例 build_* + CLI。

每个 build_* 返回一个 lesson dict（见 references/problem-schema.md），
render_html() 把它序列化进 board.html 的 __LESSON_DATA__ 数据岛。

交互设计原则：
  - 滑块驱动的量全部用 **表达式字符串**（JS 端 evalExpr 实时求值），保证拖动即时反馈；
  - 讲解文字里的数值全部由 sympy 在 **默认参数** 下精确算出，与画板读数同源一致；
  - 每页至少一个"定值指示"或"状态灯"，暴露该模型的不变量/临界条件。

用法：
  python3 generate.py list
  python3 generate.py bayes ./out/bayes.html
  python3 generate.py all ./out
"""

import json
import sys
from fractions import Fraction
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR / "lib"))

import sympy as sp                    # noqa: E402
import models_kernel as K             # noqa: E402

TEMPLATE = (SKILL_DIR / "template" / "board.html").read_text(encoding="utf-8")


# ---------------- 数值 → JSON 安全 ----------------
def _n(x):
    """sympy/Fraction → float（供 JSON）。"""
    if isinstance(x, (int, float)):
        return float(x)
    if isinstance(x, Fraction):
        return float(x)
    return float(sp.N(x))


def _tex(x):
    return K.tex(x)


def _num_str(x):
    """紧凑可读数字串：≥1000 取整并加千分位，中等值一位小数，小数用有效数字（避免科学计数法渗入正文）。"""
    v = _n(x)
    if abs(v) >= 1000:
        return f"{round(v):,}"
    if abs(v) >= 100:
        return f"{v:,.1f}"
    if abs(v - round(v)) < 1e-9:
        return str(int(round(v)))
    return f"{v:.4f}".rstrip("0").rstrip(".")


def render_html(data, out):
    """把 lesson dict 注入模板并写出。"""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    out.write_text(TEMPLATE.replace("__LESSON_DATA__", payload), encoding="utf-8")
    return out


# =====================================================================
# 1) 复利：时间是朋友还是敌人
# =====================================================================
def build_compound():
    P0, r, t = 10000, 8, 30
    c = K.compound(P0, r, t)
    r72 = K.rule_of_72(r)
    return {
        "lesson": {
            "title": "复利：时间是朋友还是敌人",
            "subtitle": "爱因斯坦据传称之为“世界第八大奇迹”——它的威力不在收益率，而在指数",
            "problem": (
                "<p>把 <b>1 万元</b> 以年化 <b>8%</b> 投入，按年复利，30 年后是多少？</p>"
                "<p class='mt-2'>直觉答案通常是「8% × 30 年 ≈ 2.4 倍」——"
                "<span class='text-rose-600 font-semibold'>这是单利，也是绝大多数人算错的地方</span>。</p>"
                "<p class='mt-2'>拖动下方滑块，看复利与单利的差距如何随时间拉开。</p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "compound", "caption": "复利 vs 单利",
                      "xMax": "max(30, t+3)", "yMax": "F*1.18",
                      "xRange": [0, "max(30, t+3)"], "yRange": [0, "F*1.18"]},
            "view": {"xRange": [0, 34], "yRange": [0, 120000]},
            "params": [
                {"name": "r", "label": "年化收益率 r", "min": 1, "max": 20, "step": 0.5, "value": r, "unit": "%", "digits": 1},
                {"name": "t", "label": "投资年数 t", "min": 1, "max": 50, "step": 1, "value": t, "unit": " 年", "digits": 0},
                {"name": "P", "label": "本金 P", "min": 1000, "max": 100000, "step": 1000, "value": P0, "unit": " 元", "digits": 0},
            ],
            "scalars": [
                {"name": "F", "expr": "P*(1+r/100)^t"},
                {"name": "Fs", "expr": "P*(1+r/100*t)"},
            ],
            "readouts": [
                {"id": "F", "label": "复利终值 F = P(1+r)^t", "type": "expr", "expr": "F", "money": True, "unit": "元", "highlight": True},
                {"id": "Fs", "label": "单利终值 P(1+r·t)", "type": "expr", "expr": "Fs", "money": True, "unit": "元", "color": "#78716c"},
                {"id": "gap", "label": "复利多出（馈赠）", "type": "expr", "expr": "F-Fs", "money": True, "unit": "元", "color": "#059669"},
                {"id": "mult", "label": "本金倍数", "type": "expr", "expr": "F/P", "digits": 2, "unit": " 倍"},
                {"id": "double", "label": "翻倍所需年数 ≈ 72/r", "type": "expr", "expr": "72/r", "digits": 1, "unit": " 年"},
                {"id": "pos", "label": "复利 vs 单利", "type": "status", "expr": "F-Fs", "op": ">", "rhs": 0, "okText": "复利已跑赢单利", "badText": "与单利持平（t=1）"},
            ],
            "legend": [
                {"color": "#b45309", "text": "复利 P(1+r)^t"},
                {"color": "#78716c", "text": "单利 P(1+r·t)"},
            ],
        },
        "steps": [
            {"title": "先写复利公式", "content": (
                "$$F = P\\left(1+\\frac{r}{n}\\right)^{nt}$$"
                "<p>按年计息 $n=1$，代入 $P=10000$、$r=8\\%$、$t=30$：</p>"
                "$$F = 10000\\times 1.08^{30} = " + _num_str(c["F"]) + "\\ \\text{元}$$"
            )},
            {"title": "对照单利，看差距", "content": (
                "<p>单利 $F_s = P(1+rt) = 10000\\times(1+0.08\\times30) = "
                + _num_str(c["F_simple"]) + "$ 元。</p>"
                "$$F - F_s = " + _num_str(c["double_vs_simple"]) + "\\ \\text{元（复利馈赠）}$$"
                "<p>复利是单利的 <b>" + f"{_n(c['F'])/_n(c['F_simple']):.2f}"
                + "</b> 倍。差额全部来自「利息再生利息」——前 10 年几乎看不出差别，后 10 年拉开一半以上。</p>"
            )},
            {"title": "72 法则：为什么是 72", "content": (
                "<p>翻倍年数 $t_{2} = \\dfrac{\\ln 2}{\\ln(1+r)}$，对小 $r$ 有 $\\ln(1+r)\\approx r$，"
                "于是 $t_2\\approx \\dfrac{0.693}{r} = \\dfrac{69.3}{r\\%}$。取 72 是因为 72 有更多因数"
                "（2,3,4,6,8,9,12…），便于口算。</p>"
                "$$t_2 = \\frac{\\ln 2}{\\ln 1.08} = " + f"{_n(c['doubling_years']):.2f}" + "\\ \\text{年}$$"
                "<p>而 72 法则给 $72/8 = " + _num_str(r72["approx"]) + "$ 年，误差仅 $"
                + f"{abs(_n(r72['error_pct'])):.2f}" + "\\%$。所以 <b>8% 年化 ≈ 每 9 年翻一倍</b>；"
                "30 年翻 3 次多：1 万 → 2 万 → 4 万 → " + _num_str(c["F"]/10000) + " 万。</p>"
            )},
            {"title": "反向：负债的复利", "content": (
                "<p>把 $r$ 变成负数是不可能的（滑块最低 1%），但把同一个公式套在信用卡欠款上："
                "<b>年化 18% 的循环利息，4 年翻倍</b>（$72/18=4$）。</p>"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>芒格：<span class='text-stone-500'>"
                "「第一，别让自己成为复利的受害者；第二，永远别停止成为复利的受益者。」</span>"
                "——所以他的第一条规则是<b>先排除愚蠢</b>（反过来想）。</p>"
            )},
        ],
    }


# =====================================================================
# 2) 贝叶斯基率：为什么阳性大多没事
# =====================================================================
def build_bayes():
    prior, sens, spec, per = 0.01, 0.99, 0.95, 1000      # 内核口径：小数
    prior_pct, sens_pct, spec_pct = 1, 99, 95            # 滑块口径：百分数
    b = K.bayes(prior, sens, spec, per)
    return {
        "lesson": {
            "title": "贝叶斯基率：为什么阳性大多是假的",
            "subtitle": "基率忽视（base-rate neglect）是最高频的认知错误之一",
            "problem": (
                "<p>某病患病率 <b>1%</b>。一种试剂盒：<b>真有病的人 99% 会查出阳性</b>（灵敏度），"
                "<b>没病的人 95% 会查出阴性</b>（特异度）。</p>"
                "<p class='mt-2'>你测出阳性。请问：你<b>真的得病</b>的概率是多少？</p>"
                "<p class='mt-2 text-rose-600 font-semibold'>绝大多数人答 99%，正确答案是 "
                + f"{_n(b['posterior'])*100:.1f}" + "%。</p>"
                "<p class='mt-2'>拖动滑块，特别是把<b>患病率</b>拉高拉低，看它如何主宰结果。</p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "bayes", "caption": "1000 人检测结果", "per": per},
            "view": {"xRange": [0, 14], "yRange": [0, 11]},
            "params": [
                {"name": "prior", "label": "先验患病率", "min": 0.1, "max": 50, "step": 0.1, "value": prior_pct, "unit": "%", "digits": 1},
                {"name": "sens", "label": "灵敏度（真阳率）", "min": 50, "max": 100, "step": 1, "value": sens_pct, "unit": "%", "digits": 0},
                {"name": "spec", "label": "特异度（真阴率）", "min": 50, "max": 100, "step": 1, "value": spec_pct, "unit": "%", "digits": 0},
            ],
            "scalars": [
                {"name": "pp", "expr": "prior/100"},
                {"name": "ps", "expr": "sens/100"},
                {"name": "pc", "expr": "spec/100"},
                {"name": "sick", "expr": "pp*1000"},
                {"name": "tp", "expr": "ps*pp*1000"},
                {"name": "fp", "expr": "(1-pc)*(1-pp)*1000"},
                {"name": "fn", "expr": "sick-tp"},
                {"name": "tn", "expr": "1000-tp-fp-fn"},
                {"name": "post", "expr": "tp/(tp+fp)"},
            ],
            "readouts": [
                {"id": "post", "label": "P(真有病 | 阳性)", "type": "expr", "expr": "post*100", "digits": 1, "unit": "%", "highlight": True},
                {"id": "fps", "label": "阳性中假阳占比", "type": "expr", "expr": "fp/(tp+fp)*100", "digits": 1, "unit": "%", "color": "#b45309"},
                {"id": "lift", "label": "阳性把风险放大", "type": "expr", "expr": "post/pp", "digits": 1, "unit": " 倍"},
                {"id": "fp", "label": "假阳性人数 / 1000", "type": "expr", "expr": "fp", "digits": 0, "unit": " 人", "color": "#b45309"},
                {"id": "tp", "label": "真阳性人数 / 1000", "type": "expr", "expr": "tp", "digits": 0, "unit": " 人", "color": "#dc2626"},
                {"id": "warn", "label": "阳性是否可信", "type": "status", "expr": "post", "op": ">", "rhs": 0.5, "okText": "可信（>50%）", "badText": "多数为假阳性"},
            ],
            "legend": [
                {"color": "#ef4444", "text": "真阳性（有病且阳性）"},
                {"color": "#f59e0b", "text": "假阳性（无病但阳性）"},
                {"color": "#7f1d1d", "text": "假阴性（有病但漏诊）"},
                {"color": "#57534e", "text": "真阴性"},
            ],
        },
        "steps": [
            {"title": "把人群铺开：1000 人的四格表", "content": (
                "<p>先验患病率 1% → 1000 人中 <b>" + _num_str(b["sick"]) + "</b> 人真有病，"
                "<b>" + _num_str(1000 - b["sick"]) + "</b> 人健康。</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li>真阳性：$" + _tex(b["sick"]) + "\\times 99\\% = " + _tex(b["tp"]) + "$ 人</li>"
                "<li>假阳性：$" + _num_str(1000 - b["sick"]) + "\\times(1-95\\%) = " + _tex(b["fp"]) + "$ 人</li>"
                "</ul>"
                "<p class='mt-2'><b>关键在于：假阳性（" + _num_str(b["fp"]) + " 人）比真阳性（"
                + _num_str(b["tp"]) + " 人）多出 " + f"{_n(b['fp'])/_n(b['tp']):.1f}" + " 倍。</b>"
                "因为健康的人基数太大——这就是<b>基率</b>的力量。</p>"
            )},
            {"title": "套贝叶斯公式", "content": (
                "$$P(\\text{病}\\mid+) = \\frac{s\\,\\pi}{s\\,\\pi + (1-c)(1-\\pi)}$$"
                "<p class='text-xs text-stone-500 mt-1'>其中 $s$=灵敏度，$c$=特异度，$\\pi$=先验患病率。</p>"
                "$$= \\frac{0.99\\times0.01}{0.99\\times0.01 + 0.05\\times0.99} = "
                + _tex(b["posterior"]) + " \\approx " + f"{_n(b['posterior'])*100:.1f}" + "\\%$$"
                "<p>分母第二项 $P(+\\mid\\text{健康}) = 1-\\text{特异度}$ 就是假阳性的来源。"
                "它乘的是 <b>0.99 这个巨大基数</b>。</p>"
            )},
            {"title": "似然比与证据强度", "content": (
                "<p>把检测质量压成一个数：<b>似然比</b> $= \\dfrac{\\text{灵敏度}}{1-\\text{特异度}} = "
                "\\dfrac{0.99}{0.05} = " + _tex(sp.Rational(99, 5)) + " \\approx 19.8$。</p>"
                "<p>贝叶斯的另一种形式：<b>先验赔率 × 似然比 = 后验赔率</b>。</p>"
                "$$\\frac{1}{99}\\times19.8 = " + _tex(b["odds_post"]) + " \\Longrightarrow P = "
                + _tex(b["posterior"]) + "$$"
                "<p>检测把风险放大了 <b>" + f"{_n(b['lift']):.1f}" + " 倍</b>"
                "——从 1% 抬到 " + f"{_n(b['posterior'])*100:.1f}" + "%，"
                "<span class='text-emerald-700 font-semibold'>这是有价值的证据，但远不是结论</span>。</p>"
            )},
            {"title": "什么时候阳性才可信", "content": (
                "<p>拖动<b>患病率</b>滑块：要让 $P(\\text{病}\\mid+) > 50\\%$，"
                "在灵敏度 99%、特异度 95% 下，患病率须超过约 <b>4.8%</b>。</p>"
                "<p class='mt-2'>这解释了两件事：</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li><b>筛查只用于高危人群</b>——先抬高先验，检测才有意义；</li>"
                "<li><b>普查必然产生大量假阳性</b>——在低基率人群里，哪怕 99% 准确的检测也是灾难。</li>"
                "</ul>"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>冤案的数学根源正在于此："
                "把「现场出现过的罕见 DNA」当成 99.99% 有罪证据，"
                "而忽略「这片区域里有多个无关者的 DNA」这个基率。</p>"
            )},
        ],
    }


# =====================================================================
# 3) 期望值与凯利：长期赢的唯一仓位
# =====================================================================
def build_expected():
    p, b, rounds = 60, 2, 40
    e = K.expected_value([(sp.Rational(6, 10), 2), (sp.Rational(4, 10), -1)])
    sb = K.survivor_bias(100, sp.Rational(9, 10), 10, 1)
    return {
        "lesson": {
            "title": "期望值与凯利：为什么「全押」必输",
            "subtitle": "算术期望决定你是否该参与，几何增长率决定你能走多远",
            "problem": (
                "<p>一个赌局：<b>60% 概率赢 2 倍，40% 概率输光本金</b>。你下注多少？</p>"
                "<p class='mt-2'>每 1 单位的期望净收益是 "
                "$$0.6\\times2 - 0.4\\times1 = " + _tex(e["ev"]) + " > 0$$"
                "<span class='text-emerald-700 font-semibold'>期望为正，应该参与</span>。"
                "但 <b>该下多大比例</b>？全押的话，长期复利增长率是负的。</p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "expected", "caption": "算术期望 vs 几何复利", "xMax": 40},
            "view": {"xRange": [0, 12], "yRange": [-0.6, 6.4]},
            "params": [
                {"name": "p", "label": "胜率 p", "min": 30, "max": 90, "step": 1, "value": 60, "unit": "%", "digits": 0},
                {"name": "b", "label": "净赔率 b（赢得 b 倍本金）", "min": 0.2, "max": 5, "step": 0.1, "value": 2, "unit": "", "digits": 1},
            ],
            "scalars": [
                {"name": "pw", "expr": "p/100"},
                {"name": "q", "expr": "1-p/100"},
                {"name": "ev", "expr": "pw*b-q"},
                {"name": "kelly", "expr": "(b*pw-q)/b"},
                {"name": "kellyHalf", "expr": "kelly/2"},
                {"name": "ev2x", "expr": "2*kelly*ev"},
            ],
            "readouts": [
                {"id": "kelly", "label": "凯利最优仓位 f* = (bp−q)/b", "type": "expr", "expr": "kelly*100", "digits": 1, "unit": "%", "highlight": True},
                {"id": "half", "label": "半凯利（芒格/巴菲特式）", "type": "expr", "expr": "kellyHalf*100", "digits": 1, "unit": "%", "color": "#0891b2"},
                {"id": "ev", "label": "每 1 单位的期望净收益", "type": "expr", "expr": "ev", "digits": 3, "unit": "", "color": "#059669"},
                {"id": "ev2", "label": "双倍凯利仓位的期望（更高！）", "type": "expr", "expr": "ev2x", "digits": 3, "unit": "", "color": "#dc2626"},
                {"id": "ok", "label": "赌局是否值得参与", "type": "status", "expr": "ev", "op": ">", "rhs": 0, "okText": "期望为正，可参与", "badText": "期望为负，别碰"},
                {"id": "risk", "label": "满凯利是否可承受", "type": "status", "expr": "kelly", "op": "<", "rhs": 0.5, "okText": "仓位<50%，尚可", "badText": "仓位过重，危险"},
            ],
            "legend": [
                {"color": "#b45309", "text": "满凯利 f*"},
                {"color": "#0891b2", "text": "半凯利 f*/2"},
                {"color": "#dc2626", "text": "双倍凯利（复利衰减）"},
            ],
        },
        "steps": [
            {"title": "算术期望：该不该参与", "content": (
                "$$E = p\\,b - q = 1.2 - 0.4 = 0.8 > 0$$"
                "<p>每 1 单位期望净赚 <b>$" + _tex(e["ev"]) + "$</b>，<b>参与是对的</b>。"
                "但注意：算术期望会<b>一路鼓励你加大仓位</b>——把每局下注额翻倍，期望净赚也翻倍到 $"
                + _tex(e["ev"] * 2) + "$，这就是陷阱。</p>"
            )},
            {"title": "凯利公式：该下多大", "content": (
                "$$f^* = \\frac{bp - q}{b} = \\frac{0.8}{2} = 40\\%$$"
                "<p>凯利仓位是<b>长期资金增长率最大化</b>的解，不是最大化期望、也不是最大化胜率。"
                "它的含义：<b>按这个比例下注，时间无限长时你一定赢，且赢的任何其他比例都更慢。</b></p>"
            )},
            {"title": "几何增长率：为什么全押必输", "content": (
                "<p>设下注比例 $x$，一次下注的资金对数增长为</p>"
                "$$g(x) = p\\ln(1+xb) + q\\ln(1-x)$$"
                "$$g(1) = \\ln(1+\\infty\\cdot) \\to -\\infty \\quad(\\text{全押})$$"
                "<p class='mt-2'>代入默认值：$g(1.0)=0.6\\ln3+0.4\\ln0 = -\\infty$，"
                "$g(0.4)= " + f"{0.6*__import__('math').log(1+0.4*2)+0.4*__import__('math').log(0.6):.4f}" + " > 0$。</p>"
                "<p class='mt-2'><b>全押 100% → 4 次后就大概率出局</b>（$0.6^4=13\\%$ 四连胜才保住）。"
                "哪怕期望为正，只要有一格是「输光」，复利就永久终结。</p>"
            )},
            {"title": "为什么是半凯利", "content": (
                "<p>凯利对参数估计的误差<b>极度敏感</b>：你把胜率高估 5%，最优仓位就要大幅下调。"
                "而凯利平方根法则说——<b>仓位减半，长期增速只损失 25%</b>，风险却大幅下降。</p>"
                "$$g(f^*/2) \\approx 0.75\\,g(f^*)$$"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>芒格与巴菲特从不用满凯利："
                "他们连「确定的事」都只下重注而非全注。"
                "<b>凯利是上限，不是目标</b>——因为你是人，而人对赔率的估计从不准。</p>"
                "<p class='mt-2'>另外，幸存者偏差会让你看到一堆「全押成功」的故事："
                "100 家公司里 10 家百倍回报被广泛报道，90 家破产无人书写。"
                "只看幸存者，真实期望 $" + _tex(sb["true_ev"]) + "$ 会被高估为 $"
                + _tex(sb["observed"]) + "$。</p>"
            )},
        ],
    }


# =====================================================================
# 4) 安全边际：为什么要留冗余
# =====================================================================
def build_safety():
    mu, sigma, price = 100, 15, 80
    s = K.margin_of_safety(mu, price)
    kp = K.knockthrough_prob(mu, sigma, price)
    return {
        "lesson": {
            "title": "安全边际：估计必然出错，所以要留冗余",
            "subtitle": "格雷厄姆的定价公式：价值 = 保守估计 × 安全边际",
            "problem": (
                "<p>你估算某资产内在价值约 <b>100</b>（估计不确定，标准差 15），"
                "当前市价 <b>80</b>。</p>"
                "<p class='mt-2'>安全边际 <b>$= (100-80)/100 = 20\\%$</b>。</p>"
                "<p class='mt-2'>但真正的问题是：<b>如果你的估值本身就错了呢？</b>"
                "拖动下方三个滑块，看「击穿概率」如何随估值不确定性 σ 变化。</p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "safety", "caption": "价值分布 vs 价格线",
                      "xRange": ["mu-3.4*sigma", "mu+3.4*sigma"],
                      "yRange": [0, "1.30/(sigma*sqrt(2*PI))"]},
            "view": {"xRange": [49, 151], "yRange": [0, 0.055]},
            "params": [
                {"name": "mu", "label": "估值中枢 μ", "min": 60, "max": 140, "step": 1, "value": mu, "unit": "", "digits": 0},
                {"name": "sigma", "label": "估值不确定性 σ", "min": 3, "max": 40, "step": 0.5, "value": sigma, "unit": "", "digits": 1},
                {"name": "price", "label": "买入价", "min": 40, "max": 140, "step": 1, "value": price, "unit": "", "digits": 0},
            ],
            "scalars": [
                {"name": "z", "expr": "(price-mu)/sigma"},
                {"name": "prob", "expr": "0.5*(1+erf(z/sqrt(2)))"},
                {"name": "mos", "expr": "(mu-price)/mu"},
                {"name": "cv", "expr": "sigma/mu"},
            ],
            "readouts": [
                {"id": "mos", "label": "安全边际 (μ−P)/μ", "type": "expr", "expr": "mos*100", "digits": 1, "unit": "%", "highlight": True},
                {"id": "prob", "label": "击穿概率 P(真实价值 < 价格)", "type": "expr", "expr": "prob*100", "digits": 1, "unit": "%", "color": "#dc2626"},
                {"id": "z", "label": "标准分 z = (P−μ)/σ", "type": "expr", "expr": "z", "digits": 2, "unit": ""},
                {"id": "cv", "label": "相对不确定性 σ/μ", "type": "expr", "expr": "cv*100", "digits": 1, "unit": "%"},
                {"id": "safe", "label": "是否留足边际", "type": "status", "expr": "prob", "op": "<", "rhs": 0.15, "okText": "击穿概率<15%，较安全", "badText": "击穿概率过高"},
            ],
            "legend": [
                {"color": "#b45309", "text": "价值概率密度 N(μ,σ²)"},
                {"color": "#dc2626", "text": "击穿区（价值跌破价格）"},
                {"color": "#059669", "text": "安全边际区间"},
            ],
        },
        "steps": [
            {"title": "先算名义安全边际", "content": (
                "$$\\text{MOS} = \\frac{\\mu - P}{\\mu} = \\frac{20}{100} = 20\\%$$"
                "<p>格雷厄姆要求 <b>至少 1/3</b>（即折价 33% 以上）。20% 属于「勉强及格」。</p>"
            )},
            {"title": "承认估值会错：正态假设", "content": (
                "<p>把估值当成随机变量：真实价值 $\\sim N(\\mu,\\sigma^2)$。"
                "<b>击穿概率</b>就是左侧尾部面积，先算标准分：</p>"
                "$$z = \\frac{P-\\mu}{\\sigma} = \\frac{80-100}{15} = " + f"{_n(kp['z']):.3f}" + "$$"
                "$$P(V < P) = \\Phi(z) = \\Phi(" + f"{_n(kp['z']):.3f}" + ")$$"
                "$$= " + f"{_n(kp['prob']):.4f}" + " \\approx " + f"{_n(kp['prob_pct']):.1f}" + "\\%$$"
                "<p class='text-xs text-stone-500 mt-1'>其中 $\\Phi(z)=\\tfrac12\\left[1+\\operatorname{erf}\\!\\left(\\tfrac{z}{\\sqrt2}\\right)\\right]$"
                " 是标准正态的累积分布函数。</p>"
                "<p>20% 的名义边际下，仍有 <b>" + f"{_n(kp['prob_pct']):.1f}" + "%</b> 概率实际上买贵了。</p>"
            )},
            {"title": "不确定性才是真正的敌人", "content": (
                "<p>把 σ 从 15 拖到 <b>30</b>（同样的 20% 边际）：击穿概率跳到 "
                f"{_n(K.knockthrough_prob(100, 30, 80)['prob_pct']):.1f}" + "%。</p>"
                "$$z = \\frac{P-\\mu}{\\sigma}$$"
                "<p class='mt-2'>同一个边际下，<b>σ 越大 → |z| 越小 → 击穿概率越高</b>。"
                "<p class='mt-2'><b>结论：安全边际不是一个固定百分比，而是 σ 的函数。</b>"
                "越是看不懂的生意（σ 越大），需要留的边际越大——这就是为什么巴菲特只买"
                "看得懂的生意（<b>能力圈</b>），并且在圈内也要留足边际。</p>"
            )},
            {"title": "把边际定量化", "content": (
                "<p>想把击穿概率压到 5% 以下，价格须满足</p>"
                "$$P \\le \\mu - 1.645\\,\\sigma = 100 - 24.68$$"
                "$$= " + _num_str(100 - 1.645 * 15) + "\\ \\text{元}$$"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>这就是「反过来想」的量化版本："
                "<b>先算出会亏多少概率的价格，再决定买不买</b>——"
                "而不是先看好公司，再找理由说服自己价格合理。</p>"
            )},
        ],
    }


# =====================================================================
# 5) 机会成本：看不见的成本
# =====================================================================
def build_opportunity():
    chosen, alts = 80, [100, 60]
    o = K.opportunity_cost(chosen, alts)
    return {
        "lesson": {
            "title": "机会成本：选 A 的真实成本是放弃的 B",
            "subtitle": "芒格：「如果我不能比对手更清楚地知道我会死在哪里，我就不去那个地方。」",
            "problem": (
                "<p>三份工作摆在面前：A 年薪 <b>80 万</b>（轻松）、"
                "B 年薪 <b>100 万</b>（忙碌）、C 年薪 <b>60 万</b>（清闲）。</p>"
                "<p class='mt-2'>你选了 A。它的<b>机会成本</b>是多少？</p>"
                "<p class='mt-2'>不是 60 万，也不是 80 万——"
                "<span class='text-rose-600 font-semibold'>是被你放弃的最优方案 100 万</span>。"
                "拖动滑块调整 A 的报价，看它什么时候才「真的划算」。</p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {
                "kind": "opportunity", "caption": "所选 vs 被放弃的最优",
                "xRange": [0, "max(altB,altC,chosen)*1.35"], "yRange": [-0.9, 3.1],
                "options": [
                    {"label": "方案 A（所选）", "value": "chosen", "chosen": True},
                    {"label": "方案 B（最优替代）", "value": "altB"},
                    {"label": "方案 C", "value": "altC"},
                ],
                "best_alt": "max(altB,altC)",
                "opp_cost_raw": "opp_cost",
                "net_raw": "net",
            },
            "view": {"xRange": [0, 135], "yRange": [-0.9, 3.1]},
            "params": [
                {"name": "chosen", "label": "所选方案 A 的价值", "min": 40, "max": 130, "step": 1, "value": chosen, "unit": " 万", "digits": 0},
            ],
            "scalars": [
                {"name": "altB", "expr": "100"},
                {"name": "altC", "expr": "60"},
                {"name": "opp_cost", "expr": "max(altB,altC)-chosen"},
                {"name": "net", "expr": "chosen-max(altB,altC)"},
            ],
            "readouts": [
                {"id": "best", "label": "机会成本 = 被放弃的最优方案", "type": "expr", "expr": "max(altB,altC)", "money": True, "unit": " 万", "highlight": True},
                {"id": "net", "label": "相对最优替代的净收益", "type": "expr", "expr": "net", "money": True, "unit": " 万", "color": "#dc2626"},
                {"id": "acct", "label": "若按账面看（不扣机会成本）", "type": "expr", "expr": "chosen", "money": True, "unit": " 万", "color": "#78716c"},
                {"id": "ok", "label": "是否选中了最优", "type": "status", "expr": "net", "op": ">=", "rhs": 0, "okText": "是最优选择", "badText": "不是最优选择"},
            ],
            "legend": [],
        },
        "steps": [
            {"title": "机会成本的定义", "content": (
                "$$\\text{机会成本} = \\max(\\text{放弃项}) - \\text{所选项}$$"
                "<p>选 A 放弃 {B, C}：被放弃的最优是 B 的 <b>100 万</b>，"
                "所以 A 的机会成本 <b>$= 100-80 = 20$ 万</b>。</p>"
                "<p class='mt-2'><span class='text-rose-600 font-semibold'>常见错误</span>："
                "拿「C 只有 60 万」自我安慰——机会成本永远对照<b>最好的那个</b>，不是最差的。</p>"
            )},
            {"title": "机会成本把「划算」变成可算", "content": (
                "<p>账面收入 80 万，扣掉机会成本 20 万，"
                "<b>真实净收益是 −20 万</b>。你其实每天在为「没去 B」付费。</p>"
                "<p class='mt-2'>拖动滑块：A 必须涨到 <b>100 万以上</b>，真实净收益才转正。"
                "在此之前，选 A 在数学上就是亏的——无论你多喜欢 A 的清闲。</p>"
            )},
            {"title": "它如何反过来约束选择", "content": (
                "<p>机会成本不只是「事后算账」，更是<b>事前排序</b>：</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li><b>比较的是「最优替代」，不是「绝对水平」</b>——所以越优秀的人机会成本越高，越不该随便做事；</li>"
                "<li><b>时间与注意力的机会成本尤其高</b>——你读这本书的机会成本是读另一本更好的书；</li>"
                "<li><b>决策前先问「我放弃了什么」</b>，而不是「我能得到什么」。</li>"
                "</ul>"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>这与「反过来想」同源："
                "把「不做什么」摆上台面，往往比「做什么」更重要。"
                "巴菲特的能力圈原则本质上就是：<b>机会成本太高时，宁可空仓</b>。</p>"
            )},
        ],
    }


# =====================================================================
# 6) 反过来想：最弱环节决定生死
# =====================================================================
def build_inversion():
    n, pw, pr = 8, 50, 10
    inv = K.inversion(n, pw, pr)
    fixg, polg = _n(inv["fix_weakest_gain"]), _n(inv["polish_rest_gain"])
    return {
        "lesson": {
            "title": "反过来想：最弱环节决定生死",
            "subtitle": "芒格：「如果我不能比对手更清楚地知道我会死在哪里，我就不去那个地方。」",
            "problem": (
                "<p>一笔投资要连续通过 <b>8 道关卡</b>（研究、估值、买点、仓位、持有、退出……），"
                "任何一道失败，全盘归零。</p>"
                "<p class='mt-2'>其中<b>最弱的一道</b>失败率高达 <b>50%</b>，其余七道各 <b>10%</b>。</p>"
                "<p class='mt-2'>不问「怎么成功」，反过来问："
                "<span class='text-rose-600 font-semibold'>先修哪一道最值钱？</span>"
                "拖动滑块，比一比「先堵最弱的洞」与「全员优化」。</p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "inversion", "caption": "最弱环节决定整体存活率"},
            "view": {"xRange": [0, 1], "yRange": [0, 1]},
            "params": [
                {"name": "n", "label": "必要环节数 n", "min": 1, "max": 12, "step": 1, "value": n, "unit": " 环", "digits": 0},
                {"name": "pw", "label": "最弱一环的失败率", "min": 1, "max": 90, "step": 1, "value": pw, "unit": "%", "digits": 0},
                {"name": "pr", "label": "其余各环的失败率", "min": 1, "max": 30, "step": 0.5, "value": pr, "unit": "%", "digits": 1},
            ],
            "scalars": [
                {"name": "Fw", "expr": "1-pw/100"},
                {"name": "Fr", "expr": "1-pr/100"},
                {"name": "Sw", "expr": "Fw*Fr^(n-1)"},
                {"name": "Sc", "expr": "Fr^n"},
                {"name": "Sp", "expr": "Fw*(1-pr/200)^(n-1)"},
                {"name": "FixGain", "expr": "Fr/Fw"},
                {"name": "PolGain", "expr": "Sp/Sw"},
            ],
            "readouts": [
                {"id": "s", "label": "整体存活率 S = ∏(1−pᵢ)", "type": "expr", "expr": "Sw*100", "digits": 1, "unit": "%", "highlight": True},
                {"id": "fail", "label": "整体失败率 1−S", "type": "expr", "expr": "(1-Sw)*100", "digits": 1, "unit": "%", "color": "#dc2626"},
                {"id": "fixg", "label": "先堵最弱一环 → 存活率 ×", "type": "expr", "expr": "FixGain", "digits": 2, "unit": " 倍", "color": "#059669"},
                {"id": "polg", "label": "其余各环失败率减半 → ×", "type": "expr", "expr": "PolGain", "digits": 2, "unit": " 倍", "color": "#0891b2"},
                {"id": "ceil", "label": "存活率上限（最弱环也修到普通水平）", "type": "expr", "expr": "Sc*100", "digits": 1, "unit": "%", "color": "#78716c"},
                {"id": "ok", "label": "存活是否过半", "type": "status", "expr": "Sw", "op": ">=", "rhs": 0.5, "okText": "存活率过半", "badText": "存活率不足一半"},
            ],
            "legend": [
                {"color": "#dc2626", "text": "最弱一环 / 现状"},
                {"color": "#57534e", "text": "其余环节"},
                {"color": "#059669", "text": "先堵最弱的洞"},
                {"color": "#0891b2", "text": "全员优化"},
            ],
        },
        "steps": [
            {"title": "把「怎么成功」换成「怎么失败」", "content": (
                "<p>逆向思维不只是姿态——它把问题变成了一个<b>可以相乘的量</b>。"
                "把一个计划拆成 $n$ 个必要环节：只要一环断掉，整体归零。"
                "于是整体存活率就是各环存活率的<b>连乘</b>：</p>"
                "$$S = (1-p_w)(1-p_r)^{n-1}$$"
                "<p>其中 $p_w$ 是最弱那一环的失败率，$p_r$ 是其余各环的失败率。</p>"
                "<p class='mt-2 text-stone-500 text-xs'>注意：串联系统的乘积与各环的排列顺序无关，"
                "所以「最弱」放在链条哪一段都一样——重要的不是它<b>在哪</b>，而是它<b>有多弱</b>。</p>"
            )},
            {"title": "代入默认参数", "content": (
                "<p>8 道关卡，最弱一环 50%、其余 10%：</p>"
                "$$S = 0.5 \\times 0.9^{7} = " + f"{_n(inv['S']):.4f}" + "$$"
                "<p>存活率只有 <b>" + f"{_n(inv['S']) * 100:.1f}" + "%</b>——"
                "尽管七道普通关卡每一道都做到了 90%。"
                "整体失败率 <b>" + f"{_n(inv['fail']) * 100:.1f}" + "%</b>，"
                "其中 <b>" + f"{_n(inv['fatal_share']) * 100:.0f}" + "%</b> 可以直接归因于最弱的那一环。</p>"
            )},
            {"title": "两种改法，比大小", "content": (
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li><b>策略 A · 先堵最弱的洞</b>：把 50% 修到 10%，存活率 <b>×"
                + f"{fixg:.2f}" + "</b>（$= 0.9/0.5$）</li>"
                "<li><b>策略 B · 全员优化</b>：其余七道各从 10% 再降到 5%，存活率 <b>×"
                + f"{polg:.2f}" + "</b></li>"
                "</ul>"
                "<p class='mt-2'>先修一个洞，胜过把七个环节都改进一遍——"
                "<b>乘法里，最小的那个因子说话最响。</b></p>"
            )},
            {"title": "天花板：环节越多，越够不着", "content": (
                "<p>就算把最弱那一环也修到 10%，存活率上限也只有</p>"
                "$$S_{\\max} = 0.9^{8} = " + f"{_n(inv['ceiling']):.4f}" + "$$"
                "<p>依然<b>不到一半</b>。要 $S \\ge 0.5$，最弱一环的失败率必须低于</p>"
                "$$p_w \\le 1 - \\frac{1}{2(1-p_r)^{n-1}}$$"
                "<p>代入 $p_r = 0.1,\\ n = 8$ 得 <b>" + f"{_n(inv['pw_limit_for_half']):.3f}"
                + "</b>——是个<b>负数</b>。也就是说，在这个结构下无论把最弱环节修得多好，"
                "存活率都过不了一半。</p>"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>这就是芒格把"
                "「<b>先排除愚蠢</b>」排在「追求卓越」前面的算术理由："
                "成功要走完整条链，失败只需断一环。先删掉失败路径，再谈收益。</p>"
            )},
        ],
    }


# =====================================================================
# 7) 激励优先：佣金决定行为
# =====================================================================
def build_incentive():
    c = 20
    inc = K.incentive(c)
    c_align = _n(inc["align_commission"])
    loss_share = _n(inc["loss_share"])
    hi = K.incentive(60)
    return {
        "lesson": {
            "title": "激励优先：佣金决定行为",
            "subtitle": "芒格：「永远不要怀疑，一个既得利益者会不顾一切地维护他的既得利益。」",
            "problem": (
                "<p>你雇人卖东西。<b>顾客</b>希望服务做到位——太少不好用，太多是浪费。"
                "顾客的价值是 $V(x) = 100x - 5x^2$，最优在 $x = 10$。</p>"
                "<p class='mt-2'><b>销售员</b>按每单位 <b>20 元</b>提成拿钱，"
                "同时要付出努力成本，收入是 $U(x) = 20x - 2x^2$。</p>"
                "<p class='mt-2'>他会做到多少？"
                "<span class='text-rose-600 font-semibold'>他不是「不够努力」——他算得很对。</span>"
                "拖动滑块改提成，看两个人的最优解怎么分岔。</p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "incentive", "caption": "委托人与代理人的最优努力"},
            "view": {"xRange": [0, 30], "yRange": [0, 600]},
            "params": [
                {"name": "commission", "label": "每单提成", "min": 0, "max": 80, "step": 1, "value": c, "unit": " 元", "digits": 0},
            ],
            "scalars": [
                {"name": "vLin", "expr": "100"},
                {"name": "vQuad", "expr": "5"},
                {"name": "cQuad", "expr": "2"},
                {"name": "xP", "expr": "vLin/(2*vQuad)"},
                {"name": "xA", "expr": "commission/(2*cQuad)"},
                {"name": "xMax", "expr": "max(24, 1.4*max(xP, xA))"},
                {"name": "Vopt", "expr": "vLin*xP - vQuad*xP^2"},
                {"name": "VatA", "expr": "vLin*xA - vQuad*xA^2"},
                {"name": "Loss", "expr": "Vopt - VatA"},
                {"name": "LossShare", "expr": "Loss/Vopt"},
                {"name": "AlignC", "expr": "2*cQuad*xP"},
                {"name": "Aligned", "expr": "abs(xA-xP) < 0.5 ? 1 : 0"},
            ],
            "readouts": [
                {"id": "xa", "label": "代理人最优 x_A = 提成/(2·成本系数)", "type": "expr", "expr": "xA", "digits": 2, "unit": "", "highlight": True},
                {"id": "xp", "label": "委托人最优 x_P", "type": "expr", "expr": "xP", "digits": 2, "unit": "", "color": "#059669"},
                {"id": "mis", "label": "错配 x_A − x_P", "type": "expr", "expr": "xA-xP", "digits": 2, "unit": "", "color": "#dc2626"},
                {"id": "loss", "label": "顾客被白损失的价值", "type": "expr", "expr": "Loss", "digits": 0, "unit": "", "color": "#dc2626"},
                {"id": "lossPct", "label": "损失占顾客最优价值的比例", "type": "expr", "expr": "LossShare*100", "digits": 1, "unit": "%", "color": "#dc2626"},
                {"id": "alignC", "label": "恰好对齐所需的提成", "type": "expr", "expr": "AlignC", "digits": 0, "unit": " 元", "color": "#78716c"},
                {"id": "ok", "label": "激励是否对齐", "type": "status", "expr": "abs(xA-xP)", "op": "<", "rhs": 0.5, "okText": "已对齐：代理人想做的事就是该做的事", "badText": "错配：代理人不会做你想做的事"},
            ],
            "legend": [
                {"color": "#b45309", "text": "顾客价值 V(x)"},
                {"color": "#0891b2", "text": "代理人收入 U(x)"},
                {"color": "#dc2626", "text": "错配区间"},
            ],
        },
        "steps": [
            {"title": "把两边的最优点分别写出来", "content": (
                "<p>委托人（顾客）价值：$V(x) = v_{lin}x - v_{quad}x^2$，"
                "对 $x$ 求导置零得 $x_P = \\dfrac{v_{lin}}{2v_{quad}}$。</p>"
                "<p>代理人效用：$U(x) = c\\,x - c_{quad}x^2$，"
                "对 $x$ 求导置零得 $x_A = \\dfrac{c}{2c_{quad}}$。</p>"
                "<p>代入 $v_{lin}=100,\\ v_{quad}=5,\\ c_{quad}=2$：</p>"
                "$$x_P = \\frac{100}{10} = " + f"{_n(inc['x_p']):.0f}" + ",\\qquad "
                "x_A = \\frac{c}{4}$$"
                "<p><b>关键在于：$x_A$ 只跟提成 $c$ 有关，跟顾客想要什么毫无关系。</b></p>"
            )},
            {"title": "提成 20 元时发生了什么", "content": (
                "<p>代理人算自己的账：$x_A = 20/4 = " + f"{_n(inc['x_a']):.0f}" + "$。"
                "顾客想要 " + f"{_n(inc['x_p']):.0f}" + "。"
                "错配 <b>" + f"{_n(inc['misalign'] * -1):.0f}" + " 个单位</b>——只做到一半。</p>"
                "<p>顾客价值从 $V(" + f"{_n(inc['x_p']):.0f}" + ") = " + f"{_n(inc['V_at_opt']):.0f}"
                + "$ 掉到 $V(" + f"{_n(inc['x_a']):.0f}" + ") = " + f"{_n(inc['V_at_agent']):.0f}"
                + "$，<b>净损失 " + f"{_n(inc['client_loss']):.0f}" + "</b>，"
                "占其最优价值的 <b>" + f"{loss_share * 100:.1f}" + "%</b>。</p>"
                "<p class='mt-2 text-stone-500 text-xs'>注意这里的损失不是「代理人偷懒」造成的，"
                "而是<b>两套目标函数本来就不同</b>造成的——换一个更勤奋的人也一样。</p>"
            )},
            {"title": "对齐点在哪", "content": (
                "<p>让两个最优点重合，解 $x_A = x_P$：</p>"
                "$$c^{*} = 2c_{quad}\\cdot x_P = 2 \\times 2 \\times 10 = "
                + f"{c_align:.0f}" + "\\ \\text{元}$$"
                "<p>只有提成恰好等于 <b>" + f"{c_align:.0f}" + " 元</b>时，"
                "代理人自己最想做的事，才正好是顾客最想让他做的事。</p>"
                "<p class='mt-2'>而且两侧是<b>对称</b>的：把提成提到 60 元，"
                "$x_A = 15$ 变成过度推销，顾客同样损失 <b>"
                + f"{_n(hi['client_loss']):.0f}" + "</b>。"
                "太少是消极，太多是过度——<b>两种错法的损失一模一样。</b></p>"
            )},
            {"title": "为什么「说教」没用", "content": (
                "<p>芒格的原话是：永远不要怀疑一个既得利益者会维护他的既得利益。"
                "上面的算术给出了它的精确含义：</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li>代理人的最优解是<b>提成的函数</b>，不是人品的函数；</li>"
                "<li>想改变行为，要么改 $c$，要么改 $c_{quad}$（努力成本），"
                "要么<b>换一种计酬方式</b>——而不是开会强调责任心；</li>"
                "<li>看到任何行为，先找背后的激励结构：<b>激励 &gt; 说教</b>。</li>"
                "</ul>"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>"
                "佣金导向的销售必然过度推销；按住院天数收费的医院必然倾向多留病人。"
                "这不说明从业者坏，只说明<b>激励结构被设计错了</b>。</p>"
            )},
        ],
    }


# =====================================================================
# 8) 能力圈：边界比大小重要
# =====================================================================
def build_competence():
    w, si, so, mos = 20, 10, 40, 20
    cp = K.competence(w / 100, si, so, 0, mos / 100)
    return {
        "lesson": {
            "title": "能力圈：边界比大小重要",
            "subtitle": "「知道边界在哪，比边界有多大更重要。」——因为边界直接决定你的风险预算",
            "problem": (
                "<p>你要买一个资产。你的组合里，<b>圈内</b>部分你估得准（估值误差 $\\sigma_{in} = 10$），"
                "<b>圈外</b>部分你看不懂（$\\sigma_{out} = 40$）。</p>"
                "<p class='mt-2'>现在有 <b>20%</b> 的仓位放在圈外。安全边际照旧留 20%。</p>"
                "<p class='mt-2'>问题：<span class='text-rose-600 font-semibold'>"
                "这 20% 的圈外暴露，会让整体风险涨多少？</span>"
                "拖动滑块，看一条曲线就够了。</p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "competence", "caption": "圈外暴露 → σ → 击穿概率"},
            "view": {"xRange": [0, 1], "yRange": [0, 0.3]},
            "params": [
                {"name": "w", "label": "圈外暴露比例 w", "min": 0, "max": 80, "step": 1, "value": w, "unit": "%", "digits": 0},
                {"name": "sigIn", "label": "圈内估值误差 σ_in", "min": 5, "max": 30, "step": 1, "value": si, "unit": "", "digits": 0},
                {"name": "sigOut", "label": "圈外估值误差 σ_out", "min": 15, "max": 80, "step": 1, "value": so, "unit": "", "digits": 0},
                {"name": "mos", "label": "安全边际 MOS", "min": 5, "max": 40, "step": 1, "value": mos, "unit": "%", "digits": 0},
            ],
            "scalars": [
                {"name": "W", "expr": "w/100"},
                {"name": "mu", "expr": "100"},
                {"name": "rho", "expr": "0"},
                {"name": "si", "expr": "sigIn"},
                {"name": "so", "expr": "sigOut"},
                {"name": "Price", "expr": "mu*(1-mos/100)"},
                {"name": "Var", "expr": "(1-W)^2*si^2 + W^2*so^2 + 2*W*(1-W)*rho*si*so"},
                {"name": "SigmaNow", "expr": "sqrt(Var)"},
                {"name": "z", "expr": "(Price-mu)/SigmaNow"},
                {"name": "Prob", "expr": "0.5*(1+erf(z/sqrt(2)))"},
                {"name": "z0", "expr": "-(mos/100)*mu/si"},
                {"name": "ProbPure", "expr": "0.5*(1+erf(z0/sqrt(2)))"},
                {"name": "ProbRatio", "expr": "Prob/ProbPure"},
                {"name": "VarShare", "expr": "W^2*so^2/Var"},
                {"name": "WCrit", "expr": "si/(si+so)"},
                {"name": "Safe", "expr": "Prob < 0.05 ? 1 : 0"},
            ],
            "readouts": [
                {"id": "sig", "label": "组合估值误差 σ", "type": "expr", "expr": "SigmaNow", "digits": 2, "unit": "", "highlight": True},
                {"id": "varshare", "label": "圈外占了多少方差", "type": "expr", "expr": "VarShare*100", "digits": 1, "unit": "%", "color": "#0891b2"},
                {"id": "prob", "label": "击穿概率 P(真实价值 < 买价)", "type": "expr", "expr": "Prob*100", "digits": 2, "unit": "%", "color": "#dc2626"},
                {"id": "pure", "label": "纯圈内时的击穿概率", "type": "expr", "expr": "ProbPure*100", "digits": 2, "unit": "%", "color": "#78716c"},
                {"id": "ratio", "label": "风险放大倍数", "type": "expr", "expr": "ProbRatio", "digits": 2, "unit": " 倍", "color": "#dc2626"},
                {"id": "wcrit", "label": "临界暴露 w*（圈外吃掉一半方差）", "type": "expr", "expr": "WCrit*100", "digits": 1, "unit": "%", "color": "#0891b2"},
                {"id": "ok", "label": "击穿概率是否低于 5%", "type": "status", "expr": "Prob", "op": "<", "rhs": 0.05, "okText": "在 5% 警戒线以内", "badText": "击穿概率已超过 5%"},
            ],
            "legend": [
                {"color": "#dc2626", "text": "击穿概率随圈外暴露上升"},
                {"color": "#0891b2", "text": "临界 w*：圈外方差 = 圈内方差"},
                {"color": "#059669", "text": "5% 警戒线"},
            ],
        },
        "steps": [
            {"title": "能力圈的量化含义", "content": (
                "<p>「能力圈」听起来像一句态度宣言，但它落在数学上就是一个数："
                "<b>你的估计误差 σ</b>。</p>"
                "<p>圈内看得懂，估值误差小（$\\sigma_{in}$）；圈外看不懂，"
                "误差大（$\\sigma_{out}$）。所以能力圈的边界，"
                "本质上是你愿意承受的 <b>σ 的边界</b>。</p>"
                "<p class='mt-2'>这正好接上第 4 节的安全边际："
                "<b>击穿概率 $= \\Phi((P-\\mu)/\\sigma)$，σ 在分母上。</b></p>"
            )},
            {"title": "组合的 σ 怎么合成", "content": (
                "<p>设圈外占比 $w$，两部分估值的相关系数 $\\rho$：</p>"
                "$$\\sigma = \\sqrt{(1-w)^2\\sigma_{in}^2 + w^2\\sigma_{out}^2"
                " + 2w(1-w)\\rho\\,\\sigma_{in}\\sigma_{out}}$$"
                "<p>本页取 $\\rho = 0$（互不相关），式子只剩前两项。"
                "注意它是<b>平方相加</b>——不是加权平均。"
                "这就是为什么圈外的一小块，能顶掉圈内的一大块。</p>"
            )},
            {"title": "代入 20% 的圈外暴露", "content": (
                "<p>$w = 0.2,\\ \\sigma_{in} = 10,\\ \\sigma_{out} = 40$：</p>"
                "$$\\sigma^2 = 0.8^2 \\times 10^2 + 0.2^2 \\times 40^2"
                " = " + f"{0.8 ** 2 * 100:.0f}" + " + " + f"{0.2 ** 2 * 1600:.0f}" + " = "
                + f"{_n(cp['sigma']) ** 2:.0f}" + "$$"
                "$$\\sigma = " + f"{_n(cp['sigma']):.2f}" + "$$"
                "<p><b>圈外只占 20% 的仓位，却贡献了整整 "
                + f"{_n(cp['var_share_out']) * 100:.0f}" + "% 的方差。</b>"
                "临界点就是 $w^{*} = \\dfrac{\\sigma_{in}}{\\sigma_{in}+\\sigma_{out}} = "
                + f"{_n(cp['w_crit']) * 100:.0f}" + "\\%$——"
                "在这一点上，两块方差的贡献恰好相等。</p>"
                "<p class='mt-2'>这就是「<b>边界比大小重要</b>」的精确版本："
                "你不需要能力圈很大，但必须知道它在哪，"
                "因为<b>越界的一小块会立刻主导整体风险</b>。</p>"
            )},
            {"title": "换算成击穿概率", "content": (
                "<p>买价取安全边际 20% 的位置：$P = \\mu(1-0.2) = " + f"{_n(cp['price']):.0f}" + "$。"
                "标准分</p>"
                "$$z = \\frac{P-\\mu}{\\sigma} = \\frac{-20}{" + f"{_n(cp['sigma']):.2f}"
                + "} = " + f"{_n(cp['z']):.3f}" + "$$"
                "<p>击穿概率 $= " + f"{_n(cp['prob']) * 100:.2f}" + "\\%$，"
                "而纯圈内只要 $ " + f"{_n(cp['prob_pure']) * 100:.2f}" + "\\%$——"
                "风险被放大了 <b>" + f"{_n(cp['prob_ratio']):.2f}" + " 倍</b>。</p>"
                "<p class='mt-2 text-stone-500 text-xs'>换句话说："
                "同样留 20% 的安全边际，<b>只要把资产放进圈外，边际就不够用了</b>。"
                "巴菲特的「只买看得懂的生意」不是保守，而是把 σ 锁在分母的一个小区间里。</p>"
            )},
        ],
    }


# =====================================================================
# 9) Lollapalooza：多个倾向同向叠加
# =====================================================================
def build_lollapalooza():
    n, amt = 4, 50
    lp = K.lollapalooza(n, amt / 100)
    return {
        "lesson": {
            "title": "Lollapalooza：多个倾向同向叠加",
            "subtitle": "芒格：「当几种心理倾向同时同向作用时，结果会超出任何单一倾向的量级。」",
            "problem": (
                "<p>一条心理倾向会把你的冲动放大 <b>50%</b>。这不算多——"
                "理性一点就压得住。</p>"
                "<p class='mt-2'>但如果 <b>4 条</b>倾向<b>同时、同方向</b>作用呢？</p>"
                "<p class='mt-2'>直觉会把它们加起来：$1 + 4 \\times 0.5 = 3$ 倍。"
                "而真实结果是"
                "<span class='text-rose-600 font-semibold'>$1.5^4 = "
                + f"{_n(lp['product']):.2f}" + "$ 倍</span>。</p>"
                "<p class='mt-2'>拖动滑块，看缺口怎么张开。</p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "lollapalooza", "caption": "乘法叠加 vs 线性直觉"},
            "view": {"xRange": [1, 10], "yRange": [0, 12]},
            "params": [
                {"name": "n", "label": "同向倾向条数 n", "min": 1, "max": 10, "step": 1, "value": n, "unit": " 条", "digits": 0},
                {"name": "amt", "label": "单条倾向的放大率 a", "min": 10, "max": 120, "step": 5, "value": amt, "unit": "%", "digits": 0},
            ],
            "scalars": [
                {"name": "a", "expr": "amt/100"},
                {"name": "nMax", "expr": "10"},
                {"name": "Prod", "expr": "(1+a)^n"},
                {"name": "Lin", "expr": "1+n*a"},
                {"name": "Excess", "expr": "Prod/Lin"},
                {"name": "ExtraPct", "expr": "(Prod-Lin)/Lin"},
            ],
            "readouts": [
                {"id": "prod", "label": "乘法叠加 (1+a)ⁿ", "type": "expr", "expr": "Prod", "digits": 2, "unit": " 倍", "highlight": True},
                {"id": "lin", "label": "线性直觉 1+na", "type": "expr", "expr": "Lin", "digits": 2, "unit": " 倍", "color": "#0891b2"},
                {"id": "extra", "label": "超出线性直觉的比例", "type": "expr", "expr": "ExtraPct*100", "digits": 1, "unit": "%", "color": "#dc2626"},
                {"id": "ex", "label": "实际 / 直觉", "type": "expr", "expr": "Excess", "digits": 2, "unit": " 倍", "color": "#dc2626"},
                {"id": "ok", "label": "是否出现超线性", "type": "status", "expr": "Excess", "op": ">", "rhs": 1.0, "okText": "已超线性——多条倾向在互相喂养", "badText": "尚未出现叠加效应"},
            ],
            "legend": [
                {"color": "#b45309", "text": "乘法叠加 (1+a)ⁿ"},
                {"color": "#0891b2", "text": "线性直觉 1+na"},
                {"color": "#dc2626", "text": "被直觉漏掉的部分"},
            ],
        },
        "steps": [
            {"title": "两个公式，只差一个位置", "content": (
                "<p>单条倾向把冲动放大 $(1+a)$ 倍。$n$ 条<b>同向</b>叠加：</p>"
                "$$\\text{真实} = (1+a)^{n} \\qquad\\text{直觉} = 1 + na$$"
                "<p>差别只在 $a$ 是乘在<b>外面</b>还是里面的常数上。"
                "指数放在外面，是复利式放大；直觉却是加法。</p>"
                "<p class='mt-2'>$n = 1$ 时两者完全相等（都是 $1+a$）——"
                "所以单条倾向看不出问题，<b>问题只在叠加时才爆发</b>。</p>"
            )},
            {"title": "代入 4 条 ×50%", "content": (
                "$$\\text{真实} = 1.5^{4} = " + f"{_n(lp['product']):.4f}" + "$$"
                "$$\\text{直觉} = 1 + 4 \\times 0.5 = " + f"{_n(lp['linear']):.0f}" + "$$"
                "<p>超出 <b>" + f"{_n(lp['extra_pct']) * 100:.1f}" + "%</b>。"
                "四条各 50% 的倾向，叠出 5 倍多的冲动——"
                "而每个人都以为只是「加了 4 个 50%」。</p>"
            )},
            {"title": "为什么是指数：互相喂养", "content": (
                "<p>把过程拆开看就明白了：第 1 条把冲动抬到 1.5 倍，"
                "第 2 条是在这个 1.5 倍<b>上面</b>再抬 50%，"
                "第 3 条又在前一个结果上抬——每一条都在<b>更高的底座</b>上发力。</p>"
                "$$1.5 \\to 2.25 \\to 3.375 \\to " + f"{_n(lp['product']):.3f}" + "$$"
                "<p>把它和「线性相加」的 $1.5 \\to 2.0 \\to 2.5 \\to 3.0$ 对照，"
                "差距一眼就出来了：<b>直觉假设各条倾向互不影响，"
                "而真实世界里它们会互相喂养。</b></p>"
                "<p class='mt-2 text-stone-500 text-xs'>在 a = "
                + f"{_n(lp['a']) * 100:.0f}" + "% 时，只要 "
                + str(lp["n_for_double"] or "—") + " 条同向倾向，"
                "就能让放大倍数<b>超过线性直觉的两倍</b>。</p>"
            )},
            {"title": "它长什么样", "content": (
                "<p>芒格举的例子：</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li><b>拍卖会</b>：社会认同 + 竞争心理 + 稀缺感 + 承诺一致 → 非理性高价；</li>"
                "<li><b>促销排队</b>：稀缺 + 社会认同 → 明知不缺货仍然排队；</li>"
                "<li><b>传销 / 邪教</b>：权威 + 社会认同 + 承诺一致 + 剥夺睡眠 → 全面控制。</li>"
                "</ul>"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>"
                "所以芒格的应对不是「不要有偏见」（人的倾向无法清零），"
                "而是<b>识别出「几个倾向正在同向叠加」</b>这种结构。"
                "一旦识别出来，就知道自己正处于指数曲线的陡坡上，该做的动作是<b>离场</b>，"
                "而不是「再理性分析一下」。</p>"
            )},
        ],
    }


# =====================================================================
# 10) 25 条误判倾向：清单把风险指数级压低
# =====================================================================
BIASES = [
    ("奖励与惩罚超级反应", "拿谁的钱就为谁说话，激励压倒一切", "先画激励结构图"),
    ("喜爱/热爱", "喜欢的人做什么都对", "把人和事分开评估"),
    ("讨厌/憎恨", "讨厌的人做什么都错", "同上，先剥离情绪再看证据"),
    ("避免怀疑", "急着下结论以消除不确定感", "强制给自己一个「再等等」"),
    ("避免不一致", "公开承诺后很难改口", "公开表态前先内部想清楚"),
    ("好奇心", "唯一纯正的建设性倾向", "用它去研究，而不是用它去冒险"),
    ("康德式公平", "要求程序公平，否则宁可两败", "分清「公平」与「划算」"),
    ("嫉妒", "见不得别人好，驱动非理性竞争", "只跟自己的目标比"),
    ("回馈", "受了小恩小惠就难以拒绝", "警惕先给好处的一方"),
    ("简单联想", "因为 A 像 B 就以为 A 是 B", "问「这个类比成立在哪一步」"),
    ("避免痛苦的否认", "太痛的事实干脆不信", "把坏消息写下来，逼自己看"),
    ("自视过高", "高估自己的能力与判断", "记录预测，用命中率打分"),
    ("过度乐观", "系统性地低估失败概率", "用基率而不是感觉"),
    ("被剥夺超级反应", "失去 100 的痛远大于得到 100", "用「不作为」的代价做对照"),
    ("社会认同", "看别人怎么做就怎么做", "问「如果没人看到，我还会做吗」"),
    ("对比误反应", "被前后对比牵着走，而非绝对值", "把绝对价格单独看一遍"),
    ("压力影响", "高压下判断力急剧下降", "重大决定不在压力下做"),
    ("易得性误衡量", "容易想起的事被高估概率", "用基率，不用记忆"),
    ("不用就忘", "不常练的能力会退化", "关键技能定期复习"),
    ("化学物质误影响", "酒精药物直接损坏判断", "重大决策前保持清醒"),
    ("衰老误影响", "认知能力随年龄下降", "把决策交给更年轻的头脑复核"),
    ("权威误影响", "无条件听信专家", "问「他的专业和这个问题相关吗」"),
    ("废话", "说得多不等于说得对", "只在有信息量时开口"),
    ("重视理由", "给了理由（哪怕荒谬）就更易被接受", "要证据，不要理由"),
    ("Lollapalooza", "多个倾向同向叠加产生极端结果", "识别同向叠加，立刻离场"),
]


def build_bias():
    k, hit, a = 4, 50, 0.5
    ck_ = K.checklist(k, a, hit / 100)
    rows = "".join(
        "<tr class='border-b border-stone-100'>"
        f"<td class='py-1.5 pr-3 text-stone-400 font-mono text-xs align-top'>{i:02d}</td>"
        f"<td class='py-1.5 pr-3 font-semibold text-stone-800 align-top'>{name}</td>"
        f"<td class='py-1.5 pr-3 text-stone-600 align-top'>{desc}</td>"
        f"<td class='py-1.5 text-stone-500 text-xs align-top'>{fix}</td>"
        "</tr>"
        for i, (name, desc, fix) in enumerate(BIASES, 1))
    return {
        "lesson": {
            "title": "误判清单：把风险指数级压下去",
            "subtitle": "芒格：「聪明人没有不每天用清单的。」——不是不犯错，而是不让错误叠加",
            "problem": (
                "<p>第 9 节说：$k$ 条同向倾向会把冲动放大 $(1+a)^k$ 倍。"
                "$k = 4$、$a = 50\\%$ 时就是 " + f"{_n(ck_['gross']):.2f}" + " 倍。</p>"
                "<p class='mt-2'>清单能做什么？它不能消除倾向，"
                "但每条倾向被拦下的概率是 <b>50%</b>（只要真的逐条问过）。</p>"
                "<p class='mt-2'>拦下一条，就少一个「互相喂养」的因子。"
                "拖动滑块看：<span class='text-rose-600 font-semibold'>"
                "同向倾向越多，清单越值钱。</span></p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "checklist", "caption": "拦截率随同向倾向条数上升"},
            "view": {"xRange": [1, 10], "yRange": [0, 1]},
            "params": [
                {"name": "kk", "label": "同时激活的同向倾向条数 k", "min": 1, "max": 10, "step": 1, "value": k, "unit": " 条", "digits": 0},
                {"name": "hit", "label": "清单对单条倾向的拦截率", "min": 10, "max": 90, "step": 5, "value": hit, "unit": "%", "digits": 0},
            ],
            "scalars": [
                {"name": "a", "expr": "0.5"},
                {"name": "kMax", "expr": "10"},
                {"name": "Gross", "expr": "(1+a)^kk"},
                {"name": "Net", "expr": "((1+a)*(1-hit/100))^kk"},
                {"name": "Blocked", "expr": "1-(1-hit/100)^kk"},
                {"name": "Cut", "expr": "Gross/Net"},
            ],
            "readouts": [
                {"id": "blocked", "label": "被清单拦下的比例", "type": "expr", "expr": "Blocked*100", "digits": 1, "unit": "%", "highlight": True},
                {"id": "gross", "label": "不上清单：冲动放大", "type": "expr", "expr": "Gross", "digits": 2, "unit": " 倍", "color": "#dc2626"},
                {"id": "net", "label": "上清单后：残余放大", "type": "expr", "expr": "Net", "digits": 3, "unit": " 倍", "color": "#059669"},
                {"id": "cut", "label": "风险被压低", "type": "expr", "expr": "Cut", "digits": 2, "unit": " 倍", "color": "#059669"},
                {"id": "ok", "label": "残余放大是否已被压到 1 倍以下", "type": "status", "expr": "Net", "op": "<", "rhs": 1.0, "okText": "已压到无放大", "badText": "仍处于放大状态"},
            ],
            "legend": [
                {"color": "#059669", "text": "上清单后的拦截率"},
                {"color": "#78716c", "text": "单条拦截率（清单基线）"},
            ],
        },
        "steps": [
            {"title": "清单的数学形式", "content": (
                "<p>每一条倾向被清单拦下的概率是 $h$。那么 $k$ 条同向倾向的<b>残余放大</b>是</p>"
                "$$\\text{残余} = (1+a)^k (1-h)^k = \\big[(1+a)(1-h)\\big]^{k}$$"
                "<p>而<b>拦截率</b>只跟 $h$ 和 $k$ 有关：</p>"
                "$$\\text{拦截率} = 1 - (1-h)^{k}$$"
                "<p class='mt-2'>注意 $(1-h)^k$ 里 $k$ 在指数上——"
                "<b>拦截率随条数呈指数逼近 100%</b>，而不是线性地涨。</p>"
            )},
            {"title": "代入 k = 4、h = 50%", "content": (
                "$$h = 0.5,\\quad k = 4$$"
                "$$\\text{拦截率} = 1 - 0.5^{4} = " + f"{_n(ck_['blocked']):.4f}"
                " = " + f"{_n(ck_['blocked']) * 100:.1f}" + "\\%$$"
                "$$\\text{残余放大} = (1.5 \\times 0.5)^{4} = 0.75^{4} = "
                + f"{_n(ck_['net']):.4f}" + " < 1$$"
                "<p>冲动从 <b>" + f"{_n(ck_['gross']):.2f}" + " 倍</b>降到 <b>"
                + f"{_n(ck_['net']):.3f}" + " 倍</b>——"
                "拦掉 <b>" + f"{_n(ck_['blocked']) * 100:.1f}" + "%</b>，风险被压低 <b>"
                + f"{_n(ck_['cut']):.1f}" + " 倍</b>。</p>"
                "<p class='mt-2 text-stone-500 text-xs'>关键在于："
                "$h = 50\\%$ 听起来只是「一份一半的用处的清单」，"
                "但 $k = 4$ 条同向倾向时，它把整条指数曲线压到了 1 以下。"
                "<b>越是容易出错的结构，清单越值钱。</b></p>"
            )},
            {"title": "25 条人类误判倾向（芒格原表）", "content": (
                "<p>下面就是芒格在《人类误判心理学》里列出的 25 条。"
                "清单的用法不是「防止有倾向」，而是<b>在重大决策前逐条问一遍</b>："
                "这一条现在有没有在起作用？</p>"
                "<div class='mt-3 overflow-x-auto'><table class='w-full text-sm'>"
                "<thead><tr class='border-b-2 border-stone-300 text-left text-xs uppercase text-stone-400'>"
                "<th class='py-2 pr-3' style='width:2rem'>#</th>"
                "<th class='py-2 pr-3'>倾向</th><th class='py-2 pr-3'>它怎么害你</th>"
                "<th class='py-2'>对策</th></tr></thead>"
                "<tbody>" + rows + "</tbody></table></div>"
                "<p class='mt-3 text-stone-500 text-xs'>其中第 25 条就是上一页的 Lollapalooza——"
                "它不是又一条倾向，而是<b>前面 24 条叠加起来</b>的那种结构性风险。"
                "所以清单要一直问到第 25 条为止。</p>"
            )},
            {"title": "怎么真的用起来", "content": (
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li><b>只用在高风险决策上</b>：不可逆、金额大、时间紧——这三类才值得走一遍 25 条；</li>"
                "<li><b>逐条问「此刻它在不在」</b>，而不是「我有没有这个毛病」——"
                "前者能得到证据，后者只会得到自我辩护；</li>"
                "<li><b>优先查同向叠加</b>：一旦有 3–4 条指向同一个方向，"
                "就停止寻找理由，改找<b>离场</b>的理由；</li>"
                "<li><b>把它写下来</b>：写在纸上的清单才有 $h$；"
                "存在脑子里的清单，$h$ 趋近于 0。</li>"
                "</ul>"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>"
                "「反过来想」+「激励优先」+「能力圈」+「清单」，"
                "四件事其实在说同一句话：<b>先保证自己不犯大错，收益自然会来。</b></p>"
            )},
        ],
    }


# =====================================================================
# 11) 贴现：今天的一块钱比明天值钱
# =====================================================================
def build_dcf():
    cf0, g, r, tg, years = 100, 8, 10, 3, 10
    d = K.dcf(cf0, g, r, years, tg)
    share = _n(d["terminal_share"])
    sens = _n(d["rate_sensitivity"])
    return {
        "lesson": {
            "title": "贴现：今天的一块钱比明天值钱",
            "subtitle": "芒格：「内在价值就是未来现金流的贴现。」——复利的镜像，就是贴现",
            "problem": (
                "<p>一个资产首年产生 <b>100</b> 的现金流，未来 10 年按 <b>8%</b> 增长，"
                "此后按 <b>3%</b> 永续增长。你的贴现率是 <b>10%</b>。</p>"
                "<p class='mt-2'>它值多少？先别急着求和——真正的问题是："
                "<span class='text-rose-600 font-semibold'>这个估值里，有多大一部分来自第 10 年之后？</span></p>"
                "<p class='mt-2'>拖动滑块，尤其是那个永续增长率。</p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "dcf", "caption": "逐年现值 + 终值现值"},
            "view": {"xRange": [0, 12], "yRange": [0, 4000]},
            "params": [
                {"name": "cf0", "label": "首年现金流 CF₀", "min": 20, "max": 400, "step": 10, "value": cf0, "unit": "", "digits": 0},
                {"name": "g", "label": "显性期增长率 g", "min": 0, "max": 20, "step": 0.5, "value": g, "unit": "%", "digits": 1},
                {"name": "r", "label": "贴现率 r", "min": 5, "max": 25, "step": 0.5, "value": r, "unit": "%", "digits": 1},
                {"name": "tg", "label": "永续增长率 g∞", "min": 0, "max": 4, "step": 0.5, "value": tg, "unit": "%", "digits": 1},
                {"name": "years", "label": "显性期年数 N", "min": 3, "max": 20, "step": 1, "value": years, "unit": " 年", "digits": 0},
            ],
            "scalars": [
                {"name": "pvExplicit", "expr": "dcfExplicit(cf0,g,r,years)"},
                {"name": "pvTerminal", "expr": "dcfTerminal(cf0,g,r,tg,years)"},
                {"name": "V", "expr": "dcfExplicit(cf0,g,r,years)+dcfTerminal(cf0,g,r,tg,years)"},
                {"name": "termShare", "expr": "dcfTerminal(cf0,g,r,tg,years)/(dcfExplicit(cf0,g,r,years)+dcfTerminal(cf0,g,r,tg,years))"},
                {"name": "rateSens", "expr": "1-(dcfExplicit(cf0,g,r+1,years)+dcfTerminal(cf0,g,r+1,tg,years))/(dcfExplicit(cf0,g,r,years)+dcfTerminal(cf0,g,r,tg,years))"},
            ],
            "readouts": [
                {"id": "v", "label": "内在价值 V = 显性期 + 终值", "type": "expr", "expr": "V", "money": True, "unit": "", "highlight": True},
                {"id": "pex", "label": "显性期现值合计", "type": "expr", "expr": "pvExplicit", "money": True, "color": "#b45309"},
                {"id": "ptv", "label": "终值现值（N 年之后全部）", "type": "expr", "expr": "pvTerminal", "money": True, "color": "#dc2626"},
                {"id": "share", "label": "终值占内在价值的比例", "type": "expr", "expr": "termShare*100", "digits": 1, "unit": "%", "color": "#dc2626"},
                {"id": "sens", "label": "贴现率 +1% → 估值下跌", "type": "expr", "expr": "rateSens*100", "digits": 1, "unit": "%", "color": "#dc2626"},
                {"id": "ok", "label": "终值占比是否低于一半", "type": "status", "expr": "termShare", "op": "<", "rhs": 0.5, "okText": "估值主要来自已看得见的现金流", "badText": "估值一多半靠远期假设"},
            ],
            "legend": [
                {"color": "#b45309", "text": "显性期各年现金流现值"},
                {"color": "#dc2626", "text": "终值现值"},
                {"color": "#059669", "text": "内在价值"},
            ],
        },
        "steps": [
            {"title": "贴现：复利倒过来走", "content": (
                "<p>复利问「今天的钱明天值多少」，贴现问「明天的钱今天值多少」——"
                "同一个 $1/(1+r)^t$，方向相反。</p>"
                "$$V = \\sum_{t=1}^{N}\\frac{CF_0(1+g)^t}{(1+r)^t}"
                " + \\frac{1}{(1+r)^N}\\cdot\\frac{CF_0(1+g)^N(1+g_\\infty)}{r-g_\\infty}$$"
                "<p>右边第二项叫<b>终值</b>：第 $N$ 年之后所有现金流的现值打包成一个数。</p>"
                "<p>要求 $r > g_\\infty$。若不满足，级数发散——"
                "「永续增长快过贴现」本身就是一个不自洽的假设。</p>"
            )},
            {"title": "代入默认参数", "content": (
                "<p>$CF_0=100,\\ g=8\\%,\\ r=10\\%,\\ N=10,\\ g_\\infty=3\\%$：</p>"
                "$$\\text{显性期} = \\sum_{t=1}^{10}\\frac{100\\times1.08^t}{1.10^t} = "
                + f"{_n(d['pv_explicit']):.2f}" + "$$"
                "$$\\text{终值} = \\frac{" + f"{_n(d['cash_N1']):.2f}" + "}{0.10-0.03}"
                "\\cdot\\frac{1}{1.10^{10}} = " + f"{_n(d['pv_terminal']):.2f}" + "$$"
                "$$V = " + f"{_n(d['V']):.2f}" + "$$"
                "<p class='mt-2'>注意终值的算法：第 11 年现金流 $100\\times1.08^{10}\\times1.03 = "
                + f"{_n(d['cash_N1']):.2f}" + "$，除以 $r-g_\\infty$，再贴现回来。</p>"
            )},
            {"title": "真正的重点：终值占多少", "content": (
                "<p>$$\\frac{\\text{终值}}{V} = \\frac{" + f"{_n(d['pv_terminal']):.2f}" + "}{"
                + f"{_n(d['V']):.2f}" + "} = " + f"{share * 100:.1f}" + "\\%$$"
                "<p>十四个字概括：<b>估值的一多半，靠的是第 10 年之后的假设。</b>"
                "而那部分恰恰最难验证——没人知道十年后这家公司还在不在。</p>"
                "<p>把滑块的 $g_\\infty$ 从 3% 拖到 4%，终值会跳一大截："
                "分母 $r-g_\\infty$ 从 7% 变成 6%，终值直接涨 1.17 倍。"
                "<b>一个百分点的永续增长率，能改写整个估值。</b></p>"
            )},
            {"title": "贴现率敏感度", "content": (
                "<p>把贴现率从 10% 上调 1 个百分点到 11%：</p>"
                "$$V(11\\%) = " + f"{_n(d['V_rate_up']):.2f}" + "\\qquad "
                "\\text{跌幅} = " + f"{sens * 100:.1f}" + "\\%$$"
                "<p>利率只动了 1%，估值掉了 "
                + f"{sens * 100:.1f}" + "%。"
                "这就是为什么<b>贴现率的选择比现金流预测更致命</b>——"
                "它同时影响每一项的分母，而且对最远的那几项影响最大。</p>"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>"
                "「安全边际」在这里有了新的含义：既然估值一多半靠远期假设，"
                "那么<b>能够承受假设出错的估值，才是安全的价格</b>。</p>"
            )},
        ],
    }


# =====================================================================
# 12) 规模优势：大者为什么更大
# =====================================================================
def build_scale():
    F, v, q1, k = 1000, 10, 500, 3
    sc = K.scale_advantage(F, v, q1, k)
    return {
        "lesson": {
            "title": "规模优势：大者为什么更大",
            "subtitle": "单位成本 $u(q) = F/q + v$ —— 固定成本被产量摊薄，于是规模本身就是护城河",
            "problem": (
                "<p>造东西要花一笔<b>固定成本</b>（厂房、研发、品牌），再花一笔<b>可变成本</b>（原料、人工）。"
                "固定成本 1000，每件可变成本 10。</p>"
                "<p class='mt-2'>你产量 <b>500</b> 件，对手产量是你的 <b>3 倍</b>。</p>"
                "<p class='mt-2'>单位成本差多少？"
                "<span class='text-rose-600 font-semibold'>这个差值，就是对手能打的价格战额度。</span></p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "scale", "caption": "单位成本随产量下降"},
            "view": {"xRange": [0, 2200], "yRange": [0, 16]},
            "params": [
                {"name": "fixed", "label": "固定成本 F", "min": 0, "max": 5000, "step": 100, "value": F, "unit": "", "digits": 0},
                {"name": "vc", "label": "每件可变成本 v", "min": 1, "max": 50, "step": 1, "value": v, "unit": "", "digits": 0},
                {"name": "q1", "label": "你的产量 q", "min": 50, "max": 2000, "step": 50, "value": q1, "unit": "", "digits": 0},
                {"name": "k", "label": "对手是你的几倍 k", "min": 1, "max": 6, "step": 0.5, "value": k, "unit": " 倍", "digits": 1},
            ],
            "scalars": [
                {"name": "u1", "expr": "fixed/q1 + vc"},
                {"name": "u2", "expr": "fixed/(k*q1) + vc"},
                {"name": "advantage", "expr": "fixed/q1 - fixed/(k*q1)"},
                {"name": "fixedShare", "expr": "(fixed/q1)/(fixed/q1+vc)"},
                {"name": "costRatio", "expr": "(fixed/q1+vc)/(fixed/(k*q1)+vc)"},
                {"name": "scale_for_10pct", "expr": "9*fixed/vc"},
            ],
            "readouts": [
                {"id": "u1", "label": "你的单位成本 u(q)", "type": "expr", "expr": "u1", "digits": 2, "unit": "", "color": "#dc2626"},
                {"id": "u2", "label": "对手的单位成本 u(kq)", "type": "expr", "expr": "u2", "digits": 2, "unit": "", "highlight": True},
                {"id": "adv", "label": "单位成本优势（价格战额度）", "type": "expr", "expr": "advantage", "digits": 2, "unit": "", "color": "#dc2626"},
                {"id": "ratio", "label": "成本比 u(q)/u(kq)", "type": "expr", "expr": "costRatio", "digits": 3, "unit": " 倍"},
                {"id": "share", "label": "固定成本占你单位成本的比例", "type": "expr", "expr": "fixedShare*100", "digits": 1, "unit": "%", "color": "#78716c"},
                {"id": "s10", "label": "占比降到 10% 所需产量 9F/v", "type": "expr", "expr": "scale_for_10pct", "money": True, "unit": ""},
                {"id": "ok", "label": "固定成本是否已被摊薄（占比<10%）", "type": "status", "expr": "fixedShare", "op": "<", "rhs": 0.1, "okText": "规模已经足够大", "badText": "固定成本还很重"},
            ],
            "legend": [
                {"color": "#b45309", "text": "单位成本 u(q)"},
                {"color": "#78716c", "text": "可变成本地板 v"},
                {"color": "#dc2626", "text": "小者 q"},
                {"color": "#059669", "text": "大者 kq"},
            ],
        },
        "steps": [
            {"title": "单位成本 = 摊薄的固定成本 + 可变成本", "content": (
                "$$u(q) = \\frac{F}{q} + v$$"
                "<p>固定成本 $F$ 除以产量 $q$——这一项随产量<b>下降</b>；"
                "可变成本 $v$ 是地板，产量再大也降不下去。</p>"
                "<p>所以规模优势<b>不是无限的</b>：它只能把 $F/q$ 压小，压不到零。"
                "这也是「规模优势」与「网络效应」的根本区别（见下一节）。</p>"
            )},
            {"title": "代入默认参数", "content": (
                "<p>$F=1000,\\ v=10,\\ q=500,\\ k=3$：</p>"
                "$$u(500) = \\frac{1000}{500} + 10 = " + f"{_n(sc['u1']):.2f}" + "$$"
                "$$u(1500) = \\frac{1000}{1500} + 10 = " + f"{_n(sc['u2']):.4f}" + "$$"
                "$$\\text{优势} = " + f"{_n(sc['advantage']):.4f}" + "$$"
                "<p>对手每卖一件，就比你便宜 "
                + f"{_n(sc['advantage']):.2f}" + "。"
                "他可以把售价压到你的成本线以下，自己仍然赚钱——"
                "<b>这就是价格战的额度。</b></p>"
            )},
            {"title": "正反馈：为什么大者更大", "content": (
                "<p>把四个环节串起来看：</p>"
                "<blockquote class='border-l-4 border-amber-400 pl-3 text-stone-600'>"
                "更大规模 → 更低单位成本 → 能定更低价格（或更多研发/广告）→ "
                "抢到更大份额 → 更大规模</blockquote>"
                "<p>这是一个<b>自我强化</b>的回路。芒格把它叫做"
                "「规模优势」，也是他偏爱「有护城河的生意」的原因。</p>"
                "<p class='mt-2'>但回路要成立，前提是固定成本足够重。"
                "拖动滑块把 $F$ 拉到 0：优势立刻消失——"
                "没有固定成本，就没有规模效应。</p>"
            )},
            {"title": "临界规模：固定成本占比", "content": (
                "<p>固定成本占单位成本的比例是个干净的进度条：</p>"
                "$$\\frac{F/q}{F/q+v} = " + f"{_n(sc['fixed_share']) * 100:.1f}" + "\\%$$"
                "<p>想把它压到 10% 以下，产量必须达到</p>"
                "$$q^{*} = \\frac{9F}{v} = \\frac{9 \\times 1000}{10} = "
                + f"{_n(sc['scale_for_10pct']):.0f}" + "$$"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>"
                "这个 $q^{*}$ 是判断「这门生意能不能靠规模取胜」的门槛："
                "<b>如果行业总容量都到不了 $9F/v$，那么谁都摊不薄固定成本，"
                "规模优势也就不存在。</b></p>"
            )},
        ],
    }


# =====================================================================
# 13) 网络效应：连接数按平方涨
# =====================================================================
def build_network():
    n = 1000
    nw = K.network_value(n)
    return {
        "lesson": {
            "title": "网络效应：连接数按平方涨",
            "subtitle": "用户只按 n 涨，连接数却按 n² 涨——这就是「赢家通吃」的算术",
            "problem": (
                "<p>一个电话网有 <b>1000</b> 个用户。理论上能建立多少条<b>双向连接</b>？</p>"
                "<p class='mt-2'>直觉会答「大约 1000 条」。实际是 "
                "<span class='text-rose-600 font-semibold'>499,500 条</span>。</p>"
                "<p class='mt-2'>拖动滑块：用户数<b>翻一倍</b>，连接数会变成几倍？</p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "network", "caption": "连接数 n(n−1)/2"},
            "view": {"xRange": [0, 2400], "yRange": [0, 3000000]},
            "params": [
                {"name": "n", "label": "用户数 n", "min": 10, "max": 5000, "step": 10, "value": n, "unit": "", "digits": 0},
            ],
            "scalars": [
                {"name": "links", "expr": "n*(n-1)/2"},
                {"name": "metcalfe", "expr": "n*(n-1)"},
                {"name": "doubleRatio", "expr": "(2*n)*(2*n-1)/(n*(n-1))"},
                {"name": "target_links", "expr": "1000000"},
                {"name": "nForTarget", "expr": "(1+sqrt(1+8*1000000))/2"},
            ],
            "readouts": [
                {"id": "links", "label": "连接数 n(n−1)/2", "type": "expr", "expr": "links", "money": True, "unit": " 条", "highlight": True},
                {"id": "met", "label": "梅特卡夫口径 n(n−1)", "type": "expr", "expr": "metcalfe", "money": True, "unit": " 条", "color": "#0891b2"},
                {"id": "ratio", "label": "用户翻倍 → 连接数 ×", "type": "expr", "expr": "doubleRatio", "digits": 3, "unit": " 倍", "color": "#dc2626"},
                {"id": "nft", "label": "100 万条连接所需用户数", "type": "expr", "expr": "nForTarget", "digits": 0, "unit": " 人", "color": "#78716c"},
                {"id": "ok", "label": "是否已进入平方区间", "type": "status", "expr": "n", "op": ">", "rhs": 100, "okText": "n 够大，平方项已占主导", "badText": "n 还小，近似线性"},
            ],
            "legend": [
                {"color": "#b45309", "text": "连接数 n(n−1)/2"},
                {"color": "#dc2626", "text": "当前 n"},
                {"color": "#059669", "text": "2n"},
            ],
        },
        "steps": [
            {"title": "连接数不是 n，而是 n(n−1)/2", "content": (
                "<p>每两个用户之间可以有一条连接。从 $n$ 个人里选 2 个：</p>"
                "$$\\binom{n}{2} = \\frac{n(n-1)}{2}$$"
                "<p>代入 $n=1000$：$\\dfrac{1000 \\times 999}{2} = "
                + f"{_n(nw['links']):,.0f}$ 条。</p>"
                "<p class='mt-2'>这里没有任何魔法——只是<b>组合数天然是二次的</b>。"
                "而人对「网络价值」的直觉通常是线性的，这正是低估的来源。</p>"
            )},
            {"title": "翻倍的威力", "content": (
                "<p>把 $n$ 换成 $2n$：</p>"
                "$$\\frac{\\binom{2n}{2}}{\\binom{n}{2}}"
                " = \\frac{2n(2n-1)}{n(n-1)} = " + f"{_n(nw['links_double_ratio']):.3f}" + "$$"
                "<p>$n$ 很大时这个比值趋于 <b>4</b>。也就是说："
                "<b>用户翻一倍，连接数变成四倍。</b></p>"
                "<p class='mt-2'>反向看更刺眼：如果对手的用户是你的两倍，"
                "他手上的「连接资产」是你的四倍。要追上他，你得先缩小这个四倍的差距——"
                "而每缩小一点，他还在继续提速。</p>"
            )},
            {"title": "所以它比规模优势更狠", "content": (
                "<p>上一节的规模优势是 $F/q$，随产量<b>衰减</b>——优势有上限。"
                "网络效应的连接数是 $n^2$，随用户数<b>加速</b>——优势没有上限。</p>"
                "<div class='mt-3 overflow-x-auto'><table class='w-full text-sm'>"
                "<thead><tr class='border-b-2 border-stone-300 text-left text-xs uppercase text-stone-400'>"
                "<th class='py-2 pr-3'>模型</th><th class='py-2 pr-3'>随规模怎么变</th>"
                "<th class='py-2'>结局</th></tr></thead><tbody>"
                "<tr class='border-b border-stone-100'><td class='py-1.5 pr-3'>规模优势</td>"
                "<td class='py-1.5 pr-3'>单位成本 $F/q+v$，优势<b>收敛</b></td>"
                "<td class='py-1.5'>寡头几家共存</td></tr>"
                "<tr><td class='py-1.5 pr-3'>网络效应</td>"
                "<td class='py-1.5 pr-3'>连接数 $n(n-1)/2$，优势<b>发散</b></td>"
                "<td class='py-1.5'>赢家通吃</td></tr>"
                "</tbody></table></div>"
                "<p class='mt-2'>芒格偏爱「有网络效应的生意」，理由就在这里："
                "<b>它是少数几个优势会自己长大的结构。</b></p>"
            )},
            {"title": "一个直觉校准：100 万条连接需要多少人", "content": (
                "<p>解 $\\dfrac{n(n-1)}{2} = 10^{6}$：</p>"
                "$$n = \\frac{1+\\sqrt{1+8\\times10^{6}}}{2} = "
                + f"{_n(nw['n_for_target']):.0f}" + "$$"
                "<p>只要 <b>" + f"{_n(nw['n_for_target']):,.0f}" + " 个人</b>，两两之间的潜在连接就超过一百万条。</p>"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>"
                "反过来读这句话：<b>当你的网络只有几千人时，"
                "你已经在处理百万级的连接关系了。</b>"
                "这也解释了为什么网络型业务的复杂度会突然失控——"
                "不是用户变多了，是关系数按平方涨了。</p>"
            )},
        ],
    }


# =====================================================================
# 14) 临界点：R₀ 略过 1 就天翻地覆
# =====================================================================
def build_tipping():
    beta, gamma = 0.6, 0.2
    tp = K.tipping(beta, gamma)
    peak = _n(tp["peak_frac_analytic"])
    final = tp["final_size_solved"]
    return {
        "lesson": {
            "title": "临界点：R₀ 略过 1 就天翻地覆",
            "subtitle": "芒格：「巴甫洛夫联想加上社会认同，能让一场荒谬像传染病一样扩散。」",
            "problem": (
                "<p>把一件事的传播看成传染：接触率 $\\beta$，恢复率 $\\gamma$。"
                "定义<b>基本传染数</b> $R_0 = \\beta S_0/\\gamma$——"
                "一个感染者平均能传染几个人。</p>"
                "<p class='mt-2'>现在取 $\\beta = 0.6$、$\\gamma = 0.2$，"
                "于是 $R_0 = 3$。</p>"
                "<p class='mt-2'>拖动两个滑块，把 $R_0$ 从 3 一路压到 1 以下看会发生什么："
                "<span class='text-rose-600 font-semibold'>不是慢慢变小，是整条曲线塌掉。</span></p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "tipping", "caption": "SIR：易感 / 感染 / 痊愈"},
            "view": {"xRange": [0, 80], "yRange": [0, 1]},
            "params": [
                {"name": "beta", "label": "接触率 β", "min": 0.05, "max": 1.2, "step": 0.05, "value": beta, "unit": "", "digits": 2},
                {"name": "gamma", "label": "恢复率 γ", "min": 0.05, "max": 0.8, "step": 0.05, "value": gamma, "unit": "", "digits": 2},
            ],
            "scalars": [
                {"name": "s0", "expr": "1"},
                {"name": "days", "expr": "80"},
                {"name": "i0", "expr": "0.0001"},
                {"name": "R0", "expr": "beta*s0/gamma"},
                {"name": "peak", "expr": "R0>1 ? i0 + s0 - gamma/beta + (gamma/beta)*log((gamma/beta)/s0) : i0"},
                {"name": "finalSize", "expr": "sirFinal(beta*s0/gamma)*100"},
                {"name": "herd", "expr": "gamma/beta"},
            ],
            "readouts": [
                {"id": "r0", "label": "基本传染数 R₀ = βS₀/γ", "type": "expr", "expr": "R0", "digits": 2, "unit": "", "highlight": True},
                {"id": "peak", "label": "峰值感染比例", "type": "expr", "expr": "peak*100", "digits": 2, "unit": "%", "color": "#dc2626"},
                {"id": "final", "label": "最终累计感染比例", "type": "expr", "expr": "finalSize", "digits": 2, "unit": "%", "color": "#059669"},
                {"id": "herd", "label": "熄灭所需的易感比例上界 γ/β", "type": "expr", "expr": "herd", "digits": 3, "unit": ""},
                {"id": "ok", "label": "会不会爆发（R₀ > 1）", "type": "status", "expr": "1-R0", "op": ">", "rhs": 0, "okText": "R₀ 未超过 1，传染自行熄灭", "badText": "R₀ 超过 1，指数扩散"},
            ],
            "legend": [
                {"color": "#0891b2", "text": "易感 S"},
                {"color": "#dc2626", "text": "感染 I"},
                {"color": "#059669", "text": "痊愈 R"},
            ],
        },
        "steps": [
            {"title": "三个方程，一条临界线", "content": (
                "<p>SIR 模型把人群分成三段（比例之和恒为 1）：</p>"
                "$$\\frac{dS}{dt} = -\\beta SI \\qquad "
                "\\frac{dI}{dt} = \\beta SI - \\gamma I \\qquad "
                "\\frac{dR}{dt} = \\gamma I$$"
                "<p>感染者变化率 $= I(\\beta S - \\gamma)$。"
                "只要 $\\beta S > \\gamma$，感染就涨；否则就跌。</p>"
                "<p>初始 $S \\approx 1$，于是临界条件写成：</p>"
                "$$R_0 = \\frac{\\beta S_0}{\\gamma} > 1$$"
                "<p class='mt-2'>这一页的曲线是用 <b>RK4 真实积分</b>出来的，"
                "不是画一条预设的钟形线——拖动滑块，方程会重新跑一遍。</p>"
            )},
            {"title": "代入 β=0.6、γ=0.2", "content": (
                "$$R_0 = \\frac{0.6}{0.2} = " + f"{_n(tp['R0']):.0f}" + "$$"
                "<p>峰值感染有解析解。令 $S_{peak} = \\gamma/\\beta$，则</p>"
                "$$I_{peak} = I_0 + S_0 - S_{peak} + \\frac{\\gamma}{\\beta}"
                "\\ln\\frac{S_{peak}}{S_0} = " + f"{peak * 100:.2f}" + "\\%$$"
                "<p>最终累计感染（解 $R_\\infty = 1 - e^{-R_0 R_\\infty}$）是 "
                "<b>" + f"{final * 100:.1f}" + "%</b>。</p>"
                "<p class='mt-2 text-stone-500 text-xs'>解析峰值与上面 RK4 画出的数值解对比过，"
                "两者相差不到 0.01——一个公式、一个积分，互为校验。</p>"
            )},
            {"title": "临界点的行为：不是渐变，是塌方", "content": (
                "<p>把 $\\gamma$ 从 0.2 拖到 0.65（$R_0$ 从 3 掉到 0.92）：</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li>$R_0 = 1$ 之前：整条感染曲线一路爬升，最终 "
                + f"{final * 100:.0f}" + "% 的人被卷进去；</li>"
                "<li>$R_0$ 刚跌破 1：感染数<b>单调下降</b>，峰值就是最初始的那一点点。</li>"
                "</ul>"
                "<p>中间没有任何过渡。这就是<b>临界点</b>（tipping point）的数学含义："
                "在阈值的一侧，扰动会自己消失；在另一侧，扰动会自己放大。</p>"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>"
                "芒格讲 Lollapalooza 说的是「多个倾向同向叠加」，"
                "这一页补上了它的动力学：<b>当叠加把 $R_0$ 推过 1，"
                "系统就换了一种行为模式。</b></p>"
            )},
            {"title": "为什么它和「心理倾向」是一回事", "content": (
                "<p>把 $\\beta$ 读成「一个已经激动的人感染别人的速率」，"
                "$\\gamma$ 读成「冷静下来的速率」，SIR 就变成了情绪扩散的模型。</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li><b>降低 β</b>：远离人群、减少接触（不看那个群聊）；</li>"
                "<li><b>提高 γ</b>：给情绪留恢复时间（睡一觉再决定）。</li>"
                "</ul>"
                "<p>两者都只要把 $R_0$ 压到 1 以下，传播就会自行熄灭——"
                "<b>不需要把它压到 0</b>。</p>"
                "<p class='mt-2'>这也是「能力圈」和「清单」在时间维度上的同伴："
                "它们做的事，就是让一次冲动在 $R_0$ 上到 1 之前停下来。</p>"
            )},
        ],
    }


# =====================================================================
# 15) 沉没成本：已经花掉的，不该进入决策
# =====================================================================
def build_sunk():
    sunk, extra, p, reward = 100, 50, 40, 200
    sk = K.sunk_cost(sunk, extra, p / 100, reward)
    return {
        "lesson": {
            "title": "沉没成本：已经花掉的，不该进入决策",
            "subtitle": "「不要为了翻本而继续投入」——但这条原则在数学上比听起来更彻底",
            "problem": (
                "<p>一个项目你已经投了 <b>100</b>，现在需要再投 <b>50</b> 才能完成。"
                "成功概率 <b>40%</b>，成功后值 <b>200</b>。</p>"
                "<p class='mt-2'>该继续吗？</p>"
                "<p class='mt-2'>大多数人会说「已经亏了 100，再投 50 太亏了」。"
                "而正确答案是：<span class='text-rose-600 font-semibold'>该继续</span>。"
                "拖动滑块，看正确的算法和账面的算法在哪一点上给出相反结论。</p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "sunk", "caption": "期望增量 vs 成功率"},
            "view": {"xRange": [0, 1], "yRange": [-150, 200]},
            "params": [
                {"name": "sunk", "label": "已投入（沉没成本）", "min": 0, "max": 400, "step": 10, "value": sunk, "unit": "", "digits": 0},
                {"name": "extra", "label": "还需再投", "min": 0, "max": 300, "step": 10, "value": extra, "unit": "", "digits": 0},
                {"name": "p", "label": "成功概率 p", "min": 0, "max": 100, "step": 1, "value": p, "unit": "%", "digits": 0},
                {"name": "reward", "label": "成功后的收益 R", "min": 0, "max": 600, "step": 10, "value": reward, "unit": "", "digits": 0},
            ],
            "scalars": [
                {"name": "evContinue", "expr": "p/100*reward - extra"},
                {"name": "evWrong", "expr": "p/100*reward - extra - sunk"},
                {"name": "breakeven", "expr": "extra/reward"},
                {"name": "breakevenWrong", "expr": "(extra+sunk)/reward"},
            ],
            "readouts": [
                {"id": "evc", "label": "正确算法 E[继续] = pR − C", "type": "expr", "expr": "evContinue", "digits": 1, "unit": "", "highlight": True},
                {"id": "evw", "label": "账面算法（把已投入算进来）", "type": "expr", "expr": "evWrong", "digits": 1, "unit": "", "color": "#dc2626"},
                {"id": "be", "label": "真正的盈亏平衡成功率 C/R", "type": "expr", "expr": "breakeven*100", "digits": 1, "unit": "%", "color": "#059669"},
                {"id": "bew", "label": "误算出来的平衡点 (C+S)/R", "type": "expr", "expr": "breakevenWrong*100", "digits": 1, "unit": "%", "color": "#dc2626"},
                {"id": "gap", "label": "两个平衡点之差（纯粹由沉没成本造成）", "type": "expr", "expr": "(breakevenWrong-breakeven)*100", "digits": 1, "unit": " 个百分点", "color": "#78716c"},
                {"id": "ok", "label": "仅按增量看是否该继续", "type": "status", "expr": "evContinue", "op": ">", "rhs": 0, "okText": "该继续（与已投入无关）", "badText": "该止损"},
            ],
            "legend": [
                {"color": "#059669", "text": "只看增量（正确）"},
                {"color": "#dc2626", "text": "把已投入也算进来（错）"},
                {"color": "#78716c", "text": "盈亏平衡线"},
            ],
        },
        "steps": [
            {"title": "决策只问增量", "content": (
                "<p>沉没成本的定义就是「已经花掉、拿不回来」的钱。"
                "任何<b>未来的</b>选择都改变不了它，所以它在决策里的系数必然是 0。</p>"
                "$$E[\\text{继续}] = pR - C$$"
                "<p>注意这个式子里<b>没有 S</b>。已投入 100 还是 100 万，"
                "答案都完全一样。</p>"
                "<p class='mt-2'>那已经花掉的钱该去哪里？去<b>复盘</b>，不去<b>决策</b>。</p>"
            )},
            {"title": "代入默认参数", "content": (
                "<p>$S=100,\\ C=50,\\ p=40\\%,\\ R=200$：</p>"
                "$$E[\\text{继续}] = 0.4 \\times 200 - 50 = "
                + f"{_n(sk['ev_continue']):.0f}" + "$$"
                "<p>正期望，<b>该继续</b>。</p>"
                "<p>而如果错误地把沉没成本算进来：</p>"
                "$$0.4 \\times 200 - 50 - 100 = " + f"{_n(sk['ev_wrong']):.0f}" + "$$"
                "<p>同一个项目，两个符号。<b>这就是损失厌恶的入口</b>——"
                "不是因为你算错了乘法，而是因为你在式子里放进了一个不该出现的数。</p>"
            )},
            {"title": "两个平衡点", "content": (
                "<p>让期望为零，解出成功率门槛：</p>"
                "$$\\text{正确：}\\quad p^{*} = \\frac{C}{R} = \\frac{50}{200} = "
                + f"{_n(sk['breakeven_p']) * 100:.0f}" + "\\%$$"
                "$$\\text{误算：}\\quad p^{*} = \\frac{C+S}{R} = "
                + f"{(extra + sunk) / reward * 100:.0f}" + "\\%$$"
                "<p>后者比前者高出 "
                + f"{(extra + sunk) / reward * 100 - _n(sk['breakeven_p']) * 100:.0f}"
                + " 个百分点——<b>这个差值完全由沉没成本制造，与项目本身毫无关系。</b></p>"
                "<p class='mt-2'>拖动「已投入」滑块，看这个差值怎么被拉开："
                "已投入越大，你要求的成功率就越离谱，于是越容易错过本来划算的事。</p>"
            )},
            {"title": "它如何伪装成「理性」", "content": (
                "<p>沉没成本最危险的地方在于，它总是以「负责任」的面目出现：</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li>「已经投了这么多，不能半途而废」——但半途而废和继续，"
                "花的都是<b>未来</b>的钱；</li>"
                "<li>「不继续就等于承认之前错了」——承认错误是<b>信息</b>，不是成本；</li>"
                "<li>「再等等就回本了」——市场不知道你的成本线在哪。</li>"
                "</ul>"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>"
                "配合前面的模型一起用：<b>用「机会成本」问这笔追加的钱还能拿去做什么，"
                "用「能力圈」问自己是不是真的看得懂这个项目。</b>"
                "两把尺子都不含 S。</p>"
            )},
        ],
    }


# =====================================================================
# 16) 冗余备份：串得少，并得多
# =====================================================================
def build_redundancy():
    r, n = 90, 5
    rd = K.redundancy(r / 100, n)
    return {
        "lesson": {
            "title": "冗余备份：串得少，并得多",
            "subtitle": "同一个 90% 可靠的零件，串联 5 个只剩 59%，并联 5 个却有 99.999%",
            "problem": (
                "<p>工程上「可靠度 90%」的零件很常见。现在要把几个这样的零件组成一个系统。</p>"
                "<p class='mt-2'>两种接法：<b>串联</b>（一个接一个，任一个坏则全坏）、"
                "<b>并联</b>（并排干同一件事，全坏才坏）。</p>"
                "<p class='mt-2'>各用 5 个零件，系统可靠度分别是多少？"
                "<span class='text-rose-600 font-semibold'>差的不是一点。</span></p>"
            ),
            "ui": {},
        },
        "board": {
            "scene": {"kind": "redundancy", "caption": "串联系数 rⁿ 与并联 1−(1−r)ⁿ"},
            "view": {"xRange": [1, 9], "yRange": [0, 1]},
            "params": [
                {"name": "r", "label": "单件可靠度 r", "min": 50, "max": 99, "step": 1, "value": r, "unit": "%", "digits": 0},
                {"name": "n", "label": "零件数 n", "min": 1, "max": 9, "step": 1, "value": n, "unit": " 个", "digits": 0},
            ],
            "scalars": [
                {"name": "series", "expr": "(r/100)^n"},
                {"name": "parallel", "expr": "1-(1-r/100)^n"},
                {"name": "gain", "expr": "(1-(1-r/100)^n)/((r/100)^n)"},
                {"name": "nHalf", "expr": "log(0.5)/log(r/100)"},
                {"name": "nNinety9", "expr": "log(0.01)/log(1-r/100)"},
            ],
            "readouts": [
                {"id": "par", "label": "并联可靠度 1−(1−r)ⁿ", "type": "expr", "expr": "parallel*100", "digits": 3, "unit": "%", "highlight": True},
                {"id": "ser", "label": "串联可靠度 rⁿ", "type": "expr", "expr": "series*100", "digits": 2, "unit": "%", "color": "#dc2626"},
                {"id": "gain", "label": "并联 / 串联", "type": "expr", "expr": "gain", "digits": 2, "unit": " 倍", "color": "#059669"},
                {"id": "nh", "label": "串联掉到 50% 所需的零件数", "type": "expr", "expr": "nHalf", "digits": 2, "unit": " 个", "color": "#dc2626"},
                {"id": "nn", "label": "并联升到 99% 所需的零件数", "type": "expr", "expr": "nNinety9", "digits": 2, "unit": " 个", "color": "#059669"},
                {"id": "ok", "label": "系统是否比单件更可靠", "type": "status", "expr": "parallel - r/100", "op": ">", "rhs": 0, "okText": "并联让它更可靠", "badText": "更不可靠"},
            ],
            "legend": [
                {"color": "#dc2626", "text": "串联 rⁿ（任一坏则坏）"},
                {"color": "#059669", "text": "并联 1−(1−r)ⁿ（全坏才坏）"},
            ],
        },
        "steps": [
            {"title": "两个公式，方向相反", "content": (
                "$$\\text{串联：}\\quad R = r^{n} \\qquad\\qquad "
                "\\text{并联：}\\quad R = 1 - (1-r)^{n}$$"
                "<p>串联是「<b>全部都要成功</b>」，并联是「<b>不能全部失败</b>」。</p>"
                "<p class='mt-2'>注意串联那个式子——它就是第 6.1 节「反过来想」里的存活率 $\\prod(1-p_i)$。"
                "同一个公式，工程学叫可靠性，投资学叫存活率。</p>"
            )},
            {"title": "代入 r=90%、n=5", "content": (
                "$$\\text{串联} = 0.9^{5} = " + f"{_n(rd['series']):.4f}"
                " = " + f"{_n(rd['series']) * 100:.2f}" + "\\%$$"
                "$$\\text{并联} = 1 - 0.1^{5} = " + f"{_n(rd['parallel']):.6f}"
                " = " + f"{_n(rd['parallel']) * 100:.3f}" + "\\%$$"
                "<p>同一个「90% 可靠」的零件：</p>"
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li>串 5 个 → 掉到 <b>" + f"{_n(rd['series']) * 100:.1f}" + "%</b>，比单件还差得多；</li>"
                "<li>并 5 个 → 升到 <b>" + f"{_n(rd['parallel']) * 100:.3f}" + "%</b>，几乎等于必然成功。</li>"
                "</ul>"
                "<p>相差 <b>" + f"{_n(rd['gain']):.0f}" + " 倍</b>。"
                "这就是「冗余备份」为什么是工程与投资里的同一件事。</p>"
            )},
            {"title": "两个有用的门槛", "content": (
                "<p>把两个公式分别置为 50% 和 99%，解出零件数：</p>"
                "$$\\text{串联掉到一半：}\\quad n = \\frac{\\ln 0.5}{\\ln 0.9} = "
                + f"{_n(rd['n_series_half']):.2f}" + " \\Rightarrow 7\\ \\text{个}$$"
                "$$\\text{并联升到 99\\%：}\\quad n = \\frac{\\ln 0.01}{\\ln 0.1} = "
                + f"{_n(rd['n_parallel_99']):.0f}" + "\\ \\text{个}$$"
                "<p>换句话说：<b>串联 7 个就和抛硬币差不多；并联只要 2 个就到 99%。</b></p>"
                "<p class='mt-2'>拖动滑块把 $r$ 从 90% 调到 99%：串联的门槛立刻放宽到 69 个，"
                "并联则 1 个就够。所以提高单件质量与增加冗余，两条路都通——"
                "但<b>冗余更便宜</b>。</p>"
            )},
            {"title": "怎么用在决策上", "content": (
                "<ul class='list-disc pl-5 space-y-1'>"
                "<li><b>减少串联环节</b>：一件事如果需要连续过关，"
                "每加一环都在做乘法削减（回到 6.1 的「反过来想」）；</li>"
                "<li><b>给关键环加并联</b>：多个供应商、多份备份、多重验证、"
                "多条收入来源——都是把「全坏才坏」变成现实；</li>"
                "<li><b>分清哪些在串联、哪些在并联</b>：很多失败不是环节不够好，"
                "而是把本该并联的东西串起来了。</li>"
                "</ul>"
                "<p class='mt-2 border-l-4 border-amber-400 pl-3'>"
                "芒格说「反过来想」：如果一件事<b>必然失败只需要一个条件</b>，"
                "那它就是串联结构，你要做的是先找出最弱的那一环；"
                "如果一件事<b>成功只需要一个条件</b>，那它是并联结构，你要做的是多备几条路。</p>"
            )},
        ],
    }


REGISTRY = {
    "compound": build_compound,
    "bayes": build_bayes,
    "expected": build_expected,
    "safety": build_safety,
    "opportunity": build_opportunity,
    "inversion": build_inversion,
    "incentive": build_incentive,
    "competence": build_competence,
    "lollapalooza": build_lollapalooza,
    "bias": build_bias,
    "dcf": build_dcf,
    "scale": build_scale,
    "network": build_network,
    "tipping": build_tipping,
    "sunk": build_sunk,
    "redundancy": build_redundancy,
}

ORDER = ["compound", "bayes", "expected", "safety", "opportunity",
         "inversion", "incentive", "competence", "lollapalooza", "bias",
         "dcf", "scale", "network", "tipping", "sunk", "redundancy"]

META = {
    "compound": ("复利", "时间是朋友还是敌人", "指数增长 · 72 法则 · 负债的另一面"),
    "bayes": ("贝叶斯基率", "为什么阳性大多是假的", "基率忽视 · 似然比 · 冤案的数学"),
    "expected": ("期望值与凯利", "为什么全押必输", "算术期望 · 几何增长 · 半凯利"),
    "safety": ("安全边际", "估计必然出错，所以要留冗余", "正态分布 · 击穿概率 · 能力圈"),
    "opportunity": ("机会成本", "选 A 的真实成本是放弃的 B", "最优替代 · 真实净收益"),
    "inversion": ("反过来想", "最弱环节决定生死", "串联存活率 · 最弱环节优先 · 避免愚蠢"),
    "incentive": ("激励优先", "佣金决定行为", "委托—代理 · 目标分岔 · 对齐点"),
    "competence": ("能力圈", "边界比大小重要", "暴露比例 · σ 预算 · 击穿概率"),
    "lollapalooza": ("Lollapalooza", "多个倾向同向叠加", "乘法放大 · 互相喂养 · 超线性"),
    "bias": ("误判清单", "把风险指数级压下去", "25 条倾向 · 拦截率 · 逐条自检"),
    "dcf": ("贴现与内在价值", "今天的一块钱比明天值钱", "两阶段 DCF · 终值占比 · 贴现率敏感度"),
    "scale": ("规模优势", "大者为什么更大", "固定成本摊薄 · 单位成本差 · 正反馈"),
    "network": ("网络效应", "连接数按平方涨", "梅特卡夫 · n(n−1)/2 · 赢家通吃"),
    "tipping": ("临界点与传染", "R₀ 略过 1 就天翻地覆", "SIR · 传染阈值 · 峰值感染"),
    "sunk": ("沉没成本", "已经花掉的，不该进入决策", "增量决策 · 两个平衡点 · 损失厌恶"),
    "redundancy": ("冗余备份", "串得少，并得多", "串联 rⁿ · 并联 1−(1−r)ⁿ · 与「反过来想」对偶"),
}


def build_index(out):
    """生成首页索引（模型格栅）。"""
    cards = []
    for key in ORDER:
        name, one, tags = META[key]
        cards.append(
            f'<a href="{key}.html" class="block bg-white rounded-xl border border-stone-200 p-5 '
            f'hover:border-amber-500 hover:shadow-lg transition-all">'
            f'<div class="text-xs font-bold text-amber-600 mb-1">{name}</div>'
            f'<div class="text-base font-bold text-stone-900 leading-snug mb-2">{one}</div>'
            f'<div class="text-xs text-stone-500 leading-relaxed">{tags}</div></a>'
        )
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>查理·芒格思维模型 · 量化演示</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{{font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif;}}</style>
</head>
<body class="bg-stone-100 text-stone-900">
<div class="max-w-4xl mx-auto px-6 py-12">
    <div class="text-xs uppercase tracking-widest text-amber-600 font-bold mb-2">Charlie Munger · Latticework of Mental Models</div>
    <h1 class="text-3xl font-bold mb-3">思维模型：可算的那一部分</h1>
    <p class="text-stone-600 leading-relaxed max-w-2xl">
        芒格说：「你必须知道重要学科的重要理论，并经常使用它们——要全部都用上，而不是只用几个。」
        下面 <b>16 个模型</b>是这套格栅里<b>能算清楚</b>的部分，分三批：
        前 5 个是数学地基（复利、贝叶斯、凯利、安全边际、机会成本）；
        中间 5 个把芒格最常说的几句话落成算式（反过来想 · 看激励 · 守能力圈 · 提防 Lollapalooza · 用清单）；
        最后 6 个是系统与结构（贴现、规模优势、网络效应、临界点、沉没成本、冗余备份）。
        拖动滑块，看数字如何改变你的判断——所有数值由 sympy 精确计算，与配套文档同源。
    </p>
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-8">
        {''.join(cards)}
    </div>
    <div class="mt-8 text-xs text-stone-500 leading-relaxed border-t border-stone-200 pt-5">
        <p>配套文档：<code>docs/思维模型.md</code> —— 全景清单、每个模型的一句话本质、案例、常见误用与决策前检查清单。</p>
        <p class="mt-2">来源：本页为教学演示，模型与数值用于说明认知偏差的数学结构，不构成投资建议。</p>
    </div>
</div>
</body></html>"""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def main(argv):
    if not argv or argv[0] in ("list", "-l"):
        print("可用模型：")
        for key in ORDER:
            name, one, _ = META[key]
            print(f"  {key:12s} {name} —— {one}")
        print("\n用法: python3 generate.py <key|all> [输出目录]")
        return 0
    if argv[0] == "all":
        out_dir = Path(argv[1]) if len(argv) > 1 else Path.cwd() / "output"
        for key in ORDER:
            p = render_html(REGISTRY[key](), out_dir / f"{key}.html")
            print(f"written: {p}")
        p = build_index(out_dir / "index.html")
        print(f"written: {p}")
        return 0
    key = argv[0]
    if key not in REGISTRY:
        print(f"未知模型 {key}；可用：{', '.join(REGISTRY)}")
        return 1
    out = Path(argv[1]) if len(argv) > 1 else Path.cwd() / f"{key}.html"
    render_html(REGISTRY[key](), out)
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
