# 画图技能调研：图解一切知识还缺什么

> 目的不是找"更多画图工具"，而是回答一个问题：**要做"图解一切知识"，我们的能力边界缺哪几块，外部有没有现成的、能借的做法。**
>
> 方法：GitHub 14 组搜索 + `topic:agent-skills diagram` 全量 topic（291 仓库）+ 10 个候选仓库 README 全文实读。
> 标注约定：**[实读]** = 读过 README 全文或关键章节；**[元数据]** = 只看了仓库描述 / star / license，未读源码。
> license 一律核对到 SPDX；`NOASSERTION` 视为"无 license"，按默认保留权利处理，**一律不复用其内容**。

---

## 一、先说结论

**不需要"再找更多画图技能"。搜出来的 291 个仓库里，画的 90% 是架构图 / 流程图 / UML / ER —— 而"图解知识"要画的是概念、机制、过程、量级、结构。这个交集很小。**

但顺着搜索，暴露出我们**四块真实的能力缺口**，每一块都有外部现成做法可借：

| # | 缺口 | 我们现状 | 外部现成做法 |
|---|---|---|---|
| 1 | **产物侧没人检查** | 所有闸门读的都是源（`figures.py`、`chapters/*.json`、`SKILL.md`），渲染出来的 HTML 没人看 | svg-diagram 的 lint 读成品；drawio-ai-kit 的 vision self-check |
| 2 | **读不懂的字段被静默跳过** | `vizkit` 遇到不认识的字段直接跳过，其余检查基于残缺模型下结论，不告知 | svg-diagram 的 `document-model` 检查：**不产生发现，只报告"哪些坐标我没读懂"** |
| 3 | **出处是二元的** | 手写 / 生成，两档 | Mirofy 的六类 provenance，且"空结果 = 没找到，绝不等于不存在" |
| 4 | **知识之间怎么连，没有图** | 19 张图 + 13 个技能都在画**单个对象**；知识的前置关系、结构、学习路径没有对应图型 | knowledge-spaces（知识空间理论 → 知识状态格 / Hasse 图 / 学习路径） |

第 4 条是"图解一切知识"真正缺的那一层：**我们有画法，没有画"知识之间关系"的语法。**

---

## 二、我们的位置

先说已经对齐的，避免重复造轮子：

| 机制 | 我们 | 外部对照 |
|---|---|---|
| CJK 字宽按 1 个字号算 | `vizkit.CHA_WIDTH = 1.0` | 与 svg-diagram 的 CJK 字宽表一致 |
| 产物可复现 | `check_skills.py` 双跑比对 | 外部罕见 |
| 正文数值由内核现算 | `figures.py` 的 `*_values()` + `@@name@@` 记号 | 外部罕见 |
| 语义校验（数字对不对） | `check_semantics.py` | Mirofy 的 provenance 是同一思路的更强形式 |
| 画布几何校验 | `vizkit.validate` + `check_geometry.py` | drawio-ai-kit 的 structural validator |
| 无 license 不复用 | 本项目纪律 | — |

**结论：单点能力我们不落后，落后的是一致性与覆盖面**——尤其是"产物侧"和"结构侧"。

---

## 三、逐项借鉴清单

### A. 借得动的七件事（按性价比排序）

#### A1. 产物自检 —— 检查渲染出来的 HTML，不检查源 [高价值，已开工]

- **出处**：`bybit-exchange/svg-diagram`（627★ / MIT / **[实读]**）
- **原文**：
  > "The linter reads the finished SVG, not an intermediate format. Nothing sits between the receipt and the file you ship."
  > "0 errors, 0 warnings is the only pass."
- **借什么**：把 `check_output.py` 立成闸门——对外链白名单、本地引用可达、canvas 尺寸、残留模板记号、渲染残留（`undefined` / `NaN`）做检查。
- **落地**：`edulab/tools/check_output.py`。这一步已经被证明有效：写它之前先去浏览器量了一次真值，量出 **viz.js 的 `resize()` 会随窗口缩放无限撑高画布**（314.4 → 328.8 → 343.2 …，无上界）——源码里看不出来，只有量产物才现形（见提交 `3a4d98b`）。

