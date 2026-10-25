# 书稿目录：三本书，一套装配

```
books/
├── math-thought/        《数学思想：从计数到无穷》10 章 43 图（无事实登记表）
├── cosmos/              《万物尺度：从普朗克时间到宇宙年龄》读法 + 8 章 8 图，112 条登记
└── life/                《生命的尺度》读法 + 2 章 2 图，50 条登记（进行中）
```

三本书共用 `edulab/shared/bookbuild.py`（装配）与 `bookcheck.py`（插图校验）。
**不要复制 build.py**：两份会独立漂移，而「正文数字必须与内核同源」这类判据
依赖只有一条装配路径。改了共享模块后，用一条命令重建全部：

```bash
python edulab/tools/build_books.py          # 少重建一本，闸门会报「产物比源码旧」
```

## 一本书的目录结构

```
books/<书>/
├── book.json            书元数据 + 目录（章节清单、每章引用哪些图）
├── chapters/chNN.json   章节正文（块序列：lead / p / h2 / formula / figure / ...）
├── figures.py           插图：用 vizkit 构造 spec，全部现算
├── facts.py             （可选但推荐）事实登记表：正文 @@记号@@ 的值与出处
├── prose-values.json    生成值基线（`build.py --update` 写入，用来抓精度漂移）
├── build.py             一行封装 → shared/bookbuild.build(HERE, argv)
└── check.py             一行封装 → shared/bookcheck.check(HERE, argv)
```

`output/` 是产物，不入库（`.gitignore` 已排除）。

## book.json 里三个可选字段

| 字段 | 效果 |
|---|---|
| `front` | 无章号的前置页（如「读法」），`[{"id","title","file"}]`。走同一条装配路径，因此也能用 `@@记号@@`，也会被事实闸门扫到 |
| `siblings` | 目录页上的「另见」链接，`[{"title","href"}]`。用相对路径指向别书的 `output/` |
| `index_note` | 覆盖目录页页脚那句话 |

另外：**有 `facts.py` 的书会自动多出一页 `output/sources.html`**（「数字的出处」），
内容全部读自登记表（记号 / 值 / 等级 / 出处 / 用在哪章 / 说明），目录页自动加链接。
没有登记表的书不生成这一页 —— 不做空附录。

## 加一章：六步

1. **写正文** `chapters/chNN.json`，块类型见下表。数字**一律**写成 `@@记号@@`。
2. **写图** `figures.py` 里加一个函数，注册进 `FIGS`；在章节 JSON 里引用
   `{"type": "figure", "id": "fig-xxx", "height": 400, "caption": "..."}`。
3. **登记数字** `facts.py`：每个记号要么来自 `figures.prose_values()`，
   要么来自 `facts.REGISTRY`（四级：现算 / 实测 / 文献 / 约定）。
4. **登记到 book.json**：加章节条目（id / num / title / file / subtitle / figs）。
5. **跑图校验**：`python check.py -v`（0 错 0 警才算过）。
6. **出书**：`python build.py`（首次会提示基线不一致，确认后 `--update`）。

## 章节块类型

| type | 字段 | 用途 |
|---|---|---|
| `lead` | text | 章首导语（可多段） |
| `p` | text | 正文段落 |
| `h2` | text | 小节标题 |
| `formula` | tex | 独立公式（KaTeX） |
| `figure` | id, height, caption | 插图 + 图注（图注里也能用 `@@记号@@`） |
| `warn` / `note` / `quote` | text（quote 另有 cite） | 提示块 |
| `table` | headers, rows | 表格（单元格可用 `$…$`） |
| `steps` | items: [{t, d}] | 步骤列表 |

## 记号系统：`@@name@@` 与基线

- 渲染时按 `prose-values.json` 的精度规则：整数不带小数点、其余默认两位、
  `@@name:3@@` 指定三位。
- **名字拼错会直接报错**，不会静默留白。
- `build.py --update` 刷新基线；之后任何**值的精度变化**都会让 build 失败 ——
  光「值来自内核」不够，呈现方式也不能被悄悄改掉。

## 事实登记表（`facts.py`）

```python
from factreg import Registry, claim
REGISTRY = Registry("书名")

REGISTRY.add(claim("c_light", 299792458.0, "m/s", grade="约定",
                   note="1983 年 CGPM 把光速定义为这个整数"))
REGISTRY.add(claim("planck_time_s", ..., "s", grade="现算",
                   recompute=lambda: math.sqrt(...),      # 闸门会真的调用它
                   note="由 ħ、G、c 推出来"))
```

| 等级 | 必须给 | 含义 |
|---|---|---|
| 现算 | `recompute` | 由本表其它登记算出来，闸门**重新算一遍**并比对 |
| 实测 | `source` + `url` + `uncertainty` | 观测/实验值 |
| 文献 | `source` + `locator` | 页码 / 表号 / DOI |
| 约定 | `note` | 单位定义或演示参数，必须说明为什么只能约定 |

闸门 `tools/check_facts.py`：F1 必填项、F2 现算复算、F3 记号双向对齐、F4 正文未登记数字
（连年份也不放过；豁免只有 `$…$`、`@@记号@@`、结构性编号）。

## 对数轴（尺度图）

```python
"view": {"xRange": [1e-45, 1e18], "yRange": [-0.7, 8.7], "xlog": True, "pad": {...}}
```

三条硬前提（E7）：范围与数据全为正；**必须显式给 ticks**（自动刻度是线性间距，
用在 log 轴上位置是错的）；`xticklabels` 与 ticks 等长。刻度文字建议直接给字符串
（`fmtTick(1e9)` 会写成「100000万」）。

## 跑闸门

```bash
python edulab/books/<书>/check.py            # 插图几何校验（0 错 0 警）
python edulab/books/<书>/build.py            # 出书（校验不过就中止）
python edulab/tools/check_facts.py           # 事实核查（未接入的书会点名）
python edulab/tools/check_licenses.py        # 外部数据许可与指纹
```
