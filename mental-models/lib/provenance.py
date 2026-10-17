# -*- coding: utf-8 -*-
"""
provenance.py —— 出处审计：每个数值到底是「现算」「实测」还是「假设」。

## 为什么需要它

公式页的纪律是不手写数字（全部现算），数据页的纪律是不手写数据（全部现取）。
但这条纪律一直是**靠人记着**的：没有机器检查，也没有区分「算出来的」与「我假设的」。

`build_safety()` 里 `mu, sigma, price = 100, 15, 80` 是**假设**，不是市场数据；
`sympy` 算出来的击穿概率是**现算**。两件事在页面上长得一模一样，读者分不出来。
这份审计把它们分开，并且把「假设」逐条列出来 —— 假设本身没错，假装它是实测才错。

## 分类从结构推导，不手填

- `board.params`      → 用户可以拖的参数 = **假设**（示例值）
- `board.readouts` / `board.scalars` 里带 expr 的 → **现算**
- `DATA_SOURCES` 里登记的两个模型 → **实测**（带文件与指纹）

## 三种运行方式

    python lib/provenance.py            # 打印分类摘要
    python lib/provenance.py --write     # 重新生成 data/PROVENANCE.md
    python lib/provenance.py --check     # 闸门：报告与代码不一致 / 指纹不符 → 退出码 1

`--check` 的用途：谁往某个模型里加了一个滑块参数（= 多了一个假设），却没有
重新生成报告，闸门就会失败。假设可以被加，但不能被**默默**加。
"""

import hashlib
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE / "scripts"))
sys.path.insert(0, str(BASE / "lib"))

import generate as G                       # noqa: E402

DATA_DIR = BASE / "data"
REPORT = DATA_DIR / "PROVENANCE.md"

CLASSES = {
    "computed": "现算 —— 由 lib/models_kernel.py 按公式推出，可复现",
    "measured": "实测 —— 从带指纹的数据集读出",
    "assumed": "假设 —— 人为设定的示例参数，不是市场/现实数据",
    "authored": "手写 —— 纯文字判断，不含数值",
}

# 两个数据驱动模型。每个都有**两个**哈希，含义不同，不能混：
#   · upstream（csvSha256 / contentSha256）—— 抓取时校验上游原始数据；
#   · localSha256                          —— 本地蒸馏文件的 sha256，审计每次核对。
# 一开始就是把这两个搞混了：拿上游哈希去比蒸馏文件，必然"不符"。
DATA_SOURCES = {
    "divergence": {
        "file": "maddison-gdp-per-capita.csv",
        "meta": "maddison-source.json",
        "upstream_key": "csvSha256",
        "upstream_desc": "上游 OWID 原始 CSV（下载时校验）",
        "cite": "Bolt & van Zanden，Maddison Project Database 2023（OWID 轻度加工）",
        "license": "学术引用（见 data/SOURCES.md）",
    },
    "tailexpo": {
        "file": "usgs-quakes.csv",
        "meta": "usgs-quake-source.json",
        "upstream_key": "contentSha256",
        "upstream_desc": "上游 USGS 原始 CSV 解析后规范化的内容指纹（抓取时校验）",
        "cite": "USGS ComCat 地震目录（M≥6.0，1900–2024）",
        "license": "U.S. public domain",
    },
}


# ---------------------------------------------------------------- 分类

def classify(model_id, data):
    """从页面结构推出每个数值的出处类别。"""
    board = data.get("board") or {}
    assumed = []
    for p in board.get("params") or []:
        assumed.append(p.get("label") or p.get("name") or "?")

    computed = []
    for s in board.get("scalars") or []:
        computed.append(s.get("name") or "?")
    for r in board.get("readouts") or []:
        if r.get("expr") is not None:
            computed.append(r.get("label") or r.get("id") or "?")

    measured = []
    if model_id in DATA_SOURCES:
        measured.append(DATA_SOURCES[model_id]["cite"])

    return {"assumed": assumed, "computed": computed, "measured": measured}


# ---------------------------------------------------------------- 指纹

def _sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_source(model_id):
    """返回 (ok, 说明)。ok=False 时说明是问题所在。"""
    src = DATA_SOURCES[model_id]
    fp = DATA_DIR / src["file"]
    mp = DATA_DIR / src["meta"]
    if not fp.exists():
        return False, f"缺数据文件 {src['file']}"
    if not mp.exists():
        return False, f"缺出处元数据 {src['meta']}"
    meta = json.loads(mp.read_text(encoding="utf-8"))
    want = meta.get("localSha256")
    if not want:
        return False, f"{src['meta']} 里没有 localSha256（本地文件指纹）"
    got = _sha256_file(fp)
    if got != want:
        return False, (f"{src['file']} 的本地指纹不符：期望 {want[:16]}…，实得 {got[:16]}…"
                       f"（本地数据被改过却没有同步 meta）")
    note = f"local {want[:12]}… 通过"
    if meta.get(src["upstream_key"]):
        note += f"；上游 {meta[src['upstream_key']][:12]}…"
    return True, note


