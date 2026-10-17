#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
skillkit —— 全家族 edu-* 技能共用的最小运行时。

放在 `edulab/shared/skillkit.py`。每个技能的 `scripts/generate.py` 只保留
「自己的 kernel import + build_* 教学内容 + REGISTRY」，其余样板一律调用本模块。

## 为什么用「相对路径 + sys.path」而不是 vendoring

技能既要在仓库里跑，又可能被整目录复制到 `.agents/skills/` 单独使用。
两种布局到共享目录的**相对深度相同**：

    edulab/skills/<技能>/scripts/generate.py   →  ../../shared  →  edulab/shared
    .agents/skills/<技能>/scripts/generate.py  →  ../../shared  →  .agents/shared

所以 `sys.path` 里塞 `SKILL_DIR.parent.parent / "shared"` 两边都能命中，
无需把共享代码在每个技能里各存一份。安装时把 `edulab/shared` 复制成
`.agents/shared` 即可（见根 README）。

## 统一了哪些东西

重构前 9 个 generate.py 里有 4 种 CLI 写法、3 种 JSON 序列化、有的建目录有的不建；
现在收敛成一个 `cli()`，并且调用姿势统一为 `python generate.py <子命令> [参数]`：

    python scripts/generate.py list                  # 列出全部条目
    python scripts/generate.py all <目录>            # 生成全部（+ index.html）
    python scripts/generate.py random [seed] [输出]  # 随机出一题
    python scripts/generate.py <key> [输出.html]     # 生成单个

