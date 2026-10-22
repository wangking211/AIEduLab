# -*- coding: utf-8 -*-
"""mental-models 用到的外部数据集：出处 / 许可 / 指纹。

由 `edulab/tools/check_licenses.py` 强制：
  · 许可判定（保留权利 / 非商用 → 不得随书分发；需署名 → attribution 必填）
  · 本地指纹（登记的 sha256 必须等于磁盘上那个文件的真实 sha256，每次真算）

数据文件本身与出处细节另见 `data/SOURCES.md`（人读）与 `data/*-source.json`（抓取时写的原始元数据）。
"""
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "edulab" / "shared"))

from datasets import Registry, dataset              # noqa: E402

REGISTRY = Registry("mental-models")

REGISTRY.add(dataset(
    "maddison_gdp",
    "人均 GDP（长期序列，2011 年国际元）",
    url="https://ourworldindata.org/grapher/gdp-per-capita-maddison-project-database",
    license="CC BY 4.0",
    license_url="https://creativecommons.org/licenses/by/4.0/",
    attribution="Bolt and van Zanden – Maddison Project Database 2023 – "
                "with minor processing by Our World in Data",
    downloaded="2026-10-16",
    local_file="data/maddison-gdp-per-capita.csv",
    local_sha256="69e2b7295a39789f6b8a6014dff79d11f70913977aec76b7cc5e9fe9bd7dd783",
    upstream_sha256="0545ad6ca37529206af49f9f964f17af927e8c154c1fe8d3813c523e0d2f43f8",
    unit="international-$ (2011)",
    note="本地文件是蒸馏后的子集；上游哈希盖的是抓取时的原始 CSV —— 两个哈希覆盖不同的文件，"
         "不许互相顶替。",
))

REGISTRY.add(dataset(
    "usgs_quakes",
    "USGS 地震目录（M≥6.0，1900–2024）",
    url="https://earthquake.usgs.gov/data/comcat/",
    license="US public domain",
    license_url="https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits",
    downloaded="2026-10-16",
    local_file="data/usgs-quakes.csv",
    local_sha256="b196bd14675f553d208c0e3a4c49932a88fce3efadf917edc60ad38c6cc81e23",
    upstream_sha256="f581277f54b0ace100332a822f46699f165b4aa24756a6a01e2f37e22e7de262",
    unit="震级 M",
    note="USGS 官方说明其数据属美国公有领域，可自由使用无需许可；官方仍请注明 credit: USGS。"
         "上游指纹是「原始 CSV 解析出 (年, 震级) 后规范化」的 sha256（见 data/usgs-quake-source.json "
         "的 hashScope）—— 与本地蒸馏文件的 sha256 覆盖不同对象，不许互相顶替。",
))
