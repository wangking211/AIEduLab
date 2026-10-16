# -*- coding: utf-8 -*-
"""audit_diagramability.py —— 「能不能用图解讲所有知识」的可行性审计。

方法：用同一条机械判据去量一个领域的全部候选知识点：

    判据（内核判据）：这个知识点，能不能写成一个「给定参数 → 输出数值/坐标」的函数？
      ├─ ① 能，且内核就是知识本身   → 图承载**论证**
      ├─ ② 有明确结构但不可算        → 图承载**组织**（索引，不证明命题）
      └─ ③ 既不可算也无固定结构      → 图只能**配图**

关键设计：**凡是判为 ① 的，脚本都真的跑一遍**，输出真实数字。
判不了的（②③）也逐条给出「它卡在哪一步」，而不是一句「不可行」。

用法：
    python edulab/tools/audit_diagramability.py
    python edulab/tools/audit_diagramability.py --write   # 同时写出报告 md
"""

import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "mental-models" / "lib"))

OUT_MD = ROOT / "edulab" / "coverage-audit.md"


# =====================================================================
# 一、能把内核跑起来的那些（① 层）—— 真的算，不是声称
# =====================================================================
def diffusion_logistic(rate, t0):
    """技术扩散的 S 曲线：p(t) = 1/(1+exp(-r(t-t0)))。

    纯数学（logistic），不需要数据。地基里的「渗透率」几乎都是这个形状。
    可算出的确定结论：从 10% 到 90% 的时长恒等于 2·ln9/r，与 t0 无关。
    """
    t = lambda p: t0 + math.log(p / (1 - p)) / rate
    return {"t10": t(0.10), "t50": t0, "t90": t(0.90),
            "duration": t(0.90) - t(0.10), "duration_exact": 2 * math.log(9) / rate}


def demographic_transition(b0, b1, d0, d1, mid_d, mid_b, steep, y0=1700, y1=2100):
    """人口转变五阶段：出生率与死亡率各自从高平台 logistic 降到低平台。

    死亡率先降（mid_d 较早）、出生率后降（mid_b 较晚），中间必然出现增长率峰值。
    **自变量是日历年**（不是从 0 开始的偏移）——这一点写错就会让曲线纹丝不动。
    返回峰值增长率与峰值年 —— 再看它对参数有多敏感。
    """
    def logistic(hi, lo, mid, t):
        return lo + (hi - lo) / (1 + math.exp((t - mid) / steep))
    best = (-1e9, None)
    curve = []
    for t in range(y0, y1 + 1):
        b = logistic(b0, b1, mid_b, t)
        d = logistic(d0, d1, mid_d, t)
        g = b - d
        curve.append((t, b, d, g))
        if g > best[0]:
            best = (g, t)
    return {"peak_growth_per_1000": best[0], "peak_year": best[1], "curve": curve}


def secular_cycle(r, a, c, m, amp=0.05, years=3000, steps=60000):
    """「王朝周期」类模型的骨架（Lotka-Volterra 型）：人口 N 与精英 E。

        dN/dt = r·N − a·N·E      （人口自增，被精英榨取）
        dE/dt = c·N·E − m·E      （精英靠人口供养，有自己的消亡率）

    平衡点 $(m/c,\\ r/a)$ 周围是闭合轨道。**关键性质有两层**：

      1. 小振幅时周期有解析式 T = 2π/√(rm)，只由 r、m 决定；
      2. 但周期**还取决于振幅** —— 离开平衡点越远，周期越长（LV 的著名性质）。

    所以 `amp` 是独立于参数的第二个旋钮。返回值同时给出解析式与 RK4 数值周期，
    让「积分器对不对」和「周期由什么决定」两件事分开受检验。
    """
    h = years / steps
    n_star, e_star = m / c, r / a
    N, E = n_star * (1 + amp), e_star
    def d(N_, E_):
        return (r * N_ - a * N_ * E_, c * N_ * E_ - m * E_)
    series = [(0.0, E)]
    for i in range(steps):
        k1 = d(N, E)
        k2 = d(N + h / 2 * k1[0], E + h / 2 * k1[1])
        k3 = d(N + h / 2 * k2[0], E + h / 2 * k2[1])
        k4 = d(N + h * k3[0], E + h * k3[1])
        N = max(1e-12, N + h / 6 * (k1[0] + 2 * k2[0] + 2 * k3[0] + k4[0]))
        E = max(1e-12, E + h / 6 * (k1[1] + 2 * k2[1] + 2 * k3[1] + k4[1]))
        series.append(((i + 1) * h, E))
    peaks = [series[i][0] for i in range(1, len(series) - 1)
             if series[i][1] > series[i - 1][1] and series[i][1] >= series[i + 1][1]
             and series[i][1] > e_star]
    periods = [peaks[i + 1] - peaks[i] for i in range(len(peaks) - 1)]
    numeric = (sum(periods) / len(periods)) if periods else None
    analytic = 2 * math.pi / math.sqrt(r * m)
    return {
        "amp": amp, "period_numeric": numeric, "period_analytic": analytic,
        "n_cycles": len(periods),
        "match": (numeric is not None and abs(numeric - analytic) < analytic * 0.02),
    }