#### A2. "报告我读不懂的部分" [高价值，未开工]

- **出处**：同上，`svg-diagram` 的第 13 号检查 `document-model`
- **原文**：
  > "…so the geometry checks never draw conclusions from coordinates they got wrong."
- **借什么**：`vizkit` 目前遇到不认识的字段就跳过。改成：**显式记录"哪些图元我没能解析"，并在报告里列出**，同时声明"下列几何检查基于不完整模型"。
- **为什么重要**：一条静默跳过的字段，可能正是坐标算错的那个字段。诚实报告"我不知道"比假装知道安全。

#### A3. 记号先验证再画 [高价值，未开工]

- **出处**：`shand001/geometry-dsl`（4★ / MIT / **[实读]**）
- **原文**：
  > `mark(right, A, B, C)` — "verify before you draw: a right-angle mark checks the angle is 90° before drawing it. **A wrong figure fails loudly instead of lying quietly.**"
- **借什么**：我们图上画的直角符号、等长记号、垂直记号，目前是"作者说它是它就是"。改成：**内核先算角度 / 边长，验证通过才画这个记号，不通过就报错。**
- **为什么重要**：这是我们语义纪律的自然延伸——我们已经在核数字，但没在核**几何记号**。一张图画着直角符号而那个角不是直角，比数字错更隐蔽，也更容易被读者当真。

#### A4. 出处分级 —— 六类 provenance [高价值，未开工]

- **出处**：`Hasan-Laraib/Mirofy`（5★ / MIT / **[实读]**，注意 star 少但设计质量极高）
- **原文**：
  > | `authored` | a human wrote it |
  > | `source-backed` | read out of a cited file and line range |
  > | `statically-derived` | computed from code without running it |
  > | `config-derived` | read from a manifest — configuration, not code |
  > | `runtime-observed` | seen in a real run |
  > | `inferred` | a guess, and labelled as one |
  >
  > "A file the scanner cannot parse becomes a recorded **gap**, never a silent omission."
  > "Empty results mean **not found**, never 'does not exist'."
- **借什么**：把我们 `SOURCES.md` 里"手写 / 生成"的二元标注，升级成分级标注。至少先落三档：
  - `现算` —— 内核每次跑出来的（我们已有的强项）
  - `实测` —— 从数据文件读出来的（有 sha256 指纹）
  - `手写` —— 人写死的
- **配套措辞纪律**：查不到就说"未发现"，不说"不存在"。

#### A5. "什么时候不该用本技能" [高价值，未开工]

- **出处**：`Agents365-ai/drawio-skill`（10,190★ / MIT / **[实读]**）
- **原文**：
  > **Reach for a sibling skill instead when you need:** —— 后接一串指向兄弟技能的路由表
- **借什么**：13 个技能各自加一段"什么时候**不**该用本技能 / 该用哪个兄弟技能"。
- **为什么重要**：技能描述决定自动触发。没有"不该用"的边界，路由会在边界案例上乱选。

#### A6. 视觉自检 [中价值，受环境限制]

- **出处**：`sparklabx/drawio-ai-kit`（657★ / MIT / **[实读]**）
- **原文**：
  > build → validate → **render + vision self-check** → final-export
- **借什么**：渲染成图，再看一眼。
- **现实约束**：本机无 chromium / ffmpeg，`browser.screenshot` 不可用 → 目前做不了。**可替代方案**：用 `browser.tabs.open` + `browser.evaluate` 采样 canvas 像素验证（本次已用这个办法挖出 A1 里的 bug）。

#### A7. 选"够用的最低一级表达" [中价值，影响入口设计]

- **出处**：`ChangWenC/understanding-ladder`（100★ / MIT / **[实读]**），基于 Karpathy 2026-10 的"理解阶梯"
- **原文**：
  > "pick the lowest rung that fully answers"
  > "**Nothing cut**" — 简化语言不等于删内容
  > "**Draft first**" — 图/页/视频都从一份可校对的文本草稿起
  > "**'Easier to understand' ≠ 'verified'**" — 结尾必须给该检查什么
