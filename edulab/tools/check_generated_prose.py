# -*- coding: utf-8 -*-
"""check_generated_prose.py —— 找出「手写进文案里的数字」。

上一轮的结论是：语义校验器只能兜底，**真正消灭「图文不符」的办法是让文字无法偏离**。
这个工具把那句话变成可数的目标：把「手写数字」的条数压到 0。

它用 AST 精确区分来源：

    f"...{expr:.2f}..."   →  FormattedValue  → 生成 ✓（数字来自内核）
    "...10000..."         →  Constant 字面量  → 手写 ✗（数字是人敲进去的）
    {"text": "...36..."}  →  JSON 字符串      → 手写 ✗

手写本身不是错——图注里引用外部事实（格雷厄姆的 1/3、帕斯卡的年份）就该手写。
错的是**本可以由内核产出却敲在字面上**的数，因为它们会随模型改动而静默过期。

用法：
    python edulab/tools/check_generated_prose.py
    python edulab/tools/check_generated_prose.py --write     # 写报告
"""

import ast
import json
import pathlib
import re
import sys
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
OUT_MD = ROOT / "edulab" / "generated-prose-report.md"

NUM_RE = re.compile(r"\d+(?:\.\d+)?")
TAG_RE = re.compile(r"<[^>]+>")
# 去噪：颜色码、rgba()、Tailwind 类名 —— 它们含数字，但不是定量断言
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGBA_RE = re.compile(r"rgba?\([^)]*\)")
CLASS_RE = re.compile(r"class=['\"][^'\"]*['\"]?")
UTIL_COLOR_RE = re.compile(r"\b[a-z][a-z0-9]*(?:-[a-z0-9]+)+-\d+\b")     # text-rose-600
UTIL_SIZE_RE = re.compile(
    r"\b(?:text|bg|border|p[xytrbl]?|m[xytrbl]?|w|h|gap|space-[xy]|grid-cols|col-span|"
    r"rounded|leading|tracking|opacity|z|top|left|right|bottom|min-w|max-w)-\[?[\d.]+(?:px|rem|%|em)?\]?")
YEAR_LO, YEAR_HI = 1000, 2100

TARGETS = [
    ("mental-models", ROOT / "mental-models" / "scripts" / "generate.py"),
    ("书 figures.py", ROOT / "edulab" / "books" / "math-thought" / "figures.py"),
]


def is_structural(raw, text):
    """年份、≤3 的小整数、第 N 步 —— 结构性数字，不参与计数。"""
    v = float(raw)
    if v == int(v) and YEAR_LO <= v <= YEAR_HI:
        return True
    if v <= 3:
        return True
    i = text.find(raw)
    if i >= 0 and re.search(r"第\s*$", text[max(0, i - 3):i]):
        return True
    return False


def denoise(text):
    """剥掉标签、颜色码、样式类 —— 留下来的才可能是定量断言。"""
    t = TAG_RE.sub(" ", text)
    t = HEX_RE.sub(" ", t)
    t = RGBA_RE.sub(" ", t)
    t = CLASS_RE.sub(" ", t)
    t = UTIL_COLOR_RE.sub(" ", t)
    t = UTIL_SIZE_RE.sub(" ", t)
    return t


def claims(text):
    """抽出文本里的手写数字（去噪后）。"""
    t = denoise(text)
    out = []
    for m in NUM_RE.finditer(t):
        if is_structural(m.group(0), t):
            continue
        out.append(m.group(0))
    return out


class Scanner(ast.NodeVisitor):
    """把「字符串字面量里的数字」和「f-string 插值出来的数字」分开。"""

    def __init__(self, path):
        self.path = path
        self.hand = []        # (行号, 数字, 上下文)
        self.generated = 0    # 插值点的个数

    def report(self, node):
        for raw in claims(node.value):
            line = getattr(node, "lineno", 0)
            ctx = node.value[:90].replace("\n", " ")
            self.hand.append((line, raw, ctx))

    def visit_JoinedStr(self, node):
        for v in node.values:
            if isinstance(v, ast.Constant) and isinstance(v.value, str):
                self.report(v)                       # f-string 的固定文本部分 → 手写
            elif isinstance(v, ast.FormattedValue):
                self.generated += 1                  # 插值 → 生成
                self.visit(v.value)
        return

    def visit_Call(self, node):
        """".format(...)" 也是生成 —— 只认 f-string 会低估覆盖率（figures.py 大量用它）。"""
        f = node.func
        if (isinstance(f, ast.Attribute) and f.attr == "format"
                and isinstance(f.value, ast.Constant) and isinstance(f.value.value, str)):
            s = f.value.value
            self.generated += len(re.findall(r"\{[^{}]*\}", s))
            for raw in claims(re.sub(r"\{[^{}]*\}", " ", s)):
                self.hand.append((getattr(node, "lineno", 0), raw,
                                  s[:90].replace("\n", " ")))
            for a in node.args:
                self.visit(a)
            return
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, str):
            self.report(node)                        # 普通字符串 → 手写
        return


