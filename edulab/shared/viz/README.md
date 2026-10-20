# shared/viz — 图形语法层

一套「声明式图形语法」，供 edulab 下所有学科与书籍共用。**不再为每个题型手写绘制代码**：
用数据描述图层，引擎负责坐标、绘制、标注避让与校验。

## 组成

| 文件 | 角色 | 谁用 |
|---|---|---|
| `viz.js` | **渲染引擎**（单文件、零依赖、Canvas 2D） | 浏览器。生成器会把它整段内联进自包含 HTML |
| `vizkit.py` | **构造 DSL + 校验器 + 补丁引擎** | Python 侧（人 / agent / CI） |
| `grammar.md` | **写图契约** | **agent 读它来生成新图** |
| `state.md` | **改图契约**（共享状态、补丁、实时通道） | **agent 读它来改已有的图** |
| `page.html` | **书页模板**（阅读流 + 内嵌图 + 状态层 + 问答面板） | 书稿构建 |
| `bridge.py` | **本地桥**（静态服务 + 提问/推补丁实时通道） | 读者与 agent 同时在线时 |

## 为什么这样分层

```
figures.py（纯数据 spec）  →  viz.js（渲染）  →  page.html（书页）
        声明式、可校验              图元 + 主题         排版与交互
```

**内容与渲染解耦**带来三件事：

1. **同一份 spec 两种用法**：预先编译成书（模式 B），或由 agent 在对话里现场生成（模式 A）。
2. **可校验**：spec 是数据，所以能在**出图之前**查出越界、重叠、变量名写错。
3. **风格统一**：换主题只改令牌，所有图自动适配（深色仪表盘 ↔ 浅色书页插图）。

## 快速上手

```python
import vizkit as vk

spec = vk.spec(
    view=[0, 30, 0, 120000],          # 世界坐标 [x0, x1, y0, y1]
    theme="paper",                     # "paper"（书页）| "dark"（画板）
    layers=[
        vk.axis(xlab="年", ylab="资金"),
        vk.line(fn="P*(1+r/100)^x", from_=[0, 30], stroke=vk.PAPER.accent),
        vk.text(1.0, 108000, "复利曲线"),
    ],
)
rep = vk.validate(spec, W=783, H=300)
print(rep.format())                    # 每条错误都带 ↳ 修法
```

```bash
python vizkit.py selftest              # 自证校验器能抓错（8 类）
python vizkit.py patchtest             # 自证补丁引擎（8 项）
python vizkit.py schema                # 打印图元清单与必填字段
python vizkit.py check spec.json 783 300
python vizkit.py patch spec.json patch.json out.json
```

## 共享状态（书页 ⇄ agent）

书页右下角「状态 / 交给 AI」：**导出状态**把「读者在看什么 + 图的完整 spec」交给 agent，
**应用补丁**把 agent 的改动立即生效并存为本地草稿。改动可经 `patch.py` **校验后入库**
成 `overrides.json`，成为书的一部分。

叠加次序：`原始 spec` → `overrides.json`（已入库）→ `LIVE`（AI 实时改的）→ `localStorage`（本地草稿，可还原）。
完整契约见 **`state.md`**。

```bash
python patch.py <patch.json>           # 校验 → 写入 output/overrides.json（不过则整批拒绝）
python patch.py --list / --clear
python book/test_gates.py              # 坏补丁闸门回归（4 类必拒 + 2 类必过，双链路）
```

## 实时通道（bridge.py）

静态书页无法与对话实时同步——`bridge.py` 补上这一层，**纯标准库、零依赖**：

```bash
python bridge.py serve --port 8810     # 服务书稿 output/ + 打开实时通道
python bridge.py asks                  # agent 看读者提了什么问
python bridge.py show ask_xxxxx         # 看问题 + 读者当时看到第几步、选中了什么
python bridge.py reply ask_xxxxx --patch p.json --say "回答文字"
python bridge.py log                   # 看已推的补丁
```

书页每张图下方有**「问这张图」**，提问走 `POST /api/ask`；agent 的补丁经 SSE 推回，
书页**不刷新就重画**并显示回答。桥不在时自动降级为纯离线阅读。

两个关键语义（写在 `state.md`）：

- **追加 vs 替换**：默认追加 `ops`；修订自己的上次改动必须加 `"replace": true`，否则内容翻倍。
- **幂等**：入库那条链路按内容签名 `sigs` 去重，同一份补丁重复应用会被跳过。

## 校验回路（agent 的标准用法）

```
写 spec → validate → 有 error 就按 fix 提示改 → 直到 ok → 才交付
```

校验项（都是实际踩过的坑）：

| 码 | 含义 |
|---|---|
| E1 | 顶层结构非法（view 未递增等） |
| E2 | 未知图元 |
| E3 | 必填字段缺失 / 未知字段（拼错） |
| E4 | 表达式引用了未定义变量 |
| E5 | 世界坐标越界 |
| E6 | 文本溢出画布 |
| W1 | 同水平带文本互相遮挡 |
| W2 | 方块类图元没开 `equalAspect` |
| W3 | 步骤缺 `note` |

**关键：校验器有自测**（`selftest()`），确保它真的能抓到错，而不是"永远说 OK"。

## 主题令牌

用令牌而非硬编码色值，换主题时整张图自动适配：

`accent` / `accent2` / `good` / `warn` / `bad` / `text` / `dim` / `muted` /
`panel` / `panelEdge` / `axis` / `grid` / `series[]` / `ramp[]`

## 图元一览

坐标类 `axis grid line bar point` · 结构类 `card arrow node edge region text glyph matrix timeline` ·
算法类 `array linear`

完整字段见 `grammar.md`；契约里还包含**选型指引**（什么图适合表达什么）与**高频错误清单**。

## 自检清单（改完必过）

- [ ] `python ../../tools/check_render.py --source viz --selftest` → **执行级**冒烟通过：
  真跑一遍 `mount → resize → render → 逐档回放`，比 `node --check` 强 ——
  语法错与运行时错一并抓住（`rect is not defined` 那次就是静态闸门全绿、页面全白）
- [ ] `python vizkit.py selftest` → 校验器自测通过
- [ ] `python vizkit.py patchtest` → 补丁引擎自测通过
- [ ] 书稿 `python check.py` → 全部图 0 错误 0 警告
- [ ] `python build.py` → 校验不通过会**中止出书**
- [ ] 书稿 `python test_gates.py` → 坏补丁闸门回归通过，且**书稿被原样还原**
- [ ] `python bridge.py serve` 起得来，`/api/status` 返回 JSON
- [ ] 无 `PYTHONIOENCODING` 环境下桥不崩（控制台编码自愈）
- [ ] 浏览器复核：0 控制台报错、图有内容、步骤控件可用、有桥时显示「已连接 AI」