- **借什么**：我们 13 个技能目前都是"直接出交互页"。缺一步判断：**这个问题其实一行字就够了，不必做图。**
- **注意**：这条与我们的纪律高度同频（尤其"更易懂 ≠ 已核验"），几乎是给我们的做法换了个名字。价值在于**入口处加一道降级判断**。

---

### B. 结构层：图解一切知识缺的那一层

#### B1. 知识空间理论 → 知识状态格 / 学习路径 [最值得立项]

- **出处**：`vanderbilt-data-science/knowledge-spaces`（11★ / MIT / **[实读]**）
- **理论底子**（它写得非常扎实）：
  - **Knowledge Space Theory**（Doignon & Falmagne, 1999）—— ALEKS 背后的数学框架，服务过数百万学生
  - **Competence-Based KST**（Heller & Stefanutti, 2024）—— 加一层潜在能力，解释"为什么存在前置关系"
  - **Formal Concept Analysis** —— 格论方法发现概念层级
  - **Evidence-Centered Design**（Mislevy et al., 2003）
- **可产出的图型**（每一类都是我们现在画不出来的）：
  1. **前置关系图**（哪些概念是哪些的前置）
  2. **知识状态格 / Hasse 图**（学生可能处于的全部状态构成的格）
  3. **学习路径**（从状态 A 到状态 B 的可行路线）
  4. **知识缺口图**（想掌握 X，还差哪几块）
- **为什么这条最值得做**：它把"知识"变成了**可画的对象**。我们前面所有图解都在画"某个概念本身"，这条线画的是"概念之间的关系"——这正是"图解一切知识"里"一切"二字所依赖的东西。
- **实现方式**：纯标准库可跑（它本身就是为 Claude Code 写的），前置关系可以由内核维护 + 人工校订，图用我们已有的 vizkit 画。
- **落地建议**：新技能 `knowledge-structure`（或并入 mental-models），第一批内容用**我们自己已有的 18 个思维模型 + 书稿 8 章**做数据——既是内容也是自检样本。

---

### C. 参考但不直接借的（看方向，不抄做法）

| 仓库 | ★ | license | 实读? | 看什么 |
|---|---|---|---|---|
| `tt-a1i/archify` | 84,505 | MIT | [实读] | **最成功的一个**，但方向是"把代码库变成可交互架构图"，与知识图解不同路。可看它的 **修正闭环**：`diagnostics[]` + 每条给 `supportedFixes`、**限两轮修正**、且明说"视觉复核另外单独做"——机器校验与人眼复核分离，这个纪律值得抄 |
| `cathrynlavery/diagram-design` | 56,477 | MIT | [实读] | 44 图型 + 89 条规则 + `lint-skin.py` / `lint-render.py` / `verify-geometry.py` / `verify-docs-sync.py` 四件套。**它的校验是"版式"，我们的是"语义"，互补不竞争** |
| `patrick-xin/diagram-design-zh` | 43 | MIT | — | 中文排版安全（CJK 断行 / 标点挤压），画中文图时可查 |
| `Agents365-ai/drawio-skill` | 10,192 | MIT | [实读] | 除 A5 外：**从真实源生成**（Terraform/K8s/SQL/OpenAPI → 图），思路可借鉴——知识图解也应从"源"生成而非手摆 |
| `nicobailon/visual-explainer` | 10,476 | MIT | — | 一页 HTML 讲清 diff / 计划 / 数据表 |
| `antvis/Infographic` | ~7,006 | MIT | [部分] | AntV 出品，"文字变信息图"，流式渲染 |
| `dwzhu-pku/PaperBanana` | 7,164 | Apache-2.0 | — | 自动学术插图 |
| `llmsresearch/paperbanana` | 2,404 | MIT | — | 同上开源扩展版 |
| `faridrashidi/cnsplots` | 702 | BSD-3-Clause | — | Cell / Nature / Science 出版级图 |
| `Sleepy-Avacado/FigGenie-paper-diagram-skill` | 167 | MIT | — | 中文，顶会风格论文图 |
| `MiaoQichuan/new-litigation-visualization` | 133 | MIT | — | **"把法律画出来"**，7 个模块（诉讼图 / 时间轴 / 对抗图 / 法律关系图）。**这是"每个领域起一个图解技能"的现成样板**，模块划分方式值得抄 |
| `HututuWorks/sci-diagram-pptx` | 30 | Apache-2.0 | — | provenance-bound、fail-closed 的科学机制图 QA |
| `shand001/geometry-dsl` | 4 | MIT | [实读] | 除 A3 外：**确定性输出**（同样的 `.geom` 编译出字节相同的图）+ **稳定错误码**（行/列）——我们的可复现闸门与它同路 |
| `sparklabx/drawio-ai-kit` | 657 | MIT | [实读] | 除 A6 外：**小模型友好**——每一步点名"哪个文件、哪条命令" |
| `Aryanutkarsh/SeeCode` | 566 | MIT | [元数据] | "Animated, explorable diagrams from a short JSON spec" —— 与我们 vizkit 的路子一样，可对照它的 spec 设计 |

