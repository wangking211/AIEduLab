# -*- coding: utf-8 -*-
"""
check_facts.py — 事实核查闸门（退出码可入 CI）。

    python tools/check_facts.py --selftest        # 负向测试：每条判据都必须能红
    python tools/check_facts.py                   # 核查所有带 facts.py 的书稿
    python tools/check_facts.py --audit <书目录>   # 只体检（不判红）：看某本书离标准还有多远

为什么要有这条闸门
------------------
「不手写数字」在本项目里已经喊了很久，但此前只对**图形**成立（figures.py 现算）。
正文里的年份、尺度、比例仍然可以手写，而且写错了没人管 —— 这类书最危险的失败模式
恰恰是「数字看着精确、来源经不起追问」。这条闸门把正文也纳入同一套纪律：
数字要么来自内核（@@记号@@），要么是登记在案的事实（带等级与出处）。

未接入的书稿会被**点名**（而不是静默跳过）—— 静默跳过正是「闸门空转」的温床。
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "shared"))

import factreg as F                                    # noqa: E402
from bookbuild import load_book_module                  # noqa: E402

TOKEN = re.compile(r"@@([a-z_][a-z0-9_]*)(?::\d+)?@@")


def load_registry(path):
    """加载一本书的 facts.py，取它导出的 REGISTRY。

    走 bookbuild 的加载器（而不是自己 importlib）：插图也用同一个加载器，
    两边才会拿到**同一个模块实例**与同一个 Registry —— F3 的「被读过」才成立。
    """
    mod = load_book_module(path.parent, "facts")
    reg = getattr(mod, "REGISTRY", None) if mod else None
    if not isinstance(reg, F.Registry):
        raise SystemExit(f"{path}：必须导出 REGISTRY = Registry(...)")
    return reg


def referenced_tokens(book, enrolled=None):
    """正文里实际用到的 @@记号@@ 集合。

    `enrolled` 不为 None 时只扫接入的章节 —— 否则其它章节的记号会被报成
    「引用了未登记的记号」，而它们本来就没打算（也没能力）在这一轮登记。
    """
    used = set()
    for p in sorted((book / "chapters").glob("*.json")):
        txt = p.read_text(encoding="utf-8-sig")
        if enrolled is not None:
            cid = json.loads(txt).get("id") or p.stem
            if cid not in enrolled:
                continue
        used |= {m.group(1) for m in TOKEN.finditer(txt)}
    return used


def chapter_blobs(book):
    """章节 JSON 的集合，按**章 id** 作键（F4 按章接入时要用它筛）。"""
    out = {}
    for p in sorted((book / "chapters").glob("*.json")):
        data = json.loads(p.read_text(encoding="utf-8-sig"))
        out[data.get("id") or p.stem] = data
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="负向测试：每条判据都要能红")
    ap.add_argument("--audit", metavar="BOOK", help="只体检某本书（不判红）")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    if args.audit:
        book = Path(args.audit)
        reg = F.Registry("audit")
        for _where, text in F._prose_texts(chapter_blobs(book)):
            for tok, ctx in reg.bare_numbers(text):
                print(f"  未登记：{tok!r}  …{ctx}…")
        return 0

    books = [d for d in sorted((ROOT / "books").iterdir()) if (d / "facts.py").exists()]
    if not books:
        print("未接入任何书稿：没有一本书带 facts.py ——")
        print("  这条闸门当前只在 --selftest 下被验证过，**不等于**书稿已被核查。")
        print("  （新书从第一章起就要求有 facts.py；旧书接入前，它的正文数字无人看守。）")
        return 0

    bad = 0
    for book in books:
        reg = load_registry(book / "facts.py")
        # 让插图真的跑一遍：谁被读过，谁就算「在用」（F3 的死条目判据靠这个）
        figs_mod = load_book_module(book, "figures")
        if figs_mod is not None:
            try:
                figs_mod.build()
            except Exception as exc:                    # noqa: BLE001
                print(f"  （{book.name}：插图构建失败，F3 只用正文引用判定：{exc!r}）")
        blobs = chapter_blobs(book)
        # 正文里的记号有两个来源：事实登记表，和插图现算的 PROSE —— 后者不算「未登记」
        fig_tokens = set()
        if figs_mod is not None and hasattr(figs_mod, "prose_values"):
            bk = json.loads((book / "book.json").read_text(encoding="utf-8-sig"))
            for ch in bk.get("chapters", []):
                if reg.enrolled is not None and ch.get("id") not in reg.enrolled:
                    continue
                try:
                    fig_tokens |= set(figs_mod.prose_values(ch.get("figs", [])))
                except Exception:                       # noqa: BLE001
                    pass
        rep = reg.check(referenced=referenced_tokens(book, reg.enrolled),
                        chapters=blobs, also_ok=fig_tokens)
        tag = "OK  " if rep.ok else "FAIL"
        if reg.enrolled is None:
            scope = f"全书 {len(blobs)} 章"
        else:
            missing = sorted(set(blobs) - set(reg.enrolled))
            scope = f"接入 {len(set(blobs) & set(reg.enrolled))}/{len(blobs)} 章"
            if missing:
                scope += f"（未接入：{', '.join(missing)}）"
        print(f"[{tag}] {book.name:20s} 登记 {len(reg.items)} 条 · {scope}  "
              f"错误 {len(rep.errors)}  警告 {len(rep.warnings)}")
        if rep.errors or rep.warnings:
            for line in rep.format().splitlines():
                print("       " + line)
        bad += len(rep.errors)
    print(f"\n合计：{len(books)} 本书，{bad} 个错误")
    return 1 if bad else 0


# =====================================================================
# 负向测试：每条判据都要能红（否则闸门就是摆设）
# =====================================================================
def selftest():
    cases = []

    def case(name, fn, want):
        try:
            rep = fn()
            got = {e["code"] for e in rep.errors}
        except KeyError as exc:                      # 构造期就挡住了 —— 也算通过
            got = {"KeyError"}
            name = name + f"（构造期拦截：{str(exc)[:40]}）"
        cases.append((want in got, name, want, sorted(got)))

    def _reg(**kw):
        r = F.Registry("t")
        r.add(F.claim("ok_one", 1.0, grade="现算", recompute=lambda: 1.0))
        return r

    # F1 等级必填项：手改 dict 绕过构造 → 闸门必须兜住
    def f1():
        r = _reg()
        c = r.items["ok_one"]
        c["recompute"] = None
        return r.check()
    case("现算级缺 recompute", f1, "F1")

    # F2 现算级复算不符（这是「不手写数字」的机器化形式）
    def f2():
        r = F.Registry("t")
        r.add(F.claim("wrong", 3.14, grade="现算", recompute=lambda: 3.14159))
        return r.check()
    case("现算值与复算不符", f2, "F2")

    # F2 复算函数抛异常也必须红（不能因为「跑不起来」就当通过）
    def f2b():
        r = F.Registry("t")
        r.add(F.claim("boom", 1.0, grade="现算", recompute=lambda: 1 / 0))
        return r.check()
    case("复算函数抛异常", f2b, "F2")

    # F3 正文引用了未登记的记号
    def f3():
        r = _reg()
        return r.check(referenced={"ok_one", "never_registered"})
    case("正文引用未登记记号", f3, "F3")

    # F3 死条目：登记了但正文与插图都没读 —— 必须出**警告**（不是错误）
    def f3_dead():
        r = F.Registry("t")
        r.add(F.claim("orphan", 1.0, grade="现算", recompute=lambda: 1.0))
        return r.check(referenced=set())
    rep_dead = f3_dead()
    cases.append((any(w["code"] == "F3" for w in rep_dead.warnings),
                  "死条目必须出 F3 警告", "F3(warn)",
                  sorted(w["code"] for w in rep_dead.warnings)))

    # 反向：被插图真读过（items[...]）的登记，不许再报死条目
    def f3_accessed():
        r = F.Registry("t")
        r.add(F.claim("used", 1.0, grade="现算", recompute=lambda: 1.0))
        _ = r.items["used"]["value"]          # 模拟插图读取
        return r.check(referenced=set())
    rep_acc = f3_accessed()
    cases.append((not any(w["code"] == "F3" for w in rep_acc.warnings),
                  "被读过的登记不算死条目", "无 F3(warn)",
                  sorted(w["code"] for w in rep_acc.warnings)))
    # F4 正文里有未登记的数字（含年份 —— 年份也是事实）
    def f4():
        r = _reg()
        return r.check(chapters={"blocks": [
            {"type": "p", "text": "宇宙年龄 138 亿年，这个式子 1838 年就有了。"}]})
    case("正文出现未登记数字", f4, "F4")

    # 构造期必填项：缺出处/不确定度必须当场抛错
    case("实测级缺出处", lambda: F.claim("x", 1.0, grade="实测"),
         "KeyError")
    case("白名单没写理由", lambda: F.Registry("t").allow_pattern(r"\d+", "x"),
         "KeyError")

    # 对照组：一份干净的登记 + 覆盖住的正文，必须**零错误零警告**
    def clean():
        r = F.Registry("t")
        r.add(F.claim("age", 13.797, "亿年", grade="实测",
                      source="Planck 2018 结果 VI 表 2",
                      url="https://doi.org/10.1051/0004-6361/201833910",
                      uncertainty=0.023, texts=["138 亿年"]))
        r.add(F.claim("light_year", 9.4607304725808e15, "米", grade="现算",
                      recompute=lambda: 299792458.0 * 365.25 * 86400.0))
        return r.check(referenced={"age", "light_year"},
                       chapters={"blocks": [
                           {"type": "p", "text": "宇宙年龄 138 亿年，见 @@age@@。"},
                           {"type": "p", "text": "光年是长度：$1$ 光年 = @@light_year@@ 米。"},
                           {"type": "p", "text": "第 8 章讲过；图 10.1 是蛛网图；两点：(1) 与 (2)。"}]})
    rep_clean = clean()
    cases.append((rep_clean.ok and not rep_clean.warnings and not rep_clean.unread,
                  "干净的登记必须全绿（含 0 警告）", "ok", rep_clean.format()[:60]))

    bad = [c for c in cases if not c[0]]
    for ok, name, want, got in cases:
        print(f"  {'✓' if ok else '✗'} {name:32s} 期望 {want:8s} 实得 {got}")
    print(f"\n{'事实核查闸门自测通过 ✓' if not bad else f'{len(bad)} 项失败'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