为了兼容历史调用，`cli()` 会自动丢掉看起来像脚本名的首个参数
（`generate.py` / `*.py`），因此 `main(sys.argv)` 与 `main(sys.argv[1:])`
两种旧写法都能平滑迁移。
"""

import json
import math
import random as _random
import re
import sys
from pathlib import Path

__all__ = ["SKILL_DIR", "shared_dir", "load_template", "render_html",
           "write_index", "default_validate", "required_sections", "cli",
           "verify_scene", "SceneMarkError"]

# 本文件所在目录即共享根（edulab/shared 或 .agents/shared）
SHARED_DIR = Path(__file__).resolve().parent


def _skill_dir() -> Path:
    """从调用方脚本的路径推断技能根目录（scripts/generate.py 的上两级）。"""
    return Path(sys.argv[0]).resolve().parent.parent


SKILL_DIR = _skill_dir()


def shared_dir() -> Path:
    return SHARED_DIR


def load_template(name="board.html", skill_dir=None):
    """读技能自己的模板。"""
    base = Path(skill_dir) if skill_dir else SKILL_DIR
    p = base / "template" / name
    if not p.exists():
        raise FileNotFoundError(f"模板不存在：{p}")
    return p.read_text(encoding="utf-8")


# ==================== 渲染 ====================
class SceneMarkError(ValueError):
    """几何记号与真实坐标不符 —— 记号会说谎，拒绝绘制。"""


def _xy(points, name):
    p = points.get(name)
    if not isinstance(p, dict):
        return None
    if isinstance(p.get("x"), (int, float)) and isinstance(p.get("y"), (int, float)):
        return (float(p["x"]), float(p["y"]))
    xy = p.get("xy")
    if isinstance(xy, (list, tuple)) and len(xy) == 2:
        return (float(xy[0]), float(xy[1]))
    return None


def _angle_at(pa, pv, pb):
    ux, uy = pa[0] - pv[0], pa[1] - pv[1]
    wx, wy = pb[0] - pv[0], pb[1] - pv[1]
    nu, nw = math.hypot(ux, uy), math.hypot(wx, wy)
    if nu == 0 or nw == 0:
        return None
    c = max(-1.0, min(1.0, (ux * wx + uy * wy) / (nu * nw)))
    return math.degrees(math.acos(c))


def verify_scene(data, *, angle_tol=1e-4, len_tol=1e-6):
    """画记号之前，先验证记号所断言的事实。

    记号不是装饰，是**断言**：
      · `right_angle_mark` 断言「角 a-vertex-b 是直角」；
      · `segment.ticks = N` 断言「所有同 N 道杠的线段等长」。

    作者写错一个点名字，图仍然画得漂漂亮亮，但它在撒谎 —— 读者会把直角符号
    当成已知条件、把同杠数当成等长去用。所以这里先算，不成立就抛错，绝不让它
    安静地画出去。原话借自 geometry-dsl：*a wrong figure fails loudly instead
    of lying quietly*。

    只处理 `board` 里带 `points` + `derived` 的结构；其它形态（如物理的
    `board.scene`）直接跳过，不做猜测。
    """
    board = data.get("board") if isinstance(data, dict) else None
    if not isinstance(board, dict):
        return
    points = board.get("points")
    derived = board.get("derived")
    if not isinstance(points, dict) or not isinstance(derived, list):
        return

    problems = []
    tick_groups = {}

    for i, d in enumerate(derived):
        if not isinstance(d, dict):
            continue
        kind = d.get("type")

        if kind == "right_angle_mark":
            a, v, b = d.get("a"), d.get("vertex"), d.get("b")
            pa, pv, pb = _xy(points, a), _xy(points, v), _xy(points, b)
            if pa is None or pv is None or pb is None:
                problems.append(
                    f"derived[{i}] 直角记号引用了缺坐标的点 "
                    f"{a}/{v}/{b}（图上会出现一个没有依据的直角符号）")
                continue
            ang = _angle_at(pa, pv, pb)
            if ang is None:
                problems.append(f"derived[{i}] 直角记号 ∠{a}{v}{b} 退化（有重合点）")
            elif abs(ang - 90.0) > angle_tol:
                problems.append(
                    f"derived[{i}] 直角记号 ∠{a}{v}{b} 实际 {ang:.4f}°，不是 90°")

        elif kind == "segment":
            n = d.get("ticks") or 0
            if not isinstance(n, int) or n <= 0:
                continue
            name = d.get("name") or f"{d.get('a')}{d.get('b')}"
            pa, pb = _xy(points, d.get("a")), _xy(points, d.get("b"))
            if pa is None or pb is None:
                continue
            tick_groups.setdefault(n, []).append((name, math.dist(pa, pb)))

    for n, items in tick_groups.items():
        if len(items) < 2:
            continue
        base = items[0][1]
        off = [f"{nm}={L:g}" for nm, L in items if abs(L - base) > len_tol]
        if off:
            desc = "，".join(f"{nm}={L:g}" for nm, L in items)
            problems.append(
                f"{n} 道等长记号被画在并不等长的线段上（{desc}）"
                f" —— 同杠数按约定表示等长")

    if problems:
        raise SceneMarkError(
            "几何记号与真实坐标不符，拒绝绘制（记号必须是真的）：\n  · "
            + "\n  · ".join(problems))


def render_html(data, out_path, *, template=None, token="__LESSON_DATA__",
                compact=False, escape_close=False, json_default=None,
                ensure_parent=True, skill_dir=None):
    """把 lesson 数据注入模板占位符，写出单文件 HTML。

    参数是为了让历史产物**逐字节不变**而保留的：
      compact        分隔符用 (",", ":")（默认用 json.dumps 的 ", " / ": "）
      escape_close   把 "</" 转成 "<\\/"（防止 payload 里的 </script> 逃逸）
      json_default  给 json.dumps 的 default=（例如 str）
      ensure_parent  自动建父目录（重构前有 3 个技能漏了这步，会直接抛异常）
    """
    if template is None:
        template = load_template(skill_dir=skill_dir)
    if token not in template:
        raise RuntimeError(f"模板中未找到占位符 {token}")
    # 记号先验证再画：直角符号 / 等长刻度必须与真实坐标一致。
    verify_scene(data)
    kw = {"ensure_ascii": False}
    if compact:
        kw["separators"] = (",", ":")
    if json_default is not None:
        kw["default"] = json_default
    payload = json.dumps(data, **kw)
    if escape_close:
        payload = payload.replace("</", "<\\/")
    html = template.replace(token, payload)
    out_path = Path(out_path)
    if ensure_parent:
        out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html, encoding="utf-8")
    return out_path


# ==================== 目录页 ====================
_INDEX_TPL = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>body{{font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif}}</style>
</head><body class="bg-slate-100 text-slate-900">
<div class="max-w-5xl mx-auto px-6 py-8">
  <div class="text-[11px] uppercase tracking-widest font-bold" style="color:{accent}">{kicker}</div>
  <h1 class="text-2xl font-bold">{title}</h1>
  <p class="text-sm text-slate-500 mt-1">{subtitle}</p>
  <div class="mt-6">{cards}</div>
</div></body></html>
"""


