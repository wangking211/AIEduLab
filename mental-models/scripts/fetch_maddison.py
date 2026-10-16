# -*- coding: utf-8 -*-
"""fetch_maddison.py —— 取「大分叉」页所需的数据，并蒸馏成仓库内的单一数据源。

设计要点（这是本项目唯一一个「数据驱动」而非「公式驱动」的模型，纪律更严）：

  1. 数据不手写。全部来自公开数据集，脚本可重跑。
  2. 原始下载件做 **sha256 校验**：源站一旦更新，脚本会大声失败，
     逼人重新核对，而不是悄悄换掉数字。
  3. 蒸馏结果落成 `data/maddison-gdp-per-capita.csv`，
     内核（算）与网页（画）都只读这一个文件 —— 单一数据源。
  4. 出处、单位、许可、必须有归属要求的原始论文，一并写进 data/SOURCES.md。

用法：
    python scripts/fetch_maddison.py                 # 下载 → 校验 → 蒸馏
    python scripts/fetch_maddison.py --raw <path>    # 用已下载的原始 CSV
    python scripts/fetch_maddison.py --accept-new-hash   # 源站更新后重新锁定指纹
"""

import csv
import hashlib
import io
import json
import pathlib
import sys
import urllib.request

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
OUT_CSV = SKILL_DIR / "data" / "maddison-gdp-per-capita.csv"
OUT_META = SKILL_DIR / "data" / "maddison-source.json"

CSV_URL = "https://ourworldindata.org/grapher/gdp-per-capita-maddison-project-database.csv"
META_URL = "https://ourworldindata.org/grapher/gdp-per-capita-maddison-project-database.metadata.json"

# 2026-10-16 抓取时的指纹。源站更新后必须 --accept-new-hash 显式重新锁定。
CSV_SHA256 = "0545ad6ca37529206af49f9f964f17af927e8c154c1fe8d3813c523e0d2f43f8"

# 只保留这几条长序列。选它们的理由：覆盖「西方最早起飞 / 北美 / 东亚 / 南亚」四类。
# （注意：这是 <12 国的图形化子集 → 触发 MPD 的「须引用原始论文」条款，见 SOURCES.md）
ENTITIES = [
    ("United Kingdom", "英国", "UK"),
    ("France", "法国", "FR"),
    ("United States", "美国", "US"),
    ("Japan", "日本", "JP"),
    ("China", "中国", "CN"),
    ("India", "印度", "IN"),
]


def fetch(url, timeout=180):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AIEduLab)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def main(argv):
    raw_path = None
    accept_new = "--accept-new-hash" in argv
    if "--raw" in argv:
        raw_path = pathlib.Path(argv[argv.index("--raw") + 1])

    if raw_path:
        raw = raw_path.read_bytes()
        print(f"用本地原始件：{raw_path}")
    else:
        print(f"下载：{CSV_URL}")
        raw = fetch(CSV_URL)

    digest = hashlib.sha256(raw).hexdigest()
    if digest != CSV_SHA256 and not accept_new:
        print(f"\n源站指纹变了，拒绝继续：\n  期望 {CSV_SHA256}\n  实得 {digest}")
        print("请先人工核对差异（哪些国家/年份变了），再 --accept-new-hash 重新锁定。")
        return 1
    if digest != CSV_SHA256:
        print(f"⚠ 指纹已更新为 {digest}（请同步改写本文件的 CSV_SHA256 常量）")
    else:
        print(f"sha256 校验通过：{digest}")

    with io.StringIO(raw.decode("utf-8")) as f:
        r = csv.reader(f)
        head = next(r)
        rows = list(r)
    assert head[:4] == ["Entity", "Code", "Year", "GDP per capita"], f"表头变了：{head}"

    want = {e for e, _, _ in ENTITIES}
    series = {e: [] for e in want}
    for ent, _code, year, val, _ann in rows:
        if ent in want and val != "":
            series[ent].append((int(year), float(val)))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with io.open(OUT_CSV, "w", encoding="utf-8", newline="\n") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["entity", "entity_zh", "year", "gdp_pc_2011intl"])
        for ent, zh, _code in ENTITIES:
            for y, v in sorted(series[ent]):
                w.writerow([ent, zh, y, f"{v:g}"])

    total = sum(len(v) for v in series.values())
    print(f"写出 {OUT_CSV.relative_to(SKILL_DIR)}：{total} 行")
    for ent, zh, _code in ENTITIES:
        ys = [y for y, _ in series[ent]]
        print(f"  {zh:4s} {ent:16s} {ys[0]:>5}–{ys[-1]:<5} {len(ys):>4} 点")

    meta = json.loads(fetch(META_URL).decode("utf-8"))
    col = meta["columns"]["GDP per capita"]
    slim = {
        "title": meta["chart"]["title"],
        "unit": col["unit"],
        "shortUnit": col["shortUnit"],
        "timespan": col["timespan"],
        "citationShort": col["citationShort"],
        "citationLong": col["citationLong"],
        "originalChartUrl": meta["chart"]["originalChartUrl"],
        "owidVariableId": col["owidVariableId"],
        "lastUpdated": col["lastUpdated"],
        "dateDownloaded": meta["dateDownloaded"],
        "csvUrl": CSV_URL,
        "csvSha256": digest,
        "note": meta["chart"]["note"],
    }
    OUT_META.write_text(json.dumps(slim, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"写出 {OUT_META.relative_to(SKILL_DIR)}（单位：{col['unit']}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
