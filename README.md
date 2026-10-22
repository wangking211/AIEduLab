# AIEduLab

多学科**交互教学内容**的实验场：可安装的教学技能（skills）+ 一套共享的**图形语法引擎** + 用它搭出来的「图解书」。

```
AIEduLab/
├── edulab/                 技能与图书的主体（见下方「来源」）
│   ├── shared/             全家族共用层
│   │   ├── viz/            ★ 图形语法层：一套 spec 描述图，引擎负责渲染/校验/改图
│   │   │   ├── viz.js        渲染引擎（16 图元、双主题、零依赖、Canvas 2D）
│   │   │   ├── vizkit.py     构造 DSL + 校验器（E1–E6/W1–W3）+ 补丁引擎
│   │   │   ├── bridge.py     本地桥：静态服务 + 读者提问 ⇄ agent 改图的实时通道
│   │   │   ├── grammar.md    写图契约（agent 读它生成新图）
│   │   │   ├── state.md      改图/补丁/实时通道契约（agent 读它改已有图）
│   │   │   └── page.html     书页模板（阅读流 + 内嵌图 + 步骤控件 + 问答面板）
│   │   ├── skillkit.py     ★ 技能共用运行时：统一 CLI / 渲染 / 校验 / 目录页
│   │   ├── board/          ★ 模板骨架（geom-fn / seq-phys 两家族）+ base 片段
│   │   └── video/          ★ 视频技能共享素材真源（中文字体；副本不入库）
│   ├── tools/
│   │   ├── check_skills.py     技能闸门：可运行 + 可复现（跨哈希种子）+ 与基线一致
│   │   │                       + 产物自检 + **执行级渲染冒烟**（第 8 项）
│   │   ├── check_render.py  ★ 执行级渲染闸门：用 node 桩**真跑**渲染路径
│   │   │                       （不抛异常 / 尺寸合法 / 有绘制 / 多帧指纹互异）
│   │   ├── viz_smoke.js         上面的 viz 层 harness（渲染引擎 × 图层 spec）
│   │   ├── page_smoke.js        上面的 page 层 harness（已构建 HTML + 最小 DOM 桩）
│   │   ├── compose_templates.py 用「共享骨架 + 各自片段」组装 template/board.html
│   │   ├── sync_video_assets.py 把 shared/video 真源同步进各视频技能的 template/
│   │   ├── check_semantics.py  语义校验：图注里的数字必须在内核/画布上找得到出处
│   │   │                       （含回归测试与校准记录；见 semantics-report.md）
│   │   ├── check_generated_prose.py 生成覆盖率：哪些数字是插值来的、哪些是手写的
│   │   ├── check_facts.py   事实核查闸门：正文里的每个数都要有等级与出处
│   │   │                       （现算/实测/文献/约定；连年份也不放过；见 shared/facts.md）
│   │   └── audit_diagramability.py 「图解能覆盖多少知识」的可行性审计（见 coverage-audit.md）
│   ├── books/math-thought/ 第一本书《数学思想：从计数到无穷》（10 章 43 图）
│   ├── skills/             32 个学科技能（数理化生 + 初高中 + 大学 + 视频 + CS）
│   ├── coverage-audit.md   「图解能覆盖多少知识」的可行性审计（现算，可重跑）
│   └── demos/ out/         手写 HTML 演示
├── .agents/skills/         技能安装副本（**本地目录，不进版本库**；真源是 edulab/skills/）
├── .agents/shared/         共用层安装副本（同上；真源是 edulab/shared/）
├── mental-models/          查理·芒格思维模型：sympy 内核 + 18 个交互页（含两页数据驱动）+ 速查文档
└── skills-lock.json        技能安装锁（含内容哈希）
```

## 只推源码

根 `.gitignore` 排除所有**构建与运行产物**：

- `output/` —— 每个技能/书籍 `scripts/generate.py` 或 `build.py` 生成的成品 HTML
- `_live/` —— `bridge.py` 的问答与补丁日志（运行时数据）
- `.agents/skills/` —— 技能的本地安装副本。**真源只有 `edulab/skills/` 一份**，
  避免 11MB 的逐字节重复；副本仅存在于本地，供技能加载器发现
- `edulab/skills/*/template/fonts/` —— 视频技能的字体副本。真源是
  `edulab/shared/video/fonts/`（全仓一份），副本由 `sync_video_assets.py` 同步，
  省掉 3.3MB 的三份重复。字体**不能**移出技能目录：浏览器按 `index.html` 的相对
  路径加载它们，且加载失败是静默降级（退回系统字体），所以闸门会逐字节校验副本
- `__pycache__/`、`node_modules/`、编辑器与系统文件

## 安装技能（本地）

技能加载器从 `.agents/skills/` 发现技能，而真源在 `edulab/skills/`。
每个技能的 `scripts/generate.py` 都会从 `../../shared/` 加载共用运行时
（`skillkit.py`）——两种布局到它的相对深度相同：

```
edulab/skills/<技能>/scripts/generate.py   → ../../shared  → edulab/shared
.agents/skills/<技能>/scripts/generate.py  → ../../shared  → .agents/shared
```

所以克隆后**两处都要复制**（改完 `edulab/` 后同样再复制一次）：

```powershell
Copy-Item "edulab\shared" ".agents\shared" -Recurse -Force
Get-ChildItem "edulab\skills" -Directory | ForEach-Object {
  Copy-Item $_.FullName ".agents\skills\$($_.Name)" -Recurse -Force
}
python edulab/tools/sync_video_assets.py      # 补上视频技能的字体副本（克隆后默认没有）
```

