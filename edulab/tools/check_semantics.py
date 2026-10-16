# -*- coding: utf-8 -*-
"""check_semantics.py —— 语义校验器的雏形：图注里的定量断言，必须找得到出处。

背景：现有校验器只查**几何**（坐标是否越界、边距是否够），看不出「图注说错了」。
书稿那次 36 张图全绿，仍有 5 类图文不符是靠人工通读抓出来的。这个工具补的就是那一格。

核心设计 —— 「出处」怎么自动取：

  * mental-models：给 `models_kernel` 的所有公开函数**打桩**，记录它们算出来过的每一个数；
    然后逐个调用 `build_*()`。于是 witness = 「内核当年真的算出来过的数」。
    任何出现在文案里的数，若既不在 witness 集、也不在其廉价派生闭包里 → 报警。

  * 数学思想书：witness = **该图画布上真正画出来的文字里的数字**（text/label/sub 字段）。
    这直接实现「图上标注 vs 图注」。

另有一条**规则类**检查：文案里的「A 行 B 列共 C」必须满足 A×B = C。

诚实声明：这个工具只能抓「数字无出处」这一类。
它抓不到语义错配（说的和指的其实是两回事）、方位说反、以及「文字断言了表格的性质」。
所以最后附一份**回归测试**：拿我们历史上真实犯过的错当测试集，报告抓到几个、漏了几个。
工具的价值由这份报告决定，不由我声称。

用法：
    python edulab/tools/check_semantics.py               # 只跑回归测试
    python edulab/tools/check_semantics.py --scan        # 扫现有的书与 18 页
"""

import pathlib
import re
import sys
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "mental-models" / "lib"))
sys.path.insert(0, str(ROOT / "mental-models" / "scripts"))
sys.path.insert(0, str(ROOT / "edulab" / "books" / "math-thought"))

NUM_RE = re.compile(r"\d+(?:,\d{3})*(?:\.\d+)?")
TAG_RE = re.compile(r"<[^>]+>")          # HTML 标签：class='border-amber-400' 里的 400 不是断言
# 「A 行 B 列共 C」这类自洽性规则
GRID_RE = re.compile(r"(\d+)\s*行\s*(\d+)\s*列\s*[^。；\n]{0,8}?(\d+)")


def strip_markup(text):
    """剥掉 HTML 标签，只留下真正读给人看的文字。"""
    return TAG_RE.sub(" ", text)
CN_DIGIT = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
            "六": 6, "七": 7, "八": 8, "九": 9}
CN_UNIT = {"十": 10, "百": 100, "千": 1000, "万": 10000}


def cn_to_int(s):
    """中文数词 → 整数（覆盖 一/两/三…十/百/千/万 的常见组合，够用即可）。"""
    total, section, num = 0, 0, 0
    for ch in s:
        if ch in CN_DIGIT:
            num = CN_DIGIT[ch]
        elif ch in CN_UNIT:
            u = CN_UNIT[ch]
            if u == 10000:
                section = (section + (num or 1)) * u
                total += section
                section, num = 0, 0
            else:
                section += (num or 1) * u
                num = 0
        else:
            return None
    return total + section + num


def cn_claims(text):
    """从文本里抽中文数词断言：X分之Y（分数）、以及普通中文数词。"""
    out = []
    for m in re.finditer(r"([零一二两三四五六七八九十百千万]+)\s*分之\s*([零一二两三四五六七八九十百千万]+)", text):
        a, b = cn_to_int(m.group(2)), cn_to_int(m.group(1))
        if a and b:
            out.append({"value": a / b, "raw": m.group(0)})
    for m in re.finditer(r"[零一二两三四五六七八九十百千万]{2,}", text):
        v = cn_to_int(m.group(0))
        if v:
            out.append({"value": float(v), "raw": m.group(0)})
    if "一半" in text or "半仓" in text:
        out.append({"value": 0.5, "raw": "半"})
    return out


def to_float(raw):
    return float(raw.replace(",", ""))


def claims_in(text):
    """抽出文本里的定量断言：阿拉伯数字 + 中文数词。"""
    out = [{"value": to_float(m.group(0)), "raw": m.group(0)} for m in NUM_RE.finditer(text)]
    out += cn_claims(text)
    return out


SCALES = [2, 10, 100, 1000, 1e4, 1e6]


