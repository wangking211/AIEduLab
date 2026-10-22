# -*- coding: utf-8 -*-
"""facts.py — 事实登记与核查：让书里每个数都带着「它是怎么来的」。

为什么要有它
------------
一本讲「万物尺度」的书，最危险的失败模式不是算错，而是**数字看着精确、来源经不起追问**：
正文写下「138 亿年」，读者无法判断它是测出来的、推出来的、还是从别处抄来的。
本模块把「一个数从哪来」变成**登记项**，并交给闸门强制：

    现算  → 必须给复算函数，闸门当场重算并比对（值不符即红）
    实测  → 必须有出处 + 可核链接 + 不确定度
    文献  → 必须有出处 + 可核定位（页码 / 表号 / DOI）
    约定  → 必须写明「为什么只能约定」，并逐条列出

再加一条更狠的：**正文里不许出现未登记的数字**。数字要么写成 `@@记号@@`
（值由内核现算），要么落在某条登记的 `texts` 里。这条规则连「1838 年」这种年份
也不放过 —— 年份也是事实，写错了同样是错。

设计约束
--------
· 登记走带签名的构造函数 `claim(...)`：缺必填项**当场报错**，不留到闸门才发现。
· 白名单（`allow_pattern`）必须**逐条给理由**。白名单就是「已批准的不一致」——
  批准可以，但不许无声地批准。
· 判据分两类：`F1/F2/F3` 管登记表自身，`F4` 管正文里有没有漏网的数字。

用法
----
    from facts import Registry, claim

    REG = Registry("宇宙尺度")
    REG.add(claim("age_universe", 13.797e9, "年", grade="实测",
                  source="Planck 2018 结果 VI（A&A 641, A6）表 2，TT,TE,EE+lowE+lensing",
                  url="https://doi.org/10.1051/0004-6361/201833910",
                  uncertainty=0.023e9))
    REG.add(claim("light_year", 9.4607304725808e15, "米", grade="现算",
                  recompute=lambda: 299792458.0 * 365.25 * 86400.0))
"""
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE / "viz") not in sys.path:      # 与图形校验共用同一份 Report 结构
    sys.path.insert(0, str(_HERE / "viz"))
import vizkit                                # noqa: E402

Report = vizkit.Report

GRADES = ("现算", "实测", "文献", "约定")

# 各等级的必填项。None / "" / 空序列都算缺。
REQUIRED = {
    "现算": ("recompute",),
    "实测": ("source", "url", "uncertainty"),
    "文献": ("source", "locator"),
    "约定": ("note",),
}

# 「明显是编号」的形式：图 10.1 / 表 3 / 第 8 章 / (1)（2）这类，不是事实量。
_STRUCT = re.compile(r"(?:图|表|第|式)\s*\d+(?:\.\d+)?|[（(]\s*\d+\s*[)）]")

# 正文里扫数字时，先要遮掉的两类：行内数学 $...$、内核记号 @@...@@
_MATH = re.compile(r"\$[^$]*\$|@@[a-z_][a-z0-9_]*(?::\d+)?@@")


def claim(cid, value, unit="", grade="", source="", url="", locator="",
          uncertainty=None, recompute=None, texts=(), note="", tol=1e-9):
    """登记一条事实。

    构造时就按等级检查必填项 —— 缺了当场抛 KeyError，而不是留到闸门里变成一条警告。
    `texts`：允许出现在正文里的字面串（如 "1838 年"）。正文里的数字必须落在某个
    `texts` 里，否则 F4 报红。
    """
    if not re.fullmatch(r"[a-z][a-z0-9_]*", cid or ""):
        raise KeyError(f"claim id 必须是小写字母开头的标识符：{cid!r}")
    if grade not in GRADES:
        raise KeyError(f"claim {cid}：grade 必须是 {GRADES} 之一，现在是 {grade!r}")
    vals = {"value": value, "unit": unit, "source": source, "url": url,
            "locator": locator, "uncertainty": uncertainty, "recompute": recompute,
            "texts": list(texts), "note": note, "tol": tol}
    for fld in REQUIRED[grade]:
        v = vals.get(fld)
        if v is None or v == "" or v == []:
            raise KeyError(f"claim {cid}：等级「{grade}」必须给 {fld}")
    return {"id": cid, "grade": grade, **vals}


def _close(a, b, tol):
    try:
        return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))
    except (TypeError, ValueError):
        return a == b


def _mask(text):
    """把 $数学$ 与 @@记号@@ 换成等长空格 —— 位置不变，扫数字时不会误伤。"""
    out = list(text)
    for m in _MATH.finditer(text):
        for i in range(m.start(), m.end()):
            out[i] = " "
    return "".join(out)