最后一步是必需的：视频技能的字体副本不入库（省掉 3.3MB 三份重复），
克隆下来是空的，必须从 `edulab/shared/video/` 真源同步一份。缺了它，
渲染时会**静默退回系统字体**——不报错，只是成片风格不对。

`skills-lock.json` 记录已安装技能的内容哈希。注意：现有条目是**安装当时的快照**，
若之后修改过技能源码，哈希不会再对得上 —— 它只作记录，不参与技能加载。

改完任意技能或根级产品后，跑一次闸门（可运行 + 跨哈希种子可复现 + 与基线/骨架一致）：

```bash
python edulab/tools/check_skills.py            # 差异即失败
python edulab/tools/check_skills.py --update   # 确认新产物正确后刷新基线
python edulab/tools/check_facts.py --selftest  # 事实核查闸门的负向测试（每条判据都要能红）
python edulab/tools/check_facts.py             # 核查所有带 facts.py 的书稿（未接入的会点名）
```

闸门覆盖 `edulab/skills/` 下的 10 个技能，外加仓库根的独立产品 `mental-models`
（它不走技能安装，但同样是「内核 + 模板 + 产物」这套约定，纳入后改动才有人把关）。
新增项**没有基线记录会直接判失败**而不是默认放行——否则加一个新技能闸门就自动对它
变绿，等于形同虚设。首次需要跑一次 `--update` 建立记录。

### 模板家族：改骨架，别改产物

六个技能的 `template/board.html` 原本是「复制一份再各自改」的产物，重复率很高、
改一处要同步多处。现在它们按家族由**共享骨架 + 各自片段**组装而成：

| 家族 | 成员 | 差异形状 |
|---|---|---|
| `geom-fn` | 解析几何 / 平面几何 / 函数与导数 | 20 个槽位，差异全是「在若干位置插入自己的块」 |
| `seq-phys` | 数列与三角 / 初中物理 / 高中物理 | 8 个槽位：head/tail 共用，只有场景函数与 `switch` 的 case 不同 |

```
edulab/shared/board/<家族>/shell.html         唯一骨架，槽位写成独占一行的 {{slot:name}}
edulab/shared/board/<家族>/parts/<name>.html  该槽位的 base 版本
<技能>/template/parts/<name>.html             该技能自己的版本；不存在则用 base 版本
```

解析规则刻意做成零配置：**自己的片段优先，缺失就回退到 base 版本**。
所以每个家族的 base 技能（`geom-fn` 的 analytic-geometry、`seq-phys` 的
math-sequences）一个片段文件都不需要。改模板时：

```bash
# 改 shared/board/<家族>/shell.html 或某个 parts/<name>.html，然后：
python edulab/tools/compose_templates.py          # 重新组装六份 board.html
python edulab/tools/compose_templates.py --check   # 只校验是否与骨架一致
```

组装产物**提交进仓库**，所以技能仍然自包含（`generate.py` 只读自己目录下的
`template/`，不依赖 `shared/board/`）；漂移由 `compose --check` 与
`check_skills.py` 一起拦住。组装器还会检查**孤儿片段**：技能若带 `template/parts/`
却不在任何家族里，会直接报错而不是让片段被静默忽略。

维护量由 3904 行降到 2014 行（−48.4%），六个产物逐字节不变。
新增同族技能时，把 shell 复制一份到自己目录、在 `FAMILIES` 里登记、按需补片段即可。

成品按需重新生成：

```bash
python edulab/books/math-thought/build.py     # 出书（校验不通过会中止）
python edulab/books/math-thought/check.py     # 43 张图 0 错 0 警
python edulab/books/math-thought/test_gates.py# 坏补丁闸门回归（双链路）
python edulab/shared/viz/vizkit.py selftest   # 校验器自测
python edulab/shared/viz/bridge.py serve --port 8810   # 起实时通道
```

## `edulab/` 的来源

`edulab/` 起源于开源项目 **[wy51ai/edulab](https://github.com/wy51ai/edulab)**，在其基础上扩展了：

- `shared/viz/` 图形语法层（引擎、校验器、补丁引擎、书页模板、实时桥）
- `books/` 图解书
- 7 个新技能：`edu-biology` `edu-cs` `edu-function-derivative` `edu-math-sequences`
  `edu-physics-junior` `edu-physics-senior` `edu-plane-geometry`
- 若干既有技能的修订

> 上游快照：`https://github.com/wy51ai/edulab.git` @ `6a9c8766061ca7101d10bab6fe3af716ec47bb07`（2026-10-10）
> 需要跟进开源更新时，从该地址取新版做对比合并。

## 环境

Python 3.14 + sympy（精确内核）、Node 18+（渲染冒烟与语法检查）。
产出是**单文件 HTML**：双击即开，不需要构建、不需要本地服务。

**排版已离线**：Tailwind 的类在构建期被编译成静态 CSS（36KB）内联进页面
（`shared/board/tailwind.min.css`，见同目录 `VENDOR.md`），不再联网。
剩下两项外部资源：**KaTeX**（公式）与 **Three.js**（3D 页）——
断网时页面照常打开、排版正常、画板可用，只有公式退化为 LaTeX 源码、3D 页空白。
这两类主机在 `tools/check_output.py` 里是**显式白名单**（引别的会报错），
每次跑闸门还会汇总「N 个产物依赖外部资源」——取舍必须一直可见。
见 `edulab/curriculum-roadmap.md` 第 16 条。
