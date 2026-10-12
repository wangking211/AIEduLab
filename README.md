# AIEduLab

多学科**交互教学内容**的实验场：可安装的教学技能（skills）+ 一套共享的**图形语法引擎** + 用它搭出来的「图解书」。

```
AIEduLab/
├── edulab/                 技能与图书的主体（见下方「来源」）
│   ├── shared/viz/         ★ 图形语法层：一套 spec 描述图，引擎负责渲染/校验/改图
│   │   ├── viz.js          渲染引擎（16 图元、双主题、零依赖、Canvas 2D）
│   │   ├── vizkit.py       构造 DSL + 校验器（E1–E6/W1–W3，每条带 ↳ 修法）+ 补丁引擎
│   │   ├── bridge.py       本地桥：静态服务 + 读者提问 ⇄ agent 改图的实时通道
│   │   ├── grammar.md      写图契约（agent 读它生成新图）
│   │   ├── state.md        改图/补丁/实时通道契约（agent 读它改已有图）
│   │   └── page.html       书页模板（阅读流 + 内嵌图 + 步骤控件 + 问答面板）
│   ├── books/math-thought/ 第一本书《数学思想：从计数到无穷》（3 章 11 图）
│   ├── skills/             13 个学科技能（数理化生 + 初高中物理/几何 + 视频 + CS）
│   └── demos/ out/         手写 HTML 演示
├── .agents/skills/         技能安装副本（**本地目录，不进版本库**；真源是 edulab/skills/）
├── mental-models/          查理·芒格思维模型：sympy 精确内核 + 交互页
└── skills-lock.json        技能安装锁（含内容哈希）
```

## 只推源码

根 `.gitignore` 排除所有**构建与运行产物**：

- `output/` —— 每个技能/书籍 `scripts/generate.py` 或 `build.py` 生成的成品 HTML
- `_live/` —— `bridge.py` 的问答与补丁日志（运行时数据）
- `.agents/skills/` —— 技能的本地安装副本。**真源只有 `edulab/skills/` 一份**，
  避免 11MB 的逐字节重复；副本仅存在于本地，供技能加载器发现
- `__pycache__/`、`node_modules/`、编辑器与系统文件

## 安装技能（本地）

技能加载器从 `.agents/skills/` 发现技能，而真源在 `edulab/skills/`。
克隆仓库后，把需要的技能复制过去即可（改完 `edulab/skills/` 后同样复制一次）：

```powershell
Copy-Item "edulab\skills\edu-cs" ".agents\skills\edu-cs" -Recurse -Force
```

`skills-lock.json` 记录已安装技能的内容哈希。注意：现有条目是**安装当时的快照**，
若之后修改过技能源码，哈希不会再对得上 —— 它只作记录，不参与技能加载。

成品按需重新生成：

```bash
python edulab/books/math-thought/build.py     # 出书（校验不通过会中止）
python edulab/books/math-thought/check.py     # 11 张图 0 错 0 警
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

Python 3.14 + sympy（精确内核）、Node 18+（语法检查）。技能与图书**不依赖第三方前端框架**，
产出都是自包含的单文件 HTML（KaTeX 走 CDN，可离线降级）。
