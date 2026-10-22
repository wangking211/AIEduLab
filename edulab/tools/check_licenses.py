# -*- coding: utf-8 -*-
"""
check_licenses.py — 外部数据集的出处 / 许可 / 指纹闸门（退出码可入 CI）。

    python tools/check_licenses.py --selftest     # 负向测试：每条判据都要能红
    python tools/check_licenses.py                # 核查所有带 datasets.py 的产品

为什么要有这条闸门
------------------
「复用一个数据集」要过三关：出处、许可、指纹。以前前两关写在散文里靠人记得，
第三关只在个别产品里做。于是新数据进来时没人被强制问一句：
**它的许可允许随书分发吗？** —— 而「无 license」默认是保留权利，搬了就是侵权。

这条闸门把三关变成登记项 + 判据，其中指纹是**每次真算**的：
登记的 sha256 必须等于磁盘上那个文件的 sha256。文件被换过、登记写错、来源不明，
都会在这里现形。
"""
import argparse
import importlib.util
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "shared"))

import datasets as D                                 # noqa: E402


def product_dirs():
    """所有可能带 datasets.py 的产品：书、技能、根级独立产品。"""
    out = []
    out += sorted(p for p in (ROOT / "books").iterdir() if p.is_dir())
    out += sorted(p for p in (ROOT / "skills").iterdir() if p.is_dir())
    out += [ROOT.parent / "mental-models"]
    return [p for p in out if (p / "datasets.py").exists()]


def load_registry(path):
    spec = importlib.util.spec_from_file_location(f"ds_{path.parent.name}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    reg = getattr(mod, "REGISTRY", None)
    if not isinstance(reg, D.Registry):
        raise SystemExit(f"{path}：必须导出 REGISTRY = Registry(...)")
    return reg


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true", help="负向测试：每条判据都要能红")
    args = ap.parse_args(argv)
    if args.selftest:
        return selftest()

    prods = product_dirs()
    if not prods:
        print("未接入任何产品：没有一处带 datasets.py ——")
        print("  这条闸门当前只在 --selftest 下被验证过，**不等于**数据许可已被核查。")
        return 0

    bad = 0
    for prod in prods:
        reg = load_registry(prod / "datasets.py")
        rep = reg.check(base_dir=prod)
        tag = "OK  " if rep.ok else "FAIL"
        ndis = sum(1 for d in reg.items.values() if d["redistributable"])
        print(f"[{tag}] {prod.name:22s} 数据集 {len(reg.items)} 个（可分发 {ndis}）  "
              f"错误 {len(rep.errors)}  警告 {len(rep.warnings)}")
        if rep.errors or rep.warnings:
            for line in rep.format().splitlines():
                print("       " + line)
        bad += len(rep.errors)
    print(f"\n合计：{len(prods)} 个产品，{bad} 个错误")
    return 1 if bad else 0


# =====================================================================
# 负向测试：每条判据都要能红（否则闸门就是摆设）
# =====================================================================
def selftest():
    cases = []

    def case(name, fn, want):
        try:
            got = fn()
        except KeyError as exc:                      # 构造期就挡住了 —— 也算通过
            got = "KeyError"
            name = name + f"（构造期拦截：{str(exc)[:38]}）"
        cases.append((want in got, name, want, got))

    tmp = Path(tempfile.mkdtemp(prefix="lic_"))
    real = tmp / "data.csv"
    real.write_text("a,b\n1,2\n", encoding="utf-8")
    good_hash = D.sha256_of(real)

    def base(**kw):
        d = dict(did="ds_one", title="示例数据", url="https://example.org/x.csv",
                 license="CC BY 4.0", license_url="https://creativecommons.org/licenses/by/4.0/",
                 attribution="Example Project 2026", downloaded="2026-10-23",
                 local_file="data.csv", local_sha256=good_hash)
        d.update(kw)
        return d

    # 构造期：保留权利却标可分发
    case("无许可却标可分发",
         lambda: D.dataset(**base(license="NOASSERTION", redistributable=True)), "KeyError")
    # 构造期：需署名的许可却没给 attribution
    case("CC BY 缺 attribution", lambda: D.dataset(**base(attribution="")), "KeyError")
    # 构造期：必填项缺失
    case("缺 url", lambda: D.dataset(**base(url="")), "KeyError")
    # 构造期：指纹不是 64 位十六进制
    case("指纹格式错", lambda: D.dataset(**base(local_sha256="abc")), "KeyError")

    # L1 手改 dict 绕过构造 → 闸门必须兜住
    def l1():
        r = D.Registry("t")
        d = D.dataset(**base(license="US public domain", attribution=""))
        d["redistributable"] = True
        d["license"] = "NOASSERTION"
        r.add(d)
        return {e["code"] for e in r.check(base_dir=tmp).errors}
    case("绕过构造标可分发", l1, "L1")

    # L2 指纹不符（文件被换过 / 登记写错）
    def l2():
        r = D.Registry("t")
        r.add(D.dataset(**base(local_sha256="0" * 64)))
        return {e["code"] for e in r.check(base_dir=tmp).errors}
    case("指纹不符", l2, "L2")

    # L2 文件不存在
    def l2b():
        r = D.Registry("t")
        r.add(D.dataset(**base(local_file="nope.csv")))
        return {e["code"] for e in r.check(base_dir=tmp).errors}
    case("本地文件不存在", l2b, "L2")

    # L3 上游指纹格式
    def l3():
        r = D.Registry("t")
        r.add(D.dataset(**base(upstream_sha256="zz")))
        return {e["code"] for e in r.check(base_dir=tmp).errors}
    case("上游指纹格式错", l3, "L3")

    # 非商用许可：不报错，但必须被判为「不可分发」（这是策略，不是错误）
    d_nc = D.dataset(**base(did="nc", license="CC BY-NC-SA 4.0", attribution="X", license_url=""))
    cases.append((d_nc["redistributable"] is False and "非商用" in d_nc["policy"],
                  "NC 许可判为不可分发", "redistributable=False",
                  f"redistributable={d_nc['redistributable']}"))

    # 对照组：干净的登记 + 真实指纹，必须零错误零警告
    r_clean = D.Registry("t")
    r_clean.add(D.dataset(**base()))
    rep = r_clean.check(base_dir=tmp)
    cases.append((rep.ok and not rep.warnings and not rep.unread,
                  "干净的登记必须全绿（含 0 警告）", "ok", rep.format()[:60]))

    bad = [c for c in cases if not c[0]]
    for ok, name, want, got in cases:
        print(f"  {'✓' if ok else '✗'} {name:34s} 期望 {want:8s} 实得 {got}")
    print(f"\n{'数据许可闸门自测通过 ✓' if not bad else f'{len(bad)} 项失败'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