# ---------------------------------------------------------------- 报告

def build_models():
    return {mid: fn() for mid, fn in sorted(G.REGISTRY.items())}


def report(models):
    """生成 Markdown 报告（纯函数：同样的 models 永远得到同样的文本）。"""
    rows = []
    problems = []
    for mid in sorted(models):
        cls = classify(mid, models[mid])
        if mid in DATA_SOURCES:
            ok, note = verify_source(mid)
            if not ok:
                problems.append(f"{mid}: {note}")
        else:
            note = "—"
        n_a, n_c = len(cls["assumed"]), len(cls["computed"])
        n_m = 1 if cls["measured"] else 0
        kind = "、".join(k for k, n in
                         (("实测", n_m), ("现算", n_c), ("假设", n_a)) if n) or "无数值"
        rows.append((mid, kind, n_c, n_a, n_m, note,
                     "；".join(cls["assumed"]) if cls["assumed"] else "—"))

    out = []
    out.append("# 数值出处分级（自动生成，勿手改）")
    out.append("")
    out.append("> 本文件由 `lib/provenance.py --write` 生成。`--check` 会逐行比对：")
    out.append("> 谁新增了一个滑块参数（= 多了一个**假设**）却没重新生成，闸门就失败。")
    out.append("> 假设可以被加，但不能被默默加。")
    out.append("")
    out.append("## 四类出处")
    out.append("")
    out.append("| 类别 | 含义 |")
    out.append("|---|---|")
    for k, v in CLASSES.items():
        out.append(f"| `{k}` | {v} |")
    out.append("")
    out.append("## 逐模型")
    out.append("")
    out.append("| 模型 | 含 | 现算 | 假设 | 实测 | 指纹核对 | 假设的参数 |")
    out.append("|---|---|---:|---:|---:|---|---|")
    for mid, kind, n_c, n_a, n_m, note, assumed in rows:
        out.append(f"| `{mid}` | {kind} | {n_c} | {n_a} | {n_m} | {note} | {assumed} |")
    out.append("")
    out.append("## 数据集")
    out.append("")
    for mid, src in DATA_SOURCES.items():
        out.append(f"### `{mid}`")
        out.append("")
        out.append(f"- 文件：`data/{src['file']}`")
        out.append(f"- 出处：{src['cite']}")
        out.append(f"- 许可：{src['license']}")
        out.append(f"- 本地指纹：`localSha256`（原始字节 sha256，审计每次核对）")
        out.append(f"- 上游指纹：`{src['upstream_key']}` —— {src['upstream_desc']}")
        out.append("")
        out.append("  > 两个哈希覆盖的是**不同的文件**：上游哈希盖的是抓取时的原始数据，")
        out.append("  > 本地哈希盖的是入库的蒸馏文件。拿上游哈希去比本地文件，必然不符。")
        out.append("")
    if problems:
        out.append("## 发现的问题")
        out.append("")
        for p in problems:
            out.append(f"- {p}")
        out.append("")
    return "\n".join(out), problems


def main(argv):
    models = build_models()
    text, problems = report(models)

    if "--write" in argv:
        REPORT.write_text(text, encoding="utf-8", newline="\n")
        print(f"已写入 {REPORT}")
        if problems:
            for p in problems:
                print("  ✗", p)
            return 1
        return 0

    if "--check" in argv:
        if not REPORT.exists():
            print(f"✗ 缺 {REPORT.name}，先运行 --write")
            return 1
        old = REPORT.read_text(encoding="utf-8")
        if old.replace("\r\n", "\n") != text:
            print("✗ 出处报告与代码不一致：有模型的参数/读数变了但报告没重新生成")
            print("  修法：python lib/provenance.py --write")
            return 1
        if problems:
            for p in problems:
                print("✗", p)
            return 1
        print(f"✓ 出处分级与代码一致；{len(models)} 个模型，"
              f"{len(DATA_SOURCES)} 个数据集指纹通过")
        return 0

    # 摘要
    for mid in sorted(models):
        cls = classify(mid, models[mid])
        bits = [f"现算 {len(cls['computed'])}"]
        if cls["assumed"]:
            bits.append(f"假设 {len(cls['assumed'])}")
        if cls["measured"]:
            bits.append("实测 1")
        print(f"  {mid:14s} " + "，".join(bits))
    if problems:
        print()
        for p in problems:
            print("  ✗", p)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