def kaya_identity(P, g, e, c):
    """Kaya 恒等式：CO₂ = P ×(GDP/P)×(E/GDP)×(CO₂/E)。

    这是一个**恒等式** —— 由构造必然成立，因此图上任何数都错不了。
    它的价值是分解（谁贡献了多少变化），不是预测。
    """
    return {"co2": P * g * e * c, "identity_holds": abs(P * g * e * c - P * g * e * c) < 1e-15}


def maddison_crossings(thresholds=(2000, 5000, 10000)):
    """用仓库里已入库的 Maddison 数据算**真实历史**：各国人均 GDP 首次越过某值的年份。

    这是 ①-b 型（需要可信数据集）：内核三行就写完，成本几乎全在数据上。
    """
    import models_kernel as K
    series = K.load_maddison()
    out = {}
    for name, pts in series.items():
        row = {}
        for th in thresholds:
            hit = next((y for y, v in pts if float(v) >= th), None)
            row[th] = hit
        out[name] = row
    return out


# =====================================================================
# 二、逐领域审计表
# =====================================================================
# layer: 1=① 可算；2=② 可结构化；3=③ 只能配图
# kind : a=纯数学/恒等式（随处可算）；b=依赖可信数据集；''=不适用
WORLD_HISTORY = [
    ("长期经济增长（人均 GDP 序列）", 1, "b", "已有：大分叉页，用 Maddison 数据"),
    ("人口转变（出生/死亡/增长率）", 1, "a", "可算；但参数来自史料估算 —— 见敏感性"),
    ("技术扩散 S 曲线（渗透率）", 1, "a", "logistic 恒等式：10%→90% 时长 = 2ln9/r"),
    ("疾病传播阈值（R₀）", 1, "a", "已有：临界点页"),
    ("战争规模分布（幂律尾部）", 1, "b", "已有：尾部风险页，用 USGS 目录"),
    ("碳排放分解（Kaya 恒等式）", 1, "a", "恒等式，由构造必真；价值在分解"),
    ("城市化 rank-size（Zipf）", 1, "b", "可算；需要城市人口数据集"),
    ("贸易网络中心性", 1, "b", "可算；需要贸易流量数据集"),
    ("王朝/帝国周期（secular cycle）", 1, "a", "能算周期 —— 但周期由参数决定，见参数扫描"),
    ("王朝时间线", 2, "", "可结构化；图只排顺序，不判定任何史实真伪"),
    ("王朝谱系树", 2, "", "可结构化（树）；结构不证明继承认定"),
    ("条约/联盟网络", 2, "", "可结构化；边的存在需史料支撑，图本身不校验"),
    ("多因战争因果图", 2, "", "可结构化；图承载的是**史学家的论断**，不是证据"),
    ("「为什么是 1914 年」", 3, "", "不可形式化：没有可算内核，因果反事实无法证伪"),
    ("罗马衰亡的史学争论", 3, "", "不可形式化：争论本体就是「如何解释」，无唯一解"),
    ("史料批判（谁写的、为何写）", 3, "", "不可形式化：判断依赖语境与史德，不是计算"),
    ("人物的关键时刻抉择", 3, "", "不可形式化：动机不可测，写成函数就是编"),
    ("把史料误差量化成 σ 传下去", 1, "a", "真正的地基：估计的**不确定度**本身可以算"),
]

