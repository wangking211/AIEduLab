# 第三方前端资源的来源与许可

本目录的 `tailwind.min.css` **不是手写的**，是用 Tailwind CLI 从本项目实际用到的
类名编译出来的静态 CSS。记录在这里是因为：一份 36KB 的生成物如果没人知道它是
怎么来的、能不能重造，它迟早会变成不可维护的黑箱。

## tailwind.min.css

| 项 | 值 |
|---|---|
| 内容 | Tailwind CSS v3.4.17 的 `base + utilities`，只含本项目用到的类 |
| 生成方式 | `python edulab/tools/build_tailwind_css.py`（装 `tailwindcss@3.4.17`，`--minify`） |
| 扫描范围 | 各技能/书稿/`mental-models` 的**产物 HTML + 模板**（见脚本 `CONTENT`） |
| 许可 | MIT（Tailwind Labs） |
| 校验 | `python edulab/tools/build_tailwind_css.py --check` 比对 sha256 |
| 体积 | ≈36 KB（内联进每页；Play CDN 运行时是 407 KB/页，不可接受） |

### 为什么要离线化

原先每页引 `<script src="https://cdn.tailwindcss.com">`：断网时排版**整体塌掉**
（工具类是这个项目的全部版面骨架），而文档长期写着「自包含」。详见
`curriculum-roadmap.md` 第 16 条。

### 重编译的正确顺序

类名集合 = 产物 ∪ 模板。所以改了模板或新增题型后：

1. 重新生成产物（`scripts/generate.py all <dir>`）
2. `python edulab/tools/build_tailwind_css.py`（产物里多了新类，CSS 要跟着长）
3. 再生成一次产物（把新 CSS 内联进去）

漏了第 3 步的表现是：新类没有样式，但页面能开、也不报错 —— 这是最难受的失败形态。
`check_output.py` 会把残留的 `__TAILWIND_CSS__` 占位符判成错误，但**漏类它查不出**，
所以改样式后务必在浏览器里看一眼。

### 与 Play CDN 的已知差异

用「逐元素比对 30 项计算样式」验证过 7 个代表页（见提交说明）：
5 页 0 差异，`edu-chem-reaction` 有 3 个步骤徽章差 1.6px 边框 ——
Play CDN 的 JIT 没给这些**运行时插入**的元素编译 `border-2`，静态 CSS 反而更忠于源码。

## 仍然走 CDN 的两项（已批准，非「离线可用」）

| 资源 | 主机 | 断网后果 |
|---|---|---|
| KaTeX（公式） | `cdn.jsdelivr.net` | 公式显示为 LaTeX 源码 |
| Three.js（3D 页） | `cdnjs.cloudflare.com` | 3D 页空白 |

KaTeX 要真离线需要连 20+ 个字体文件一起内联（每页 +1MB 量级），
是独立工程，见 roadmap 第 16 条。
