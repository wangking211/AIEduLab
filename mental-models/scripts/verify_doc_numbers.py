# -*- coding: utf-8 -*-
"""核验 docs/思维模型.md 里引用的每一个数值是否与 models_kernel 一致。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))
import sympy as sp
import models_kernel as K

def f(x):
    return float(sp.N(x))

checks = []
def ck(name, got, want, tol=1e-6):
    ok = abs(got - want) <= tol
    checks.append((ok, name, got, want))

# ---- 复利 ----
c = K.compound(10000, 8, 30)
ck("复利终值 30 年", f(c["F"]), 100627, 1.0)
ck("单利终值 30 年", f(c["F_simple"]), 34000, 0.5)
ck("复利馈赠", f(c["double_vs_simple"]), 66627, 1.0)
ck("本金倍数", f(c["gain_multiple"]), 10.06, 0.01)
ck("复利/单利 倍数", f(c["F"] / c["F_simple"]), 2.96, 0.005)
ck("翻倍年数", f(c["doubling_years"]), 9.01, 0.01)

c50 = K.compound(10000, 8, 50)
ck("复利 50 年（万元）", f(c50["F"]) / 10000, 46.9, 0.1)

r72 = K.rule_of_72(8)
ck("72法则误差% (绝对)", abs(f(r72["error_pct"])), 0.07, 0.02)
ck("72/8 = 9 年", f(r72["approx"]), 9, 1e-9)

ck("18% 翻倍年数", 72 / 18, 4, 1e-9)
ck("信用卡 1 万 20 年", f(K.compound(10000, 18, 20)["F"]) / 10000, 27.4, 0.1)

# ---- 贝叶斯 ----
b = K.bayes(0.01, 0.99, 0.95, 1000)
ck("真阳性人数", f(b["tp"]), 9.9, 1e-9)
ck("假阳性人数", f(b["fp"]), 49.5, 1e-9)
ck("假阴性人数", f(b["fn"]), 0.1, 1e-9)
ck("真阴性人数", f(b["tn"]), 940.5, 1e-9)
ck("后验概率 %", f(b["posterior"]) * 100, 16.7, 0.05)
ck("阳性中假阳占比 %", f(b["fp_share"]) * 100, 83.3, 0.05)
ck("似然比", f(b["sens"] / (1 - b["spec"])), 19.8, 0.05)
ck("风险放大倍数", f(b["lift"]), 16.7, 0.05)
# 后验 > 50% 的患病率阈值
lo, hi = 0.0, 0.5
for _ in range(60):
    mid = (lo + hi) / 2
    if f(K.bayes(mid, 0.99, 0.95)["posterior"]) < 0.5:
        lo = mid
    else:
        hi = mid
ck("后验>50% 所需患病率 %", hi * 100, 4.8, 0.05)

# ---- 期望值 / 凯利 ----
e = K.expected_value([(sp.Rational(6, 10), 2), (sp.Rational(4, 10), -1)])
ck("期望净收益 E", f(e["ev"]), 0.8, 1e-9)
ck("凯利仓位 %", f(e["kelly"]) * 100, 40, 1e-9)
ck("半凯利 %", f(e["kelly_half"]) * 100, 20, 1e-9)
ck("双倍凯利算术期望", f(e["ev"] * 2), 1.6, 1e-9)

import math
def growth(x, p=0.6, b=2.0):
    return math.exp(p * math.log(1 + x * b) + (1 - p) * math.log(1 - x))
ck("g(0.2) 半凯利 > 0", 1 if growth(0.2) > 1 else 0, 1)
ck("g(0.4) 满凯利 > 0", 1 if growth(0.4) > 1 else 0, 1)
ck("g(0.8) 双倍凯利 < 1", 1 if growth(0.8) < 1 else 0, 1)
ck("四连胜概率", 0.6 ** 4 * 100, 12.96, 1e-9)
ck("半凯利增速保留率 %",
   (math.log(growth(0.2)) / math.log(growth(0.4))) * 100, 75, 1.0)

# ---- 安全边际 ----
s = K.margin_of_safety(100, 80)
ck("名义 MOS %", f(s["mos"]) * 100, 20.0, 1e-9)

kp = K.knockthrough_prob(100, 15, 80)
ck("击穿概率 σ=15 %", f(kp["prob_pct"]), 9.1, 0.05)
ck("z", f(kp["z"]), -1.3333, 0.001)

kp30 = K.knockthrough_prob(100, 30, 80)
ck("击穿概率 σ=30 %", f(kp30["prob_pct"]), 25.2, 0.05)
ck("Φ(-4/3) 数值", f(kp["prob"]), 0.0912, 0.001)

ck("P ≤ μ−1.645σ", f(100 - 1.645 * 15), 75.325, 1e-9)
ck("1.645σ = 24.68", f(1.645 * 15), 24.675, 0.01)

# ---- 机会成本 ----
o = K.opportunity_cost(80, [100, 60])
ck("机会成本（放弃的最优）", f(o["opp_cost"]), 20, 1e-9)
ck("最优替代", f(o["best_alt"]), 100, 1e-9)
ck("相对最优净收益", f(o["net_vs_best"]), -20, 1e-9)
ck("不是最优", 0 if o["is_best"] else 1, 1)

# ---- 反过来想（§6.1） ----
inv = K.inversion(8, sp.Rational(1, 2), sp.Rational(1, 10))
ck("串联存活率 %", f(inv["S"]) * 100, 23.91, 0.005)
ck("整体失败率 %", f(inv["fail"]) * 100, 76.09, 0.005)
ck("最弱环失败占比 %", f(inv["fatal_share"]) * 100, 65.7, 0.05)
ck("先堵最弱 ×", f(inv["fix_weakest_gain"]), 1.80, 0.005)
ck("全员优化 ×", f(inv["polish_rest_gain"]), 1.46, 0.005)
ck("存活率上限 %", f(inv["ceiling"]) * 100, 43.05, 0.005)
ck("过一半所需 pw 上界", f(inv["pw_limit_for_half"]), -0.045, 0.0005)
ck("该结构下过不了一半", 1 if not inv["half_reachable"] else 0, 1)
ck("先堵最弱优于全员优化", 1 if inv["fix_is_better"] else 0, 1)

# ---- 激励优先（§6.2） ----
inc = K.incentive(20)
ck("委托人最优 x_P", f(inc["x_p"]), 10, 1e-9)
ck("代理人最优 x_A", f(inc["x_a"]), 5, 1e-9)
ck("错配 x_A − x_P", f(inc["misalign"]), -5, 1e-9)
ck("顾客最优价值 V(x_P)", f(inc["V_at_opt"]), 500, 1e-9)
ck("代理人最优处 V(x_A)", f(inc["V_at_agent"]), 375, 1e-9)
ck("顾客被白损失", f(inc["client_loss"]), 125, 1e-9)
ck("损失占比 %", f(inc["loss_share"]) * 100, 25.0, 1e-9)
ck("恰好对齐的提成 c*", f(inc["align_commission"]), 40, 1e-9)
inc60 = K.incentive(60)
ck("提成 60 时 x_A", f(inc60["x_a"]), 15, 1e-9)
ck("提成 60 时损失（与 20 对称）", f(inc60["client_loss"]), 125, 1e-9)

# ---- 能力圈（§6.3） ----
cp = K.competence(sp.Rational(1, 5), 10, 40, 0, sp.Rational(1, 5))
ck("组合方差 σ²", f(cp["sigma"]) ** 2, 128, 1e-9)
ck("组合 σ", f(cp["sigma"]), 11.31, 0.005)
ck("圈外占方差 %", f(cp["var_share_out"]) * 100, 50.0, 1e-9)
ck("临界暴露 w* %", f(cp["w_crit"]) * 100, 20.0, 1e-9)
ck("标准分 z", f(cp["z"]), -1.768, 0.0005)
ck("击穿概率 %", f(cp["prob"]) * 100, 3.85, 0.005)
ck("纯圈内击穿概率 %", f(cp["prob_pure"]) * 100, 2.28, 0.005)
ck("风险放大倍数", f(cp["prob_ratio"]), 1.69, 0.005)

# ---- Lollapalooza（§6.4） ----
lp = K.lollapalooza(4, sp.Rational(1, 2))
ck("乘法叠加 (1+a)^n", f(lp["product"]), 5.06, 0.005)
ck("线性直觉 1+na", f(lp["linear"]), 3.0, 1e-9)
ck("超出比例 %", f(lp["extra_pct"]) * 100, 68.8, 0.05)
ck("实际 / 直觉", f(lp["excess"]), 1.69, 0.005)
ck("超过 2 倍所需条数", lp["n_for_double"], 5, 1e-9)

# ---- 误判清单（§6.5） ----
bi = K.checklist(4, sp.Rational(1, 2), sp.Rational(1, 2))
ck("不上清单的冲动放大", f(bi["gross"]), 5.06, 0.005)
ck("上清单后的残余放大", f(bi["net"]), 0.316, 0.0005)
ck("拦截率 %", f(bi["blocked"]) * 100, 93.75, 0.005)
ck("风险被压低倍数", f(bi["cut"]), 16.0, 1e-9)

# ---- 汇总 ----
bad = [c for c in checks if not c[0]]
for ok, name, got, want in checks:
    if not ok:
        print(f"  FAIL {name}: got={got!r} want={want!r}")
print(f"\n{len(checks) - len(bad)}/{len(checks)} checks passed")
if bad:
    print(f"{len(bad)} FAILED")
    raise SystemExit(1)
print("docs/思维模型.md 数值核验全部通过 ✓")