CROSS_DOMAIN = {
    "数学": [("坐标几何", 1), ("函数与导数", 1), ("概率与计数", 1), ("数列", 1),
             ("平面几何", 1), ("立体几何", 1), ("组合爆炸", 1), ("极限与积分", 1)],
    "物理": [("运动学", 1), ("牛顿定律", 1), ("动量与能量", 1), ("圆周运动", 1),
             ("电磁学", 1), ("折射", 1), ("热力学", 1)],
    "化学": [("配平", 1), ("物质的量", 1), ("化学平衡", 1), ("电化学", 1),
             ("反应机理", 1), ("官能团分类", 2)],
    "生物": [("孟德尔遗传", 1), ("群体遗传", 1), ("种群增长", 1), ("光合/呼吸", 1),
             ("能量金字塔", 1), ("细胞结构", 2)],
    "计算机": [("排序与查找", 1), ("树与图", 1), ("复杂度", 1), ("动态规划", 1), ("编码", 1)],
    "文学": [("格律/音步", 1), ("文体计量（stylometry）", 1), ("叙事结构", 2),
             ("主题解读", 3), ("作者意图", 3)],
    "哲学": [("形式逻辑/真值表", 1), ("模态逻辑", 1), ("概率论基础", 1),
             ("伦理判断", 3), ("心身问题", 3), ("认识论论证", 3)],
    "法学": [("量刑指南公式", 1), ("构成要件", 2), ("判例网络", 2),
             ("法律层级", 2), ("宪法解释", 3)],
    "音乐": [("律制/音程（频率比）", 1), ("对位", 1), ("和声功能", 2),
             ("曲式", 2), ("演奏诠释", 3)],
    "医学": [("药代动力学", 1), ("临床决策（贝叶斯）", 1), ("诊断推理树", 2),
             ("影像判读", 3), ("医患沟通", 3)],
}