def _prose_texts(node, key=None, path="章节"):
    """递归取出所有「会被读者读到」的字符串。

    跳过两类：结构字段（id/file/num/height/type），以及 `tex`（formula 块的
    公式体是**纯数学**，里面的数字是推导的一部分，不是需要出处的事实）。
    """
    if isinstance(node, str):
        if key in ("id", "file", "num", "height", "type", "tex"):
            return
        yield path, node
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _prose_texts(v, key, f"{path}[{i}]")
    elif isinstance(node, dict):
        for k, v in node.items():
            if k in ("id", "file", "num", "height", "type"):
                continue
            yield from _prose_texts(v, k, f"{path}.{k}")


class Registry:
    """一个（书 / 章）的事实登记表。"""

    def __init__(self, name=""):
        self.name = name
        self.items = {}
        self.allow = []                       # [(compiled, 理由)]

    def add(self, c):
        if c["id"] in self.items:
            raise KeyError(f"claim id 重复：{c['id']}")
        self.items[c["id"]] = c
        return c

    def allow_pattern(self, pattern, why):
        """放行一类不登记的数字。**理由必填** —— 白名单就是「已批准的不一致」。"""
        if not isinstance(why, str) or len(why.strip()) < 8:
            raise KeyError(f"白名单 {pattern!r} 必须写明理由（至少 8 字），"
                           f"否则没人知道它为什么被批准")
        self.allow.append((re.compile(pattern), why))

    def values(self):
        """给 @@记号@@ 用的 {id: 值}。"""
        return {cid: c["value"] for cid, c in self.items.items()}

    def texts(self):
        return [(c["id"], t) for c in self.items.values() for t in c["texts"]]

    # ---------------- 判据 ----------------
    def check(self, referenced=None, chapters=None):
        r = Report()
        # F1 等级必填项（构造时已挡；这里兜底防「手改 dict 绕过构造」）
        for cid, c in self.items.items():
            for fld in REQUIRED.get(c["grade"], ()):
                if not c.get(fld):
                    r.err("F1", f"claim[{cid}]",
                          f"等级「{c['grade']}」缺 {fld}", "补上该字段")
        # F2 现算级：当场重算并比对 —— 这是「不手写数字」的机器化形式
        for cid, c in self.items.items():
            if c["grade"] != "现算":
                continue
            fn = c.get("recompute")
            if not callable(fn):
                r.err("F2", f"claim[{cid}]", "现算级必须给可调用的 recompute",
                      "给一个无参函数，闸门会真的调用它")
                continue
            try:
                got = fn()
            except Exception as exc:                     # noqa: BLE001
                r.err("F2", f"claim[{cid}]", f"复算函数抛异常：{exc!r}", "修 recompute")
                continue
            if not _close(got, c["value"], c.get("tol", 1e-9)):
                r.err("F2", f"claim[{cid}]",
                      f"复算得 {got!r}，登记的是 {c['value']!r}（容差 {c.get('tol')}）",
                      "要么改登记值，要么改内核 —— 两者必须同源")
        # F3 正文引用的记号必须登记；登记的必须被引用
        if referenced is not None:
            for cid in sorted(set(referenced) - set(self.items)):
                r.err("F3", "正文", f"引用了未登记的记号 @@{cid}@@",
                      "在 facts 里登记它，或改用别处已登记的记号")
            for cid in sorted(set(self.items) - set(referenced)):
                r.warn("F3", f"claim[{cid}]", "登记了但正文从未引用（死条目）",
                       "删掉它，或在正文里引用")
        # F4 正文里的未登记数字
        if chapters is not None:
            for where, text in _prose_texts(chapters):
                for tok, ctx in self.bare_numbers(text):
                    r.err("F4", where, f"未登记的数字 {tok!r}（…{ctx}…）",
                          "改成 @@记号@@（由内核现算），或在 facts 里登记并写进它的 texts")
        return r

    def bare_numbers(self, text):
        """找出既不在 $数学$ 里、也不在 @@记号@@ 里、也不被登记/白名单覆盖的数字。

        返回 [(数字, 上下文)]。工具层的体检模式（--audit）也用它。
        """
        out = []
        masked = _mask(text)
        # 结构性编号（图 10.1 / 第 8 章 / (1)）整体跳过
        struct = [(m.start(), m.end()) for m in _STRUCT.finditer(masked)]
        covered = []
        for _cid, t in self.texts():
            for occ in re.finditer(re.escape(t), text):
                covered.append((occ.start(), occ.end()))
        for m in re.finditer(r"\d+(?:\.\d+)?", masked):
            s, e = m.start(), m.end()
            if any(a <= s and e <= b for a, b in struct):
                continue
            if any(a <= s and e <= b for a, b in covered):
                continue
            if any(p.search(text) for p, _ in self.allow):
                continue
            lo, hi = max(0, s - 10), min(len(text), e + 10)
            out.append((m.group(0), text[lo:hi].replace("\n", " ")))
        return out