def derived_closure(vals):
    """witness 的派生闭包 —— **只做单位换算**（百分比、千分位、万）。

    这里做了两次校准，都记在报告里：
      · 闭包为空 → 误报 3.6%（0.575×100=57.5% 这类合法换算全被当成无出处）
      · 闭包放进任意两数的和/差/积/商 → 误报归零，但**真错也被解释掉了**：
        fig-universal 把 5 位写成 7 位，而 7 可以由 witness 里的两数相加得到，
        于是回归从 3/3 掉到 2/3。
    结论：**派生规则越宽，召回越低**。所以只保留「同一数量的不同单位」这一种派生 ——
    它对应真实的写作行为（把 0.575 写成 57.5%），而不会凭空造出新数。
    """
    out = set(vals)
    for v in vals:
        for k in SCALES:
            out.add(v * k)
            out.add(v / k)
    return out


def witnessed(value, witness, tol=2e-3):
    """命中判定：绝对/相对容差内等于任一 witness 或派生值。"""
    for w in witness:
        if w == 0:
            if abs(value) < 1e-9:
                return True
            continue
        if abs(value - w) <= max(tol, abs(w) * tol):
            return True
    return False


# =====================================================================
# witness 采集
# =====================================================================
def book_witness(fid, spec):
    """该图画布上真正画出来的文字里的数字。"""
    vals, seen = set(), []

    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                if isinstance(v, str) and k in ("text", "label", "sub", "value", "cite"):
                    seen.append(v)
                    for c in claims_in(v):
                        vals.add(c["value"])
                else:
                    walk(v)
        elif isinstance(node, list):
            for v in node:
                walk(v)
    walk(spec.get("layers", []))
    return vals, seen


def kernel_witness():
    """给 models_kernel 的公开函数打桩，把 build_* 全部跑一遍，收集它算出来过的每个数。"""
    import models_kernel as K
    vals = set()

    def collect(x, depth=0):
        if depth > 5 or isinstance(x, bool):
            return
        if isinstance(x, (int, float)):
            vals.add(float(x))
            return
        # 内核返回的是 sympy 对象（Integer/Rational/Float）与 Fraction，
        # 不转成 float 的话 witness 集几乎是空的 —— 这个坑第一次就踩了。
        try:
            import sympy as sp
            if isinstance(x, sp.Basic) and getattr(x, "is_number", False):
                vals.add(float(x))
                return
        except (TypeError, ValueError):
            pass
        if isinstance(x, Fraction):
            vals.add(float(x))
            return
        if isinstance(x, dict):
            for v in x.values():
                collect(v, depth + 1)
        elif isinstance(x, (list, tuple)):
            for v in x:
                collect(v, depth + 1)

    originals = {}
    for name in dir(K):
        if name.startswith("_"):
            continue
        fn = getattr(K, name)
        if callable(fn) and getattr(fn, "__module__", "") == "models_kernel":
            originals[name] = fn

            def make(f):
                def wrapped(*a, **kw):
                    r = f(*a, **kw)
                    collect(r)
                    return r
                return wrapped
            setattr(K, name, make(fn))
    try:
        import generate as G
        pages = {}
        for key in G.ORDER:
            pages[key] = G.REGISTRY[key]()
    finally:
        for name, fn in originals.items():
            setattr(K, name, fn)
    return vals, pages


# =====================================================================
# 报错
# =====================================================================
YEAR_LO, YEAR_HI = 1000, 2100


def scan_text(label, text, witness, flags, seen_numbers=None):
    """对一段文案跑 witness 检查，报告无出处的数字。"""
    text = strip_markup(text)
    # 结构性数字：第 N 步 / 图 N / 式 N —— 指代位置，不是定量断言
    structural = {m.group(1) for m in re.finditer(r"第\s*(\d+)\s*[步张囷节页条]", text)}
    for c in claims_in(text):
        v, raw = c["value"], c["raw"]
        # 白名单：年份、≤3 的小整数、结构性序号
        if v == int(v) and YEAR_LO <= v <= YEAR_HI:
            continue
        if v <= 3 or raw in structural:
            continue
        if witnessed(v, witness):
            continue
        flags.append({"where": label, "raw": raw, "value": v,
                      "context": _ctx(text, raw)})