def write_index(out_path, entries, *, title, subtitle="", kicker="Interactive Lesson",
                accent="#0f766e"):
    """生成 index.html。entries 是 (key, module, title, blurb) 的可迭代对象。

    这是重构前 4 个技能各自手写一遍的那段 HTML（此处为等价实现）。
    """
    cards = []
    for key, module, ttl, blurb in entries:
        cards.append(
            f'<a href="{key}.html" class="block bg-white rounded-lg border border-slate-200 '
            f'p-4 hover:border-teal-500 hover:shadow transition-all">'
            f'<div class="text-[11px] font-bold mb-1" style="color:{accent}">{module}</div>'
            f'<div class="text-sm font-bold text-slate-900 leading-snug">{ttl}</div>'
            f'<div class="text-[11px] text-slate-500 mt-1">{blurb}</div></a>')
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        _INDEX_TPL.format(title=title, kicker=kicker, subtitle=subtitle,
                          accent=accent, cards="".join(cards)),
        encoding="utf-8")
    return out_path


# ==================== 校验 ====================
def default_validate(key, data):
    """所有技能都能通过的最低门槛：数据是 dict 且带非空 steps。

    重构前各技能的校验强度不一（有无、3 处、11 处断言各自为政），
    这里给一个统一下限；技能可以再传自己的 validate 做更严的检查。
    """
    if not isinstance(data, dict):
        raise AssertionError(f"{key}: build 返回值应为 dict，实际 {type(data).__name__}")
    steps = data.get("steps")
    if not isinstance(steps, list) or not steps:
        raise AssertionError(f"{key}: 缺少非空 steps（回放/步骤区需要它）")
    return True


def required_sections(*names, min_steps=1):
    """生成一个校验器：data 必须含 names 里的每个字段（非空），且 steps 不少于 min_steps。

    重构前这段代码在 math-sequences / physics-junior / physics-senior 里各写了一遍。
    """
    def _validate(key, data):
        for n in names:
            if not data.get(n):
                raise AssertionError(f"{key}: 缺少 {n}")
        steps = data.get("steps") or []
        if len(steps) < min_steps:
            raise AssertionError(f"{key}: 步骤不足（{len(steps)} < {min_steps}）")
        return True
    return _validate


def _looks_like_script(a):
    return a.endswith(".py") or re.fullmatch(r"generate(\.py)?", a) is not None