---

### D. 明确不借

| 仓库 | ★ | 为什么不借 |
|---|---|---|
| `muthuishere/hand-drawn-diagrams` | 78 | **NOASSERTION**（无 license）→ 按默认保留权利，不复用其内容 |
| `Agents365-ai/365-skills` | 85 | 无 license |
| `kimlawtech/korean-patent-diagram` | 19 | 无 license |
| `ystemsrx/sql_to_ER` / `libnyx/LT2MD` / `drawcms/drawcms` | 191 / 109 / 26 | AGPL-3.0，与本项目许可策略不合 |
| 各类 `awesome-*` 清单、PPT 类 | — | 与"图解知识"无关 |
| Mermaid / Excalidraw / draw.io 直接引为运行时 | — | 破坏**单文件产物**（要额外引运行时库；本项目现有 CDN 依赖已是已知取舍，不能再加） |

---

## 四、三条筛选标准（以后按这个筛）

1. **零构建期依赖 / 单文件 HTML** —— 产物双击可开，不需要构建、不需要本地服务
   （**注意**：排版已离线（内联编译后的 Tailwind CSS）；仍走 CDN 的只有
   KaTeX 公式与 Three.js 3D，断网时分别退化为 LaTeX 源码、空白。
   见 `curriculum-roadmap.md` 第 16 条与 `shared/board/VENDOR.md`）
2. **产物能被脚本校验** —— 不能靠"看着对"
3. **license 明确 MIT / Apache / BSD** —— `NOASSERTION` 一律不碰

---

## 五、一个观察

**搜出来的画图技能 90% 画的是架构 / 流程 / UML / ER。** 这类图的共同点是：**节点是给定的，画的是连线。**

而"图解知识"难的地方在前一步：**节点是自己想出来的，连线要自己论证。** 所以这 291 个仓库里，真正与我们同路的只有 5 个：

`diagram-design`、`understanding-ladder`、`knowledge-spaces`、`geometry-dsl`、`litigation-visualization`。

其中 `knowledge-spaces` 是唯一把**知识本身当图对象**的——这就是我们该立项的那一条。

---

## 六、落地顺序

| 顺序 | 事项 | 状态 |
|---|---|---|
| 1 | A1 产物自检 `check_output.py` | **已完成**（`c3ea80c`，7 项；O4/O5 直接抓画布自增长与宽度口径漂移） |
| 2 | A2 document-model（报告读不懂的部分） | **已完成**（`ef53e07`，`Report.unread` + 元素级字段白名单） |
| 3 | A3 记号先验证再画 | **已完成**（`ef53e07`，`verify_scene`；上线即抓到 4 处记号撒谎） |
| 4 | A4 出处分级 | **已完成**（`mental-models/lib/provenance.py`；18 个模型分「现算 / 实测 / 假设」，假设逐条列出，报告与代码不同步即闸门失败） |
| 5 | A5 "什么时候不该用本技能" × 13 | **已完成**（`ef53e07` + 闸门；含 3 个视频技能） |
| 6 | B1 知识结构图新技能 | **已完成**（`0a94626`，`edu-knowledge-map`） |
| 7 | A6 视觉自检 | **部分机器化**：`tools/check_render.py`（+ `viz_smoke.js` / `page_smoke.js`）用 node 桩**真执行**渲染路径，验「不抛异常 / 有绘制 / 多帧指纹互异」；但它**不是像素级视觉检查**（无 GPU、无真实字体排版），3D 页仍需真机浏览器；环境限制（无 chromium）下用 `browser.evaluate` 采样像素曾是唯一替代 |

