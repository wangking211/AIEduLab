# -*- coding: utf-8 -*-
"""datasets.py — 外部数据集的出处 / 许可 / 指纹登记。

为什么要有它
------------
「复用一个数据集」在本项目里已经是允许的，但它必须过三关：**出处、许可、指纹**。
前两关以前只写在 `SOURCES.md` 这类散文里，靠人记得；第三关（指纹）只在个别产品里做。
结果是：一个新数据集进来时，没人被强制问「它的许可能不能随书分发」——
而**无 license 默认是保留权利**（`NOASSERTION` 同理），搬了就是侵权。

本模块把三关变成**登记项 + 判据**：

    许可判定  空 / NOASSERTION / 未知  → 视为保留权利，redistributable 必须为 False
              含 NC（非商用）/ ND（禁改） → 不得随书分发
              需署名的许可（CC BY* / ODbL / MIT / Apache / BSD）→ attribution 必填
    指纹      local_sha256 必须与**磁盘上那个文件的真实 sha256** 一致（闸门每次真算）

设计约束
--------
· 构造期就拦：`dataset(...)` 缺必填项、或「保留权利却标了可分发」当场抛错。
· 许可判定用**白名单式**：只认明确列出的许可；认不出的一律按「保留权利」处理，
  宁可保守 —— 判错的代价是侵权，不是麻烦。
· 上游哈希与本地哈希覆盖的是**不同的文件**（抓取时的原始数据 vs 入库的蒸馏文件），
  两者都要留，且不许互相顶替。

用法
----
    from datasets import Registry, dataset

    REGISTRY = Registry("mental-models")
    REGISTRY.add(dataset(
        "maddison_gdp", "人均 GDP（长期序列）",
        url="https://ourworldindata.org/grapher/gdp-per-capita-maddison-project-database",
        license="CC BY 4.0",
        license_url="https://creativecommons.org/licenses/by/4.0/",
        attribution="Bolt and van Zanden – Maddison Project Database 2023 – with minor processing by Our World in Data",
        downloaded="2026-10-16",
        local_file="data/maddison-gdp-per-capita.csv",
        local_sha256="69e2b7295a39789f6b8a6014dff79d11f70913977aec76b7cc5e9fe9bd7dd783",
    ))
"""
import hashlib
import re
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE / "viz") not in sys.path:      # 与图形校验共用同一份 Report 结构
    sys.path.insert(0, str(_HERE / "viz"))
import vizkit                                # noqa: E402

Report = vizkit.Report

# ---- 许可判定：只认明确列出的；认不出的一律按「保留权利」处理 ----
# 顺序有意义：先判禁止项（NC/ND），再判可分发项。
_NOT_ALLOWED = re.compile(r"\bNC\b|\bND\b|non-?commercial|no-?deriv|非商用|禁止改|保留权利|all rights reserved",
                          re.IGNORECASE)
_ATTRIBUTION_NEEDED = re.compile(
    r"cc\s*by|creative commons|odbl|odc-by|mit|apache|bsd|gpl|mpl|署名|attribution",
    re.IGNORECASE)
_PUBLIC_DOMAIN = re.compile(r"public\s*domain|公有领域|cc0|cc-0", re.IGNORECASE)
_NO_LICENSE = re.compile(r"^\s*$|noassertion|unknown|none|null|未标注|无许可|没有许可", re.IGNORECASE)


def license_policy(lic):
    """把许可字符串判成 (可否随书分发, 是否必须署名, 说明)。

    认不出的许可 → (False, True, "认不出的许可，按保留权利处理")。
    这是**故意保守**：判错的代价是侵权，不是麻烦。
    """
    s = (lic or "").strip()
    if _NO_LICENSE.search(s):
        return False, True, "无许可/NOASSERTION —— 默认保留权利，不可随书分发"
    if _NOT_ALLOWED.search(s):
        return False, True, "许可含非商用/禁改条款 —— 不可随书分发（可引用、可自算，但不得搬运）"
    if _PUBLIC_DOMAIN.search(s):
        return True, False, "公有领域/CC0 —— 可分发，不强制署名（仍建议注明来源）"
    if _ATTRIBUTION_NEEDED.search(s):
        return True, True, "需署名的开放许可 —— 可分发，但必须给出 attribution 原文"
    return False, True, "认不出的许可 —— 按保留权利处理，不可随书分发"