def _ctx(text, raw, pad=18):
    i = text.find(raw)
    if i < 0:
        return text[:60]
    return text[max(0, i - pad):i + len(raw) + pad].replace("\n", " ")


def check_grid_rule(label, text, flags):
    for m in GRID_RE.finditer(text):
        a, b, c = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if a * b != c:
            flags.append({"where": label, "raw": m.group(0),
                          "value": f"{a}×{b}≠{c}",
                          "context": f"[规则] {a} 行 × {b} 列 应为 {a*b}，文中写 {c}"})


CALIBRATION = """校准记录：这一步失败过三次，都记下来，因为它比结论有用

  第 1 版  闭包为空、sympy 数没收集、HTML 标签没剥   误报 402/1757 = 22.9%
  第 2 版  修 sympy 收集 + 剥标签                    误报  63/1757 =  3.6%
  第 3 版  闭包放进「任意两数的和/差/积/商」          误报   0/1757 =  0.0%
           ——但回归从 3/3 掉到 2/3：fig-universal 把「5 位」写成「7 位」，
             而 7 可以由 witness 里的两数相加得到，于是真错被「解释」掉了。
  第 4 版  闭包只做单位换算（×/÷ 10 的幂与 2）        误报   2/2168 =  0.09%
          回归 3/3 = 100%

  结论：**派生规则越宽，召回越低。** 宁可留少量误报（人工一眼可判），
  也不要为了报表好看而把真错解释掉 —— 那正是这个工具存在的理由。
"""


def run_scan():
    print(CALIBRATION)
    print("=" * 78)
    print("扫描：数学思想（8 章）")
    print("=" * 78)
    import json
    import figures as F
    figs = F.build()
    chapter_captions = {}
    for p in sorted((ROOT / "edulab" / "books" / "math-thought" / "chapters").glob("ch*.json")):
        doc = json.loads(p.read_text(encoding="utf-8"))
        for b in doc.get("blocks", []):
            if b.get("type") == "figure" and b.get("caption"):
                chapter_captions.setdefault(b.get("id") or b.get("figure"), []).append(b["caption"])
    book_flags, total_claims, total_no_witness = [], 0, 0
    for fid, spec in figs.items():
        w, labels = book_witness(fid, spec)
        pooled = set(w)
        for note in spec.get("steps", []):
            for c in claims_in(note.get("note", "")):
                pooled.add(c["value"])
        w = derived_closure(set(pooled))
        texts = list(chapter_captions.get(fid, []))
        for note in spec.get("steps", []):
            texts.append(note.get("note", ""))
        claims = sum(len(claims_in(t)) for t in texts)
        total_claims += claims
        before = len(book_flags)
        for t in texts:
            scan_text(f"书 {fid}", t, w, book_flags)
            check_grid_rule(f"书 {fid}", t, book_flags)
        total_no_witness += len(book_flags) - before
    print(f"图数 {len(figs)}，断言 {total_claims} 条，其中无出处 {total_no_witness} 条（{total_no_witness/max(1,total_claims)*100:.1f}%）")
    for f in book_flags:
        print(f"  ⚠ [{f['where']}] 「{f['raw']}」 … {f['context']}")

    print()
    print("=" * 78)
    print("扫描：mental-models（18 页）")
    print("=" * 78)
    w, pages = kernel_witness()
    w = derived_closure(w)
    print(f"内核 witness 集：{len(w)} 个不同的数")
    mm_flags, total_claims2 = [], 0
    for key, page in pages.items():
        texts = []
        les = page.get("lesson", {})
        texts.append(les.get("problem", ""))
        for st in page.get("steps", []):
            texts.append(st.get("content", ""))
        total_claims2 += sum(len(claims_in(t)) for t in texts)
        for t in texts:
            scan_text(f"页 {key}", t, w, mm_flags)
            check_grid_rule(f"页 {key}", t, mm_flags)
    print(f"断言 {total_claims2} 条，其中无出处 {len(mm_flags)} 条（{len(mm_flags)/max(1,total_claims2)*100:.1f}%）")
    for f in mm_flags:
        print(f"  ⚠ [{f['where']}] 「{f['raw']}」 … {f['context']}")