---

## 七、anatomy：3D 人体解剖的可行性

生物技能目前只能画 2D 示意图（细胞、反射弧、能量金字塔）。器官形态要 3D 才讲得清，
但这条路被**许可**卡住了，三个候选只有一个能用。

| 项目 | ★ | license | 结论 |
|---|---|---|---|
| `thebuggeddev/anatomy`（Three.js 交互式人体解剖，GPT 5.6 Sol 生成） | 3,684 | **无**（`license: null`） | **不可复用**。无 license = 默认保留权利，连模型带代码都不能抄 |
| `jixiangying/anatomy`（基于 BodyParts3D，11 大系统、双语标注、全局搜索） | 57 | **无**（`license: null`） | **不可复用**；但它的**产品结构**（按系统分组 + 双语标注 + 搜索）值得学 |
| BodyParts3D（DBCLS，日本，FMA 本体驱动的 3D 网格库） | — | **CC BY-SA 2.1 JP** | **唯一可用**，但要接受 share-alike |

### BodyParts3D 的三个约束

1. **署名必须带原文**：
   > "BodyParts3D, (c) The Database Center for Life Science licensed under
   > CC Attribution-Share Alike 2.1 Japan"
2. **SA 传染**：改了网格 / 基于它做衍生图，衍生作品也得按 CC BY-SA 2.1 JP 发布。
   这和我们「自包含 HTML」不冲突，但和「闭源分发」冲突。
3. **体积**：全库网格是几百 MB 量级，塞不进单文件网页。要用就得**按系统裁剪**
   （比如只取心脏 + 主要血管）并做网格简化。

### 结论

解剖 3D **可以做，但不是「借一个技能」的事**：只能自己从 BodyParts3D 取数据、
裁剪、简化、署名，并且接受 SA。相比之下，`edu-biology` 现在的 2D 示意图
（细胞器、反射弧）性价比高得多；3D 解剖应当单独立项，而不是塞进现有技能。

---

## 附：搜索方法与命中概况

- 查询组：`topic:agent-skills diagram`（291 仓库）、`agent skill diagram SKILL.md`、`SKILL.md mermaid drawio excalidraw skill`、`topic:claude-skills diagram`、`skill knowledge-graph concept-map`、`skill data-visualization svg chart`、`cjk chinese diagram skill`、`figure matplotlib publication skill`、`hand-drawn diagram skill`、`architecture diagram skill`、`ascii diagram skill`、`topic:agent-skills visualization`、`SKILL.md whiteboard sketch note` 等
- 补充检索：TikZ / GeoGebra 方向（`Patrick-Healy/tikz-diagrams-skill`，含 animate.sty 动画与 visual QA，依赖 TeX 栈，与我们自包含路线不合）、Explorable Explanations 方向（Bret Victor / Nicky Case / Distill 的设计模式，属**方法论**而非可执行技能）
- 实读 README：10 个（`archify`、`bybit-exchange/svg-diagram`、`sparklabx/drawio-ai-kit`、`ChangWenC/understanding-ladder`、`vanderbilt-data-science/knowledge-spaces`、`Hasan-Laraib/Mirofy`、`shand001/geometry-dsl`、`antvis/Infographic`、`nicobailon/visual-explainer`、`Agents365-ai/drawio-skill`）
- 已在本项目调研中覆盖、本文不重复：`cathrynlavery/diagram-design`（另有中文版 `patrick-xin/diagram-design-zh`）、`thebuggeddev/anatomy`（无 license 不可用）、`jixiangying/anatomy`