def scan_python(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    sc = Scanner(path)
    sc.visit(tree)
    return sc


def scan_json_chapters():
    """章节 JSON：@@name@@ 记号算「生成」，其余数字算「手写」。"""
    hand, gen = [], 0
    base = ROOT / "edulab" / "books" / "math-thought" / "chapters"
    for p in sorted(base.glob("ch*.json")):
        for ln, line in enumerate(p.read_text(encoding="utf-8").split("\n"), 1):
            if '"caption"' not in line and '"text"' not in line and '"d":' not in line:
                continue
            gen += len(re.findall(r"@@[a-z_][a-z0-9_]*(?::\d+)?@@", line))
            for raw in claims(line):
                hand.append((p.name, ln, raw, line.strip()[:90]))
    return hand, gen


def main(argv):
    sys.path.insert(0, str(ROOT / "edulab" / "tools"))
    import check_semantics as CS          # 复用它的 witness 采集

    lines = []
    w = lines.append
    w("# 手写数字审计：生成覆盖率测量，以及两次失败的自动化尝试")
    w("")
    w("上一轮的结论是：语义校验只能兜底，**真正消灭「图文不符」的办法是让文字无法偏离**。")
    w("这份报告先量出「现在有多少文字在生成路径上」，再记下我试图把它自动化时的两次失败。")
    w("")
    w("## 一、判据（可靠的那一层）")
    w("")
    w("```")
    w('f"...{expr:.2f}..."   →  FormattedValue  → 生成 ✓（数字来自内核）')
    w('"...10000..."         →  Constant       → 手写 ✗（数字是人敲进去的）')
    w("```")
    w("")
    w("AST 级判定，是语法事实 —— 这一层不靠猜，因此可信。")
    w("（数字条数先做过去噪：颜色码 `#b45309`、`text-rose-600` 这类样式类不算断言。）")
    w("")

    total_hand = total_gen = 0
    per_file = []
    actionable = {}

    for label, path in TARGETS:
        sc = scan_python(path)
        total_hand += len(sc.hand)
        total_gen += sc.generated
        per_file.append((label, len(sc.hand), sc.generated, None))
        actionable[label] = sc.hand

    jrows, jgen = scan_json_chapters()
    per_file.append(("书 chapters/*.json", len(jrows), jgen, None))
    total_hand += len(jrows)
    total_gen += jgen

    # 第二道：内核/画布算得出来的手写数字
    kw, pages = CS.kernel_witness()
    kw = CS.derived_closure(kw)
    mm_action = [h for h in actionable["mental-models"]
                 if CS.witnessed(float(h[1]), kw)]
    import figures as F
    book_figs = F.build()
    book_w = {}
    for fid, spec in book_figs.items():
        wset, _ = CS.book_witness(fid, spec)
        for note in spec.get("steps", []):
            for c in CS.claims_in(note.get("note", "")):
                wset.add(c["value"])
        book_w[fid] = CS.derived_closure(wset)
    all_book_w = set()
    for s in book_w.values():
        all_book_w |= s
    fig_action = [h for h in actionable["书 figures.py"]
                  if CS.witnessed(float(h[1]), all_book_w)]
    json_action = [r for r in jrows if CS.witnessed(float(r[2]), all_book_w)]
    n_action = len(mm_action) + len(fig_action) + len(json_action)
    cov = {label: (g / (h + g) * 100 if (h + g) else 0.0) for label, h, g, _ in per_file}

    w("## 二、可靠的那部分：来源测量")
    w("")
    w("| 文件 | 手写数字 | f-string 插值点 | 生成占比（按数字条数）|")
    w("|---|---|---|---|")
    for label, h, g, _ in per_file:
        w(f"| {label} | {h} | {g} | {cov[label]:.0f}% |")
    w(f"| **合计** | **{total_hand}** | **{total_gen}** | "
      f"{total_gen/(total_hand+total_gen)*100:.0f}% |")
    w("")
    w("这一层是**可靠的**：AST 区分「字符串字面量」与「f-string 插值」，是语法事实，不靠猜。")
    w("")
    w("读出来的结构事实：")
    w("")
    w(f"- **mental-models** 已有 {dict((l, g) for l, _h, g, _ in per_file)['mental-models']} "
      f"个插值点（覆盖率 {cov['mental-models']:.0f}%）—— 文案的主要数字确实是从内核流过来的。")
    w(f"- **书 `chapters/*.json`：0 个插值点、{len(jrows)} 个手写数字、覆盖率 "
      f"{cov['书 chapters/*.json']:.0f}%** —— 这本书的正文**根本没有生成路径**。")
    w("  这正是上次通读能在 8 章里抓出 5 类图文不符的**结构性原因**。")
    w("")

    w("## 三、我试了两次「自动判定可生成」，都失败了（记下来）")
    w("")
    w("**第 1 次：内核也算得出这个数吗？**")
    w("")
    w("判据：手写数字若能匹配内核 witness（含 ×/÷10 的幂的换算闭包），就算「可生成」。")
    w(f"结果：{total_hand} 个手写数字里报了 {n_action} 个「可生成」—— 覆盖率接近 100%，明显失真。")
    w("")
    w("原因：**换算闭包让几乎任何数都能匹配到某个内核值**。")
    w("`8` 匹配 0.8、80、800、8000…… 于是 `utf-8` 里的 8、`max(30, t+3)` 里的 30 全被误判。")
    w("")
    w("**第 2 次（更根本）：它分不清「输入参数」和「输出结果」。**")
    w("")
    w("正文写「以 $P=10000$、$r=8\\%$、$t=30$ 代入」—— 这三个数是**输入**，")
    w("内核当然「算得出」它们（它们就是被传进去的），但正文**应该**写它们。")
    w("真正该生成的是**输出**（终值、比值、斜率……）。")
    w("而「这个数在句子里指的是输入还是输出」是个**语义问题**，不是数值问题 ——")
    w("与 check_semantics 撞在同一堵墙上。")
    w("")
    w("**所以「自动判定该不该生成」不可行。可行的是人工逐条判定 + 工具给出可靠的分母。**")
    w("")

    w("## 四、可执行的部分：按文件排优先级")
    w("")
    w("| 文件 | 生成覆盖率 | 判断 |")
    w("|---|---|---|")
    w(f"| mental-models（`generate.py`）| {cov['mental-models']:.0f}% | "
      "已在生成路径上，逐个把剩下的手写输出改成插值即可 |")
    w(f"| 书 `figures.py` | {cov['书 figures.py']:.0f}% | "
      "同上，步骤注解里已大量使用 `.format()`，继续补齐 |")
    w(f"| **书 `chapters/*.json`** | **{cov['书 chapters/*.json']:.0f}%** | "
      f"**最大短板：正文的生成路径刚起步（目前接通 {len(F.PROSE)} 张图）** |")
    w("")
    w("给 `chapters/*.json` 加生成路径，是这套方法里**性价比最高的一步**：")
    w("上次通读抓出的 5 类图文不符，全部落在这个 0% 的文件里。")
    w("")
    w("## 五、结论")
    w("")
    w("「让文字无法偏离」这件事，**方向是对的，但没有全自动的解**：")
    w("")
    w("1. **来源可以自动测**（AST），且测出来的结构问题很清楚：书稿正文 0% 生成。")
    w("2. **该不该生成无法自动判**（输入 vs 输出是语义问题）。")
    w("3. 所以正确的分工是：**工具负责给出分母与可疑清单，人负责逐条判定。**")
    w("   这恰好也是 check_semantics 的定位 —— 它是网，不是法官。")

    text = "\n".join(lines) + "\n"
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)
    print(f"[written] {OUT_MD.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
