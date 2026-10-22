# datasets.py —— 外部数据集守则

> 一句话：**搬别人的数据之前，先回答「许可能不能搬」；搬完之后，要能证明「搬的就是它」。**

## 三关

| 关 | 问题 | 怎么落成机器可查的 |
|---|---|---|
| **出处** | 它从哪来？ | `url` + `downloaded`（抓取日期）+ `upstream_sha256` |
| **许可** | 许不允许随书分发？要不要署名？ | `license` 走**白名单式判定**；`redistributable` 与 `attribution` 必须与判定一致 |
| **指纹** | 入库的字节就是当初抓的吗？ | `local_sha256` 必须等于磁盘上那个文件的真实 sha256（闸门**每次真算**） |

## 许可判定：只认明确列出的

| 许可形态 | 可否随书分发 | 必须署名 |
|---|---|---|
| 空 / `NOASSERTION` / 未标注 / 未知 | ✗ **默认保留权利** | — |
| 含 NC（非商用）/ ND（禁改） | ✗ | — |
| 公有领域 / CC0 | ✓ | 不强制（仍建议注明来源） |
| CC BY\* / ODbL / MIT / Apache / BSD / GPL / MPL | ✓ | ✓ 必须给 `attribution` 原文 |
| **认不出的任何写法** | ✗ 按保留权利处理 | — |

最后一行是**故意保守**的：判错的代价是侵权，不是麻烦。想用某个许可，就把它加进
`datasets.py` 的白名单并写清理由——不要靠「大概能用」蒙过去。

本项目已明确**不可搬**的来源：MIT OpenCourseWare、OpenStax（均为 CC BY-NC-SA 4.0）。
它们可以读、可以学结构，但内容一律自算自绘。

## 用法

```python
from datasets import Registry, dataset

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
))
```

`dataset(...)` 在**构造期**就拦：缺必填项、或「保留权利却标了可分发」、或
「需署名的许可没给 attribution」——当场抛 `KeyError`，不留到闸门。

## 两个哈希覆盖的不是同一个东西

- `upstream_sha256`：抓取时**上游原始数据**的指纹（有的项目是规范化后的内容指纹）
- `local_sha256`：**入库的蒸馏文件**的指纹（闸门每次核对）

两者**不许互相顶替**。拿上游哈希去比本地文件，必然不符——这不是 bug，是常识：
中间隔着一道蒸馏。

## 判据

| 代码 | 管什么 | 红了说明 |
|---|---|---|
| **L1** | 许可判定与 `redistributable`/`attribution` 是否一致 | 有人绕过了构造（手改 dict），或署名漏了 |
| **L2** | 本地指纹 vs 磁盘真实 sha256；文件是否存在 | 文件被换过、登记写错、或数据没入库 |
| **L3** | 上游指纹格式 | 抄错了一位，或者根本不是哈希 |
| **L4**（警告） | 可分发却没给 `license_url` | 读者没法自行核对许可 |

## 跑

```bash
python tools/check_licenses.py --selftest   # 负向测试：每条判据都要能红
python tools/check_licenses.py              # 核查所有带 datasets.py 的产品
```

未接入的产品会被**点名**（不静默跳过）：没有 `datasets.py` 的产品不判红，
但也不等于它的数据许可被核查过。
