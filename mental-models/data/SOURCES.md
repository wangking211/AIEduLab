# 数据出处与许可

本目录只有一个数据集：**大分叉（`divergence.html`）** 所用的长期人均 GDP 序列。
这是 `mental-models` 里唯一一个**数据驱动**而非公式驱动的模型，所以纪律不同：

> **公式页的纪律是不手写数字（全部现算）；数据页的纪律是不手写数据（全部现取）。**

---

## 1. 数据集

| 项 | 值 |
|---|---|
| 名称 | GDP per capita — Maddison Project Database（经 Our World in Data 轻度加工） |
| 原始出处 | Bolt, Jutta and Jan Luiten van Zanden (2024), "Maddison style estimates of the evolution of the world economy: A new 2023 update", *Journal of Economic Surveys*, 1–41. DOI: 10.1111/joes.12618 |
| 数据库版本 | Maddison Project Database 2023（169 国，至 2022 年） |
| 数据集 DOI | 10.34894/INZBF2 |
| 单位 | **international-$，2011 年价**（已按通胀与各国生活成本差异调整） |
| 时间跨度 | 公元 1 – 2022 年（区域性估计自 1820 年起） |
| OWID 最后更新 | 2024-04-26 |
| 抓取日期 | 2026-10-16 |

## 2. 抓取方式（可复现）

```bash
python scripts/fetch_maddison.py                # 下载 → sha256 校验 → 蒸馏
python scripts/fetch_maddison.py --raw <path>   # 用已下载的原始件
```

- 下载源：`https://ourworldindata.org/grapher/gdp-per-capita-maddison-project-database.csv`
- 原始件 **sha256**（抓取当时）：`0545ad6ca37529206af49f9f964f17af927e8c154c1fe8d3813c523e0d2f43f8`
- 源站一旦更新，脚本会**拒绝继续**并要求人工核对差异后 `--accept-new-hash` 重新锁定 —— 
  目的是不让数字被悄悄换掉。

## 3. 蒸馏结果

`maddison-gdp-per-capita.csv`（2188 行；仅保留以下 6 条长序列，未做任何插值）：

| 实体 | 覆盖 | 点数 |
|---|---|---|
| United Kingdom 英国 | 1000–2022 | 772 |
| France 法国 | 1–2022 | 748 |
| United States 美国 | 1650–2022 | 226 |
| Japan 日本 | 730–2022 | 154 |
| China 中国 | 1000–2022 | 136 |
| India 印度 | 1600–2022 | 152 |

选择理由：覆盖「西方最早起飞（英/法）、北美（美）、东亚（日/中）、南亚（印）」四类。
`maddison-source.json` 保存了 OWID 元数据中的单位、引用与更新时间，供脚本与核验读取。

## 4. 许可与**必须遵守的归属要求**

Maddison Project Database 2023 采用 **Creative Commons Attribution 4.0 International（CC BY 4.0）**，
允许再分发，但附带两条**我们恰好都触发**的要求：

> 当出现下列任一情形时，**除引用 MPD 之外，还必须引用各原始论文**：
> (a) 数据以**图形形式**展示；
> (b) 使用**少于 12 个国家**的子集做统计或其他用途。

本页在画板上**图形化展示**了 **6 个国家** —— 两条都命中。故逐国原始论文列于下节。

## 5. 逐国原始论文（摘自 MPD 2023 的 Sources 工作表）

**United Kingdom 英国**
- 公元 1 年：Scheidel, W. & Friesen, S. J. (2009), "The size of the economy and the distribution of
  income in the Roman Empire", *Journal of Roman Studies*, 99, 61–91.
- 1252–1700、1700–1870：Broadberry, S. N., Campbell, B., Klein, A., Overton, M. & van Leeuwen, B. (2015),
  *British Economic Growth 1270–1870*, Cambridge University Press.

**France 法国**
- 公元 1 年：Scheidel & Friesen (2009)（同上）。
- 1276–1800：Ridolfi, L. & Nuvolari, A. (2021), "L'histoire immobile? A reappraisal of French economic
  growth using the demand-side approach, 1280–1850", *European Review of Economic History*, 25(3), 405–428.

**United States 美国**
- 1650–1790：McCusker, J. J., "Colonial Statistics", *Historical Statistics of the United States:
  Earliest Times to the Present*, Cambridge University Press, V-671.
- 1790–1870：Sutch, R. (2006), "National Income and Product", 同上, III-23–25.

**Japan 日本**
- 724–1874：Bassino, J.-P., Broadberry, S., Fukao, K., Gupta, B. & Takashima, M. (2018),
  "Japan and the Great Divergence, 730–1874", CEI Working Paper Series 2018-13, Hitotsubashi University.
- 1874–1940：Fukao, K., Bassino, J.-P., Makino, T., Paprzycki, R., Settsu, T., Takashima, M. & Tokui, J. (2015),
  *Regional Inequality and Industrial Structure in Japan: 1874–2008*, Maruzen Publishing.

**China 中国**
- 1000–1661、1661–1933：Broadberry, S. N., Guan, H. & Li, D. D. (2018), "China, Europe and the Great
  Divergence: a Study in Historical National Accounting, 980–1850", *Journal of Economic History*, 78(4), 955–1000.
- 1661–1933：Xu, Y., Shi, Z., van Leeuwen, B., Ni, Y., Zhang, Z. & Ma, Y. (2016), "Chinese National Income,
  ca. 1661–1933", *Australian Economic History Review*, 57(3), 368–393.
- 1952–2008：Wu, H. X. (2014), "China's growth and productivity performance debate revisited",
  The Conference Board EPWP Series, EWP#14-01.

**India 印度**
- 1600–1870：Broadberry, S. N., Custodis, J. & Gupta, B. (2015), "India and the great divergence: an
  Anglo-Indian comparison of GDP per capita, 1600–1871", *Explorations in Economic History*, 55, 58–75.

**近期数据的通用来源**（MPD Sources 工作表的说明行）
- 2008–2022：纳入 TED 的国家取自 The Conference Board 的 Total Economy Database，
  其余国家取自联合国国民账户统计。

## 6. 已知局限（页面与文档须如实交代）

1. **早期数据极稀疏**：1820 年以前多为**估算**，且年份不连续（如中国 1000–1820 仅 44 个点，
   印度 1600 年以前没有数据）。所以图上**只连实测点、不做插值**，稀疏本身就是信息。
2. **PPP 基准拼接**：1990 年前用 1990 年 PPP，2011 年起用 2011 年 PPP，中间年份做了平滑衔接 ——
   跨 1990 边界的增速因此带有方法学痕迹。
3. **区域估计与国别序列口径不同**：区域（如 Western Europe）自 1820 年起才有。
4. **口径变化**：部分国家在 2008 年前后切换数据来源（见上）。

## 7. 引用格式

> Bolt, Jutta and Jan Luiten van Zanden (2024), "Maddison style estimates of the evolution of the
> world economy: A new 2023 update", *Journal of Economic Surveys*, 1–41. DOI: 10.1111/joes.12618
> —— 经 Our World in Data 轻度加工；本页另按 MPD 归属要求列出第 5 节的逐国原始论文。

本页为教学演示，数据经再分发（CC BY 4.0），不构成任何投资或政策建议。