# ==================== 命令行 ====================
def cli(registry, *, doc=None, seeds=None, meta=None, groups=None,
        random_build=None, validate=None, prepare=None, render=None,
        index=None, index_writer=None, commands=None,
        template_name="board.html", token="__LESSON_DATA__", compact=False,
        escape_close=False, json_default=None, argv=None):
    """统一入口。返回进程退出码（0 = 成功）。

    registry      {key: callable() -> data}
    doc           --help / 无参数时打印的说明
    seeds         随机出题的候选 key（默认 = registry 全部）
    meta          key -> (module, title, blurb)，用于 list 与 index
    groups        {组名: [key...]}；给了则 list 分组打印
    random_build  自定义随机：callable(rng) -> (key, data)；不给则随机挑一个 key
    validate      callable(key, data) -> True / 抛异常；默认 default_validate
    prepare       callable(key, data) -> data，在 validate 之前做装配/整理
                  （例如 chem-reaction 的 assemble_data、solid-geometry 的 _answer 自检）
    render        callable(key, data, out_path) -> Path；按 key 选用不同模板时给
                  （例如 biology 的 board/cell 双模板）。给了它就不用 template_name。
    index         生成 index.html 时的标题；不给则 all 不生成 index
    index_writer  callable(out_dir) -> Path；技能自带 index 版式时给
    commands      {子命令名: callable(rest_args) -> int}；技能特有的额外子命令
                  （例如 edu-cs 的 verify）
    template_name / token / compact / escape_close / json_default
                  渲染配置，透传给 render_html（各技能序列化差异靠它保持逐字节一致）
    """
    args = list(sys.argv[1:] if argv is None else argv)
    # 兼容旧的 main(sys.argv)：丢掉形如脚本名的首个参数
    if args and _looks_like_script(args[0]):
        args = args[1:]
    validate = validate or default_validate
    pool = list(seeds) if seeds else list(registry)
    _tpl = None if render is not None else load_template(template_name)

    def _render(key, data, out):
        if render is not None:
            return render(key, data, out)
        return render_html(data, out, template=_tpl, token=token, compact=compact,
                           escape_close=escape_close, json_default=json_default)

    def _emit(key):
        data = registry[key]()
        if prepare:
            data = prepare(key, data)
        validate(key, data)
        return data

    def _list():
        if groups:
            for gname, keys in groups.items():
                print(f"[{gname}]")
                for k in keys:
                    if k not in registry:
                        continue
                    extra = ""
                    if meta:
                        m = meta(k)
                        extra = f"  {m[1]} —— {m[2]}" if m else ""
                    print(f"  {k:18s}{extra}")
            print()
            return 0
        for k in registry:
            line = f"  {k}"
            if meta:
                m = meta(k)
                line += f"   {m[1]}  （{m[0]}）" if m else ""
            print(line)
        return 0

    def _all(rest):
        out_dir = Path(rest[0]) if rest else (SKILL_DIR / "output")
        out_dir.mkdir(parents=True, exist_ok=True)
        for k in registry:
            print("written:", _render(k, _emit(k), out_dir / f"{k}.html"))
        if index_writer:
            print("written:", index_writer(out_dir))
        elif index:
            entries = [((k,) + meta(k)) if meta else (k, "", k, "")
                       for k in registry]
            write_index(out_dir / "index.html", entries, title=index,
                        subtitle=f"共 {len(registry)} 页 · 数据由 kernel 精确计算得出")
            print("written:", out_dir / "index.html")
        return 0

    def _random(rest):
        seed, out = None, None
        for a in rest:
            if out is None and not a.endswith(".html") and re.fullmatch(r"-?\d+", a):
                seed = int(a)
            else:
                out = a
        rng = _random.Random(seed)
        if random_build:
            key, data = random_build(rng)
        else:
            key = rng.choice(pool)
            data = registry[key]()
        if prepare:
            data = prepare(key, data)
        validate(key, data)
        print(f"random pick: {key}  seed={seed}")
        print("written:", _render(key, data, Path(out) if out else (Path.cwd() / f"{key}.html")))
        return 0

    if not args or args[0] in ("-h", "--help", "help"):
        print((doc or "").strip()
              or "用法：generate.py list | all <目录> | random [seed] [输出] | <key> [输出]")
        return 0
    cmd = args[0]
    if cmd == "list":
        return _list()
    if cmd == "all":
        return _all(args[1:])
    if cmd == "random":
        return _random(args[1:])
    if commands and cmd in commands:
        return commands[cmd](args[1:])
    if cmd not in registry:
        print(f"未知条目 {cmd!r}；可用：{', '.join(registry)}")
        return 1
    out = Path(args[1]) if len(args) > 1 else (Path.cwd() / f"{cmd}.html")
    print("written:", _render(cmd, _emit(cmd), out))
    return 0
