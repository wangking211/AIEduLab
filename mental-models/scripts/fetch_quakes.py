# -*- coding: utf-8 -*-
"""fetch_quakes.py —— 取「尾部：少数事件支配总量」页所需的数据。

与 fetch_maddison.py 同一套纪律，但有一处关键差别：

  USGS 的 API 是**动态生成**响应的（两次请求的字节不同），所以 sha256 对原始响应
  没有意义。这里改用**内容指纹**：把解析后的 (年, 震级) 规范化成文本再取哈希。
  它锚定的是「数据集内容」，而不是「某次 HTTP 传输的字节」——这才是我们真正要保的东西。

另：USGS 只提供 1969 年以后的全球数字目录（即便请求从 1900 年开始）。
脚本会**如实记录实际覆盖范围**，绝不声称更早。

用法：
    python scripts/fetch_quakes.py
    python scripts/fetch_quakes.py --accept-new-fingerprint
"""

import csv
import hashlib
import io
import json
import pathlib
import sys
import urllib.parse
import urllib.request

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
OUT_CSV = SKILL_DIR / "data" / "usgs-quakes.csv"
OUT_META = SKILL_DIR / "data" / "usgs-quake-source.json"

API = "https://earthquake.usgs.gov/fdsnws/event/1/query"
PARAMS = {
    "format": "csv",
    "starttime": "1900-01-01",     # 请求全部；服务端实际只回 1969 年以后
    "endtime": "2024-12-31",
    "minmagnitude": "6.0",
}
MIN_MAG = 6.0

# 2026-10-16 抓取时的内容指纹（规范化 (年, 震级) → sha256）
CONTENT_SHA256 = "f581277f54b0ace100332a822f46699f165b4aa24756a6a01e2f37e22e7de262"


def fetch():
    url = API + "?" + urllib.parse.urlencode(PARAMS)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (AIEduLab)"})
    with urllib.request.urlopen(req, timeout=300) as r:
        return url, r.read()


def parse(raw):
    rows = []
    with io.StringIO(raw.decode("utf-8")) as f:
        for r in csv.DictReader(f):
            if r.get("type") != "earthquake" or not r.get("mag"):
                continue
            try:
                y, m = int(r["time"][:4]), float(r["mag"])
            except (ValueError, TypeError):
                continue
            if m >= MIN_MAG:
                rows.append((y, m))
    rows.sort()
    return rows


def fingerprint(rows):
    blob = "\n".join(f"{y},{m:.4f}" for y, m in rows).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def main(argv):
    accept = "--accept-new-fingerprint" in argv
    url, raw = fetch()
    rows = parse(raw)
    fp = fingerprint(rows)
    if fp != CONTENT_SHA256 and not accept:
        print(f"\n数据集内容变了，拒绝继续：\n  期望 {CONTENT_SHA256}\n  实得 {fp}")
        print("请先人工核对差异（新增/修订了哪些事件），再 --accept-new-fingerprint 重新锁定。")
        return 1
    if fp != CONTENT_SHA256:
        print(f"⚠ 指纹已更新为 {fp}（请同步改写本文件的 CONTENT_SHA256 常量）")
    else:
        print(f"内容指纹校验通过：{fp}")

    ys = [y for y, _ in rows]
    mags = [m for _, m in rows]
    print(f"事件 {len(rows)} 条，实际覆盖 {min(ys)}–{max(ys)}，震级 {min(mags):g}–{max(mags):g}")

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with io.open(OUT_CSV, "w", encoding="utf-8", newline="\n") as f:
        f.write("year,magnitude\n")
        for y, m in rows:
            f.write(f"{y},{m:g}\n")
    print(f"写出 {OUT_CSV.relative_to(SKILL_DIR)}")

    # 本地蒸馏文件的指纹：与 contentSha256（上游原始 CSV 解析后的规范化指纹）
    # 盖的不是同一个东西。审计核的是这一条。
    local_digest = hashlib.sha256(OUT_CSV.read_bytes()).hexdigest()

    meta = {
        "title": "Earthquake catalog (ANSS Comprehensive Catalog, ComCat)",
        "source": "U.S. Geological Survey (USGS) Earthquake Hazards Program",
        "queryUrl": url,
        "params": PARAMS,
        "minMagnitude": MIN_MAG,
        "requestedStart": PARAMS["starttime"],
        "actualCoverage": f"{min(ys)}-{max(ys)}",
        "actualStartNote": "USGS 默认目录不含 1969 年以前的全球数字化记录；请求 1900 年起的目的是"
                           "让服务端回传它所拥有的全部数据，脚本如实记录实际起点。",
        "eventCount": len(rows),
        "contentSha256": fp,
        "localFile": OUT_CSV.name,
        "localSha256": local_digest,
        "dateDownloaded": "2026-10-16",
        "license": "U.S. public domain（USGS 官方说明：USGS-authored or produced data and "
                   "information are considered to be in the U.S. public domain）",
        "creditsUrl": "https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits",
    }
    OUT_META.write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"写出 {OUT_META.relative_to(SKILL_DIR)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