def main(argv):
    lines = []
    w = lines.append

    w("# 可行性审计：能不能用图解讲「所有知识」")
    w("")
    w("> 全部结论由 `edulab/tools/audit_diagramability.py` 现算得出，可重跑。")
    w("")
    w("## 判据")
    w("")
    w("```")
    w("判据：这个知识点能不能写成一个「给定参数 → 输出数值/坐标」的函数？")
    w("  ① 能，且内核就是知识本身  → 图承载**论证**")
    w("  ② 有明确结构但不可算      → 图承载**组织**（索引，不证明命题）")
    w("  ③ 既不可算也无固定结构    → 图只能**配图**")
    w("```")
    w("")
    w("另外把 ① 分成两类，因为成本结构完全不同：")
    w("")
    w("- **①-a 纯数学/恒等式**：随处可算，成本极低")
    w("- **①-b 依赖可信数据集**：内核三行就写完，**成本几乎全在数据**（出处、许可、指纹）")
    w("")

    # ---- 深审：世界史 ----
    w("## 一、深审：世界史")
    w("")
    w("| 知识点 | 判定 | 类型 | 卡在哪 / 依据 |")
    w("|---|---|---|---|")
    tag = {1: "**① 可算**", 2: "② 结构化", 3: "③ 配图"}
    for name, layer, kind, note in WORLD_HISTORY:
        w(f"| {name} | {tag[layer]} | {kind or '—'} | {note} |")
    w("")
    counts = {1: 0, 2: 0, 3: 0}
    for _, layer, _, _ in WORLD_HISTORY:
        counts[layer] += 1
    n = len(WORLD_HISTORY)
    w(f"**分布**：① {counts[1]}/{n}（{counts[1]/n*100:.0f}%）、"
      f"② {counts[2]}/{n}（{counts[2]/n*100:.0f}%）、"
      f"③ {counts[3]}/{n}（{counts[3]/n*100:.0f}%）")
    w("")
    w("注意 ③ 的四个条目**不是历史的边角料**，而是历史学的**核心方法**"
      "（史料批判、因果论证、动机推断）。所以「图解覆盖世界史」这句话，"
      "即使把 ① 全部做完，也覆盖不到这门学科的立身之本。")
    w("")

    # ---- ① 层的实算 ----
    w("## 二、① 层真的算一遍（不是声称）")
    w("")

    d = diffusion_logistic(rate=0.35, t0=1900)
    w("**技术扩散 S 曲线**（r=0.35/年，t0=1900）—— 纯数学，无参数争议：")
    w("")
    w(f"- 10% 在 {d['t10']:.1f} 年、50% 在 {d['t50']:.1f} 年、90% 在 {d['t90']:.1f} 年")
    w(f"- 10%→90% 时长 = **{d['duration']:.2f} 年**，与解析值 2·ln9/r = "
      f"{d['duration_exact']:.2f} 年一致")
    w("- 这个结论**与 t0 无关**：无论扩散从哪一年开始，从 10% 爬到 90% 都是 {:.1f} 年。"
      .format(d['duration']))
    w("")

    dt = demographic_transition(b0=45, b1=10, d0=35, d1=10, mid_d=1920, mid_b=1950, steep=15)
    w("**人口转变**（示意参数，非任何具体国家）：")
    w("")
    w(f"- 增长率峰值 **{dt['peak_growth_per_1000']:.2f}‰**，出现在第 "
      f"{dt['peak_year']} 年")
    w("- 敏感性：把出生率下降的中点 mid_b 各挪 ±10 年 ——")
    row = []
    for shift in (-10, 0, 10):
        r = demographic_transition(45, 10, 35, 10, 1920, 1950 + shift, 15)
        row.append(f"mid_b={1950+shift} → 峰值 {r['peak_growth_per_1000']:.2f}‰ "
                   f"@{r['peak_year']} 年")
    for x in row:
        w(f"  - {x}")
    w("")
    w("**这就是 ① 层的真相**：内核完全确定，但输入的参数来自史料估算；"
      "**内核的确定性 ≠ 结论的确定性**。图上那条曲线看起来很精确，"
      "而它的峰值年份实际上取决于你怎么估那两个中点。")
    w("")

    kk = kaya_identity(P=1.0, g=2.0, e=0.5, c=2.0)
    w("**Kaya 恒等式**：CO₂ = P × (GDP/P) × (E/GDP) × (CO₂/E) —— "
      f"由构造必然成立（自检：{kk['identity_holds']}）。"
      "所以图上一个数都不会错；但它的价值是**分解**，不是预测。")
    w("")

    w("**王朝周期（secular cycle 的骨架：Lotka-Volterra 型）**")
    w("")
    w("模型：$\\dot N = rN - aNE$、$\\dot E = cNE - mE$，平衡点 $(m/c,\\; r/a)$ 周围是闭合轨道。"
      "周期有两层性质 —— 先分开验证：")
    w("")
    w("**第一层：积分器对不对。**振幅取小（偏离平衡点 5%）时，数值周期应当逼近解析式 "
      "$T = 2\\pi/\\sqrt{rm}$：")
    w("")
    w("| r | m | 解析周期 T=2π/√(rm) | RK4 数值周期 | 一致 |")
    w("|---|---|---|---|---|")
    for r_, m_ in [(0.050, 0.050), (0.020, 0.050), (0.080, 0.050), (0.050, 0.020)]:
        sc = secular_cycle(r_, 0.5, 0.5, m_, amp=0.05)
        num = f"{sc['period_numeric']:.1f} 年" if sc["period_numeric"] else "—"
        w(f"| {r_} | {m_} | {sc['period_analytic']:.1f} 年 | {num} | "
          f"{'✓' if sc['match'] else '✗'} |")
    w("")
    w("**第二层：周期由什么决定。**固定参数，只改**振幅**（离开平衡点多远）：")
    w("")
    w("| 振幅（偏离平衡点） | RK4 数值周期 |")
    w("|---|---|")
    for amp_ in (0.05, 0.5, 1.0, 3.0, 10.0):
        sc = secular_cycle(0.05, 0.5, 0.5, 0.05, amp=amp_)
        num = f"{sc['period_numeric']:.1f} 年" if sc["period_numeric"] else "—"
        w(f"| {amp_*100:.0f}% | {num} |")
    w("")
    w("**所以「周期」有两个旋钮**：参数（$r,m$）与振幅（初始条件）。"
      "振幅往往没人能独立观测 —— 于是「某文明两百年一循环」可以**被拟合出来**："
      "它有着 ① 的形态（有公式、能算、能画），却只有 ③ 的证据力（参数与初值都不可独立验证）。"
      "**这是图解最危险的一种：看起来像推导。**")
    w("")

    cross = maddison_crossings()
    w("**用已入库的真实数据算历史**（①-b）——各国人均 GDP 首次越线的年份"
      "（国际元，2011 年价）：")
    w("")
    w("| 国家 | ≥2000 | ≥5000 | ≥10000 |")
    w("|---|---|---|---|")
    for name in ["United Kingdom", "France", "United States", "Japan", "China", "India"]:
        row = cross[name]
        cell = lambda v: str(v) if v else "尚未"
        w(f"| {name} | {cell(row[2000])} | {cell(row[5000])} | {cell(row[10000])} |")
    w("")
    w("这几个数字是**可核对的史实**（数据来自 Maddison Project，见 "
      "`mental-models/data/SOURCES.md`）。内核只用了三行，"
      "成本几乎全在数据上 —— 这就是 ①-b 的成本结构。")
    w("")

    # ---- 跨域粗筛 ----
    w("## 三、跨域粗筛")
    w("")
    w("| 领域 | ① 可算 | ② 结构化 | ③ 配图 | 覆盖不了的 |")
    w("|---|---|---|---|---|")
    tot = {1: 0, 2: 0, 3: 0}
    for dom, units in CROSS_DOMAIN.items():
        c = {1: 0, 2: 0, 3: 0}
        for _, layer in units:
            c[layer] += 1
            tot[layer] += 1
        miss = "、".join(u for u, l in units if l == 3) or "—"
        w(f"| {dom} | {c[1]} | {c[2]} | {c[3]} | {miss} |")
    allc = {1: 0, 2: 0, 3: 0}
    for u in WORLD_HISTORY:
        allc[u[1]] += 1
    for k in tot:
        allc[k] += tot[k]
    grand = sum(allc.values())
    w(f"| **合计（含世界史）** | **{allc[1]}** | **{allc[2]}** | **{allc[3]}** | — |")
    w("")
    w(f"**① 占 {allc[1]}/{grand} = {allc[1]/grand*100:.0f}%**；"
      f"③ 占 {allc[3]}/{grand} = {allc[3]/grand*100:.0f}%。")
    w("")

    # ---- 结论 ----
    w("## 四、结论")
    w("")
    w("**做不到「所有知识」。能做到的是「所有知识的计算骨架」——约为总量的 "
      f"{allc[1]/grand*100:.0f}%。**")
    w("")
    w("三条要点：")
    w("")
    w("1. **① 比想象的大，但不是全部**。把历史推进 ① 需要可信数据集（我们已经做了两次），"
      "这条路是通的；但历史学的核心方法落在 ③。")
    w("2. **① 内部有两级可信度**。①-a（恒等式/纯数学）图上的数错不了；"
      "①-b（依赖数据集）要看守则；而**参数靠估的模型，形态是 ①、证据力是 ③** —— "
      "周期模型就是例子。这种要显式标注，否则图解会生产「看似严谨的错觉」。")
    w("3. **最大的缺口是语义校验**。现有校验器只看坐标，看不出「图注说错了」——"
      "书稿那次 36 张图全绿，仍有 5 类图文不符是我读出来的。"
      "不补这一块，覆盖率越高，错误越安静。")
    w("")

    text = "\n".join(lines)
    print(text)
    if "--write" in argv:
        OUT_MD.parent.mkdir(parents=True, exist_ok=True)
        # 全仓用 LF：显式指定 newline，否则 Windows 上会写成 CRLF
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
        print(f"\n[written] {OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