def dataset(did, title, url, license, downloaded, local_file, local_sha256,
            license_url="", attribution="", upstream_sha256="", unit="", note="",
            redistributable=None):
    """登记一个外部数据集。构造期就检查许可判定与必填项，不合格当场抛 KeyError。"""
    if not re.fullmatch(r"[a-z][a-z0-9_]*", did or ""):
        raise KeyError(f"dataset id 必须是小写字母开头的标识符：{did!r}")
    ok, needs_attr, why = license_policy(license)
    if redistributable is None:
        redistributable = ok
    if redistributable and not ok:
        raise KeyError(f"dataset {did}：许可「{license}」判定为不可分发（{why}），"
                       f"不能标 redistributable=True")
    for fld, v in (("title", title), ("url", url), ("license", license),
                   ("downloaded", downloaded), ("local_file", local_file),
                   ("local_sha256", local_sha256)):
        if not v:
            raise KeyError(f"dataset {did}：必须给 {fld}")
    if needs_attr and not attribution:
        raise KeyError(f"dataset {did}：许可「{license}」要求署名，必须给 attribution 原文")
    if not re.fullmatch(r"[0-9a-f]{64}", (local_sha256 or "").lower()):
        raise KeyError(f"dataset {did}：local_sha256 必须是 64 位十六进制")
    return {"id": did, "title": title, "url": url, "license": license,
            "license_url": license_url, "attribution": attribution,
            "downloaded": downloaded, "local_file": local_file,
            "local_sha256": local_sha256.lower(), "upstream_sha256": upstream_sha256,
            "unit": unit, "note": note, "redistributable": bool(redistributable),
            "policy": why}


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Registry:
    """一个产品（书 / 技能 / 根级产品）用到的外部数据集登记表。"""

    def __init__(self, name=""):
        self.name = name
        self.items = {}

    def add(self, d):
        if d["id"] in self.items:
            raise KeyError(f"dataset id 重复：{d['id']}")
        self.items[d["id"]] = d
        return d

    def check(self, base_dir=None):
        """跑判据。base_dir = 登记里 local_file 相对于谁（产品根目录）。"""
        r = Report()
        for did, d in self.items.items():
            ok, needs_attr, why = license_policy(d["license"])
            # L1 许可判定复核（兜住「手改 dict 绕过构造」）
            if d["redistributable"] and not ok:
                r.err("L1", f"dataset[{did}]",
                      f"标了可分发，但许可「{d['license']}」判定为不可分发（{why}）",
                      "把 redistributable 改成 False，或换一个许可明确允许分发的数据源")
            if needs_attr and not d["attribution"]:
                r.err("L1", f"dataset[{did}]", f"许可「{d['license']}」要求署名，但没给 attribution",
                      "补上归属原文（照抄上游要求的写法）")
            # L2 指纹：必须与磁盘上那个文件的真实 sha256 一致
            if base_dir is not None:
                p = Path(base_dir) / d["local_file"]
                if not p.exists():
                    r.err("L2", f"dataset[{did}]", f"登记的本地文件不存在：{d['local_file']}",
                          "改 local_file，或把数据抓下来入库")
                else:
                    got = sha256_of(p)
                    if got != d["local_sha256"]:
                        r.err("L2", f"dataset[{did}]",
                              f"指纹不符：磁盘是 {got[:16]}…，登记的是 {d['local_sha256'][:16]}…",
                              "文件被换过或登记写错；先确认来源再更新指纹")
            # L3 上游指纹格式（有就必须是 64 位十六进制）
            if d["upstream_sha256"] and not re.fullmatch(r"[0-9a-f]{64}", d["upstream_sha256"].lower()):
                r.err("L3", f"dataset[{did}]", "upstream_sha256 必须是 64 位十六进制",
                      "从抓取脚本的输出里取")
            # L4 引用完整性：可分发却没给许可链接 → 警告（不是错，但必须显式知道）
            if d["redistributable"] and not d["license_url"]:
                r.warn("L4", f"dataset[{did}]", "可随书分发，但没给 license_url",
                       "补上许可原文链接，读者才好自行核对")
        return r