# =====================================================================
# 回归测试：拿历史真实错误当测试集
# =====================================================================
def run_regression():
    """每条都是我们**真的犯过**的错。

    计分必须严格：**只有报出的值/规则命中那条错的本身，才算「抓到」**。
    只要报警就算命中，会把无关数字引起的误报当成战果 —— 那是自欺。
    """
    import figures as F
    figs = F.build()

    def book_w(fid):
        w, _ = book_witness(fid, figs[fid])
        for note in figs[fid].get("steps", []):
            for c in claims_in(note.get("note", "")):
                w.add(c["value"])
        return derived_closure(w)

    # target: 数字 → 必须报出该值；"GRID" → 必须触发自洽性规则；None → 本工具设计上不可查
    corpus = [
        ("书 ch06 fig-poincare 图注", book_w("fig-poincare"),
         "以 $K=-1$ 计，该三角形的双曲面积是 0.790（占整个圆盘的 12.6%），换算成角度正是 45.24 度。",
         "12.6% 并无出处（同一批数算出来的是 25.13%）", 12.6),
        ("书 ch07 正文", book_w("fig-cayley"),
         "结合律对这 36 行 36 列共 216 组元素逐个验证都成立。",
         "36 行 36 列 ≠ 216；实为 6×6×6 = 216", "GRID"),
        ("书 ch08 fig-universal 图注", book_w("fig-universal"),
         "把这张表编码成的数字串 E(M)（每个转移定长 7 位）。",
         "实为 5 位 —— 图上的标注写的就是 5", 7.0),
        ("书 ch06 fig-sphere 图注", book_w("fig-sphere"),
         "从北极上空俯视的地球仪，取北半球的八分之一。",
         "应为「北半球的四分之一」—— 词语指代错，八分之一这个数本身在图上有出处", None),
        ("书 ch07 fig-roots 图注", book_w("fig-roots"),
         "左边三步依次是 n=3,4,5。",
         "该图是单画布、没有左右分栏 —— 错在方位词，不在数字", None),
        ("书 ch08 fig-bb 图注", book_w("fig-bb"),
         "Σ(3)=6、T(3)=21 是同一台机器的两副面孔。",
         "Σ 与 T 其实是两台不同的机器 —— 概念错配", None),
        ("审计脚本（自产）", set(),
         "数值积分与解析式逐项吻合，所以这不是算错。",
         "同一次输出的表格标的是 ✗ —— 文字断言了**表格的性质**", None),
    ]

    print("=" * 78)
    print("回归测试：拿历史真实错误当测试集（只有命中该错本身才算抓到）")
    print("=" * 78)
    checkable = caught = 0
    for where, witness, text, why, target in corpus:
        flags = []
        scan_text(where, text, witness, flags)
        check_grid_rule(where, text, flags)
        if target is None:
            mark = "—  设计上不可查"
        else:
            if target == "GRID":
                hit = any("行" in str(f["raw"]) for f in flags)
            else:
                hit = any(isinstance(f["value"], float) and abs(f["value"] - target) < 1e-6
                          for f in flags)
            checkable += 1
            caught += hit
            mark = "✅ 抓到" if hit else "❌ 漏掉"
        print(f"{mark}  {where}")
        print(f"        原文：{text}")
        print(f"        真错：{why}")
        for f in flags:
            print(f"        报警：值={f['value']!r}  ← {f['context']}")
        print()
    n = len(corpus)
    print(f"可查 {checkable} 条，抓到 {caught} 条（{caught/max(1,checkable)*100:.0f}%）；"
          f"设计上不可查 {n-checkable} 条。")
    print()
    print("漏掉/不可查的四条指向同一件事 —— 文字与画面**语义**不符时，校验器看不见：")
    print("  词语指代错（八分之一 vs 四分之一）、方位说反、概念错配、断言了表格的性质。")
    print("所以真正有效的手段是让文字**无法**偏离：")
    print("  **文案由内核生成，而不是由人手写之后再校验。** 校验器只是兜底的那张网。")


def main(argv):
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        if "--scan" in argv:
            run_scan()
            print()
        run_regression()
    text = buf.getvalue()
    sys.stdout.write(text)          # 控制台照样打印（中文可能被终端编码弄花）
    if "--write" in argv:
        out = ROOT / "edulab" / "semantics-report.md"
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        sys.stdout.write(f"\n[written] {out.as_posix()}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
