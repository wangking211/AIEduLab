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
           "verify_scene", "SceneMarkError", "SceneReport"]

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


_SAFE_FUNCS = {
    "sin": math.sin, "cos": math.cos, "tan": math.tan, "asin": math.asin,
    "acos": math.acos, "atan": math.atan, "sqrt": math.sqrt, "abs": abs,
    "min": min, "max": max, "pow": pow, "PI": math.pi, "pi": math.pi,
}


def _resolve(v, env):
    """把坐标解析成浮点：数字直接转；字符串（参数表达式）按 env 求值。

    解析不了返回 None —— 调用方必须把「算不出来」与「算出来是错的」分开。
    """
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(eval(v, {"__builtins__": {}}, {**_SAFE_FUNCS, **env}))
        except Exception:
            return None
    return None


def _point_xy(points, name, env):
    """解析点的 (x, y)。任一分量解析不出就返回 None —— 由 _point_state 定状态。

    坐标格式以**真实产物**为准：`{"xy": [x, y]}`（`{"x":…,"y":…}` 仅作兼容）。
    分量可以是数字，也可以是参数表达式字符串（如 `"2*cos(ang*PI/180)"`），
    后者按 env 求值，求不出即视为不可判定。

    「点不存在」与「坐标求不出」在这里**不区分**：前者由 `name in points` 判，
    后者由本函数判。混为一谈会把写错点名的硬错误降级成「无法判定」。
    """
    p = points.get(name)
    if not isinstance(p, dict):
        return None
    raw = p.get("xy")
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        xs, ys = raw
    else:
        xs, ys = p.get("x"), p.get("y")
    x = _resolve(xs, env)
    y = _resolve(ys, env)
    return (x, y) if x is not None and y is not None else None


def _angle_at(pa, pv, pb):
    """∠apb 的角度（度）。三点共线或重合返回 None —— 调用方按退化处理。"""
    ax, ay = pa[0] - pv[0], pa[1] - pv[1]
    bx, by = pb[0] - pv[0], pb[1] - pv[1]
    na = math.hypot(ax, ay)
    nb = math.hypot(bx, by)
    if na < 1e-12 or nb < 1e-12:
        return None
    c = max(-1.0, min(1.0, (ax * bx + ay * by) / (na * nb)))
    return math.degrees(math.acos(c))


def _point_state(points, name, env):
    """(坐标, 状态)，状态三值化 —— 这是本守卫能诚实的前提。

      'ok'      —— 坐标是数字，或表达式能按 env 求值 → 可以下结论；
      'missing' —— 点根本没定义（引用写错了名字）→ 硬错误：记号指向一个不存在的点；
      'blind'   —— 点定义了，但坐标是按默认参数求不出来的表达式 → **无法判定**。

    「算不出来」与「算出来是错的」是两回事。前者不报错，但必须留痕；
    若把 blind 也并进 errors，就是把「我不知道」谎报成「它错了」。
    """
    p = points.get(name)
    if not isinstance(p, dict):
        return None, "missing"
    got = _point_xy(points, name, env)
    if got is not None:
        return got, "ok"
    return None, "blind"


class SceneReport:
    """记号守卫的结论。

    · `errors` —— **读懂了记号，且算出来它在撒谎**。必须拒绝绘制。
    · `unread` —— **没读懂**：记号引用的东西按当前信息判不了。既不算通过，
      也不算失败，但必须打印出来，并在结论里声明「不覆盖这些地方」。

    二者互不替代。把 unread 混进 errors 会误杀合法的动态场景；把 unread 静默
    吞掉则等于假装验证过 —— 后者更危险。
    """

    __slots__ = ("errors", "unread")

    def __init__(self):
        self.errors = []
        self.unread = []

    @property
    def ok(self):
        """没有**确定为错**的记号。注意：ok 不代表全部验证过，看 unread。"""
        return not self.errors

    def __bool__(self):
        return self.ok

    def lines(self):
        """给人看的两段报告（空段不出现）。"""
        out = []
        if self.errors:
            out.append("错误（记号与真实坐标不符，已拒绝绘制）：")
            out += [f"  ✗ {m}" for m in self.errors]
        if self.unread:
            out.append("无法判定（按默认参数解析不出记号依赖的坐标）：")
            out += [f"  ? {m}" for m in self.unread]
        if not self.errors and not self.unread:
            out.append("记号守卫：全部记号均已验证通过。")
        return out

    def summary(self):
        """一句话结论，**必须**包含 unread 的声明。"""
        head = f"直角/等长记号：{len(self.errors)} 个确定为错"
        if self.unread:
            head += f"，{len(self.unread)} 个无法判定（结论不覆盖这些地方）"
        else:
            head += "，无未判定项"
        return head


def verify_scene(data, *, angle_tol=1e-4, len_tol=1e-6):
    """画记号之前，先验证记号所断言的事实。

    记号不是装饰，是**断言**：
      · `right_angle_mark` 断言「角 a-vertex-b 是直角」；
      · `segment.ticks = N` 断言「所有同 N 道杠的线段等长」。

    作者写错一个点名字，图仍然画得漂漂亮亮，但它在撒谎 —— 读者会把直角符号
    当成已知条件、把同杠数当成等长去用。所以这里先算，不成立就抛错，绝不让它
    安静地画出去。原话借自 geometry-dsl：*a wrong figure fails loudly instead
    of lying quietly*。

    **两种不通过要分开报**（见 `SceneReport`）：
      · 算出来是错的 → errors，抛 `SceneMarkError`；
      · 判不了（坐标是解析不出的表达式）→ unread，**不抛错**，返回并要求打印。

    判定在**参数默认值**上进行：动态场景的坐标可以写成表达式，
    按默认参数代入后能判就判，判不了就如实记为 unread。

    **任何预期外的异常都会被转成 unread 并让 `ok` 为 False。** 这是通用性质，
    不是针对某个场景的特例：校验器若能因自身 bug 静默失效，就比没有更危险 ——
    调用方会以为已验证过。异常走 unread 而不是 errors，是因为「我不知道」不等于
    「它错了」；但两者都让 `ok` 为 False，所以下游闸门照样拦得住。

    只处理 `board` 里带 `points` + `derived` 的结构；其它形态（如物理的
    `board.scene`）直接跳过，不做猜测。返回 `SceneReport`。
    """
    report = SceneReport()
    board = data.get("board") if isinstance(data, dict) else None
    if not isinstance(board, dict):
        return report
    points = board.get("points")
    derived = board.get("derived")
    if not isinstance(points, dict) or not isinstance(derived, list):
        return report

    tick_groups = {}
    tick_blind = []

    # 参数默认值：坐标可以写成表达式（如 "2*cos(ang*PI/180)"），按默认值验证。
    param = board.get("param") or {}
    env = {param.get("name"): param.get("value")} if param.get("name") else {}

    def xy(name):
        return _point_state(points, name, env)

    try:
        _verify_derived(report, derived, points, env, xy, tick_groups, tick_blind,
                        angle_tol, len_tol)
    except SceneMarkError:
        raise
    except Exception as exc:            # noqa: BLE001 —— 必须兜住一切，不能漏
        report.unread.append(
            f"verify_scene 内部异常 {type(exc).__name__}: {exc} —— "
            f"该场景未验证，不代表记号正确")
    if report.errors:
        raise SceneMarkError(
            "几何记号与真实坐标不符，拒绝绘制（记号必须是真的）：\n  · "
            + "\n  · ".join(report.errors))
    return report


def _verify_derived(report, derived, points, env, xy, tick_groups, tick_blind,
                    angle_tol, len_tol):
    """验证 derived 里的记号。**所有**异常由 verify_scene 兜住，这里只管判定。

    拆出来的理由：verify_scene 的职责是「绝不让异常逃出去」，本函数的职责是
    「判定得对」。两件事分开，才好在 verify_scene 里用一个 except 覆盖全部路径，
    而不是给每个分支各补一个特例。
    """
    for i, d in enumerate(derived):
        if not isinstance(d, dict):
            continue
        kind = d.get("type")

        if kind == "right_angle_mark":
            a, v, b = d.get("a"), d.get("vertex"), d.get("b")
            (pa, sa), (pv, sv), (pb, sb) = xy(a), xy(v), xy(b)
            if "missing" in (sa, sv, sb):
                bad = [n for n, s in ((a, sa), (v, sv), (b, sb)) if s == "missing"]
                report.errors.append(
                    f"derived[{i}] 直角记号引用了不存在的点 {bad}"
                    f"（图上会出现一个没有依据的直角符号）")
                continue
            if "blind" in (sa, sv, sb):
                bad = [n for n, s in ((a, sa), (v, sv), (b, sb)) if s == "blind"]
                report.unread.append(
                    f"derived[{i}] 直角记号 ∠{a}{v}{b} 的点 {bad} 按默认参数解析不出坐标，"
                    f"无法判定它是否真为 90°")
                continue
            ang = _angle_at(pa, pv, pb)
            if ang is None:
                report.errors.append(f"derived[{i}] 直角记号 ∠{a}{v}{b} 退化（有重合点）")
            elif abs(ang - 90.0) > angle_tol:
                report.errors.append(
                    f"derived[{i}] 直角记号 ∠{a}{v}{b} 实际 {ang:.4f}°，不是 90°")

        elif kind == "segment":
            n = d.get("ticks") or 0
            if not isinstance(n, int) or n <= 0:
                continue
            name = d.get("name") or f"{d.get('a')}{d.get('b')}"
            (pa, sa), (pb, sb) = xy(d.get("a")), xy(d.get("b"))
            if "missing" in (sa, sb):
                report.errors.append(
                    f"derived[{i}] 等长记号 {name} 引用了不存在的点 "
                    f"{[x for x, s in ((d.get('a'), sa), (d.get('b'), sb)) if s == 'missing']}")
                continue
            if "blind" in (sa, sb):
                tick_blind.append(f"{n} 道杠（{name}）")
                continue
            tick_groups.setdefault(n, []).append((name, math.dist(pa, pb)))

    for n, items in sorted(tick_groups.items()):
        if len(items) < 2:
            continue
        base = items[0][1]
        if any(abs(L - base) > len_tol for _nm, L in items):
            desc = "，".join(f"{nm}={L:g}" for nm, L in items)
            report.errors.append(
                f"{n} 道等长记号被画在并不等长的线段上（{desc}）"
                f" —— 同杠数按约定表示等长")

    if tick_blind:
        report.unread.append(
            "以下等长记号的端点按默认参数解析不出坐标，无法判定是否真等长："
            + "、".join(sorted(set(tick_blind))))
    # 注意：这里**不** raise。是否拒绝绘制由 verify_scene 统一裁决，
    # 这样它才能在一个 except 里同时处理「判定出错」与「判定本身崩了」。


# ==================== 内联资源（离线自足） ====================
# 页面曾经引 <script src="https://cdn.tailwindcss.com">：断网就整页排版塌掉。
# 现在改为**构建期编译好的静态 CSS**内联进来（shared/board/tailwind.min.css，
# 由 tools/build_tailwind_css.py 用 Tailwind CLI 生成）。
# 占位符留在模板里而不是直接嵌 36KB CSS：32 个技能的 template/board.html
# 否则各自复制一份，改一处要同步 32 处 —— 那种重复一定会漂移。
TAILWIND_TOKEN = "__TAILWIND_CSS__"

_tw_cache = {}


def tailwind_css():
    """读取共享的静态 Tailwind CSS（进程内缓存，只读一次）。"""
    key = "css"
    if key not in _tw_cache:
        p = Path(__file__).resolve().parent / "board" / "tailwind.min.css"
        _tw_cache[key] = p.read_text(encoding="utf-8")
    return _tw_cache[key]


def inline_assets(html):
    """把模板里的资源占位符替换成真实内容（当前只有 Tailwind CSS）。

    关键细节：**注入位置必须与 Play CDN 一致** —— 它把生成的 <style> 追加到
    `<head>` 末尾，因此 Tailwind 的 preflight 与 utilities 会压过页面自带的
    `<style>`。若把 CSS 放在原来 `<script>` 的位置（页面样式之前），优先级就
    反过来：页面里 `figure{margin:2rem 0}` 会盖掉 preflight 的 `figure{margin:0}`，
    整页高度当场漂移 85px（2026-10 实测）。所以这里先摘掉占位符，再统一插到
    `</head>` 之前。
    """
    if TAILWIND_TOKEN not in html:
        return html
    css = tailwind_css()
    block = "<style>" + css + "</style>"
    # 占位符可能被 `<style>` 包着（模板里的常规写法），也可能裸着
    if "<style>" + TAILWIND_TOKEN + "</style>" in html:
        html = html.replace("<style>" + TAILWIND_TOKEN + "</style>", "", 1)
    else:
        html = html.replace(TAILWIND_TOKEN, "", 1)
    if "</head>" in html:
        return html.replace("</head>", block + "\n</head>", 1)
    return html + block          # 没有 head 的极端情况：放到最前面也比丢失好


def render_html(data, out_path, *, template=None, token="__LESSON_DATA__",
                compact=False, escape_close=False, json_default=None,
                ensure_parent=True, skill_dir=None,
                require_full_verification=False):
    """把 lesson 数据注入模板占位符，写出单文件 HTML。

    参数是为了让历史产物**逐字节不变**而保留的：
      compact        分隔符用 (",", ":")（默认用 json.dumps 的 ", " / ": "）
      escape_close   把 "</" 转成 "<\\/"（防止 payload 里的 </script> 逃逸）
      json_default  给 json.dumps 的 default=（例如 str）
      ensure_parent  自动建父目录（重构前有 3 个技能漏了这步，会直接抛异常）
      require_full_verification  记号守卫有**无法判定**项（unread）时也判失败。
        默认 False：unread 只打印不阻断，历史产物逐字节不变。
        生成新内容时应传 True —— 盲区不该静默溜过，否则等于假装验证过。
    """
    if template is None:
        template = load_template(skill_dir=skill_dir)
    if token not in template:
        raise RuntimeError(f"模板中未找到占位符 {token}")
    # 记号先验证再画：直角符号 / 等长刻度必须与真实坐标一致。
    report = verify_scene(data)
    for _line in report.lines():
        print("[记号守卫] " + _line, file=sys.stderr)
    if report.unread and require_full_verification:
        raise SceneMarkError(
            f"记号守卫有 {len(report.unread)} 个记号无法判定"
            f"（默认参数下解析不出坐标），拒绝出图：\n  · "
            + "\n  · ".join(report.unread))
    kw = {"ensure_ascii": False}
    if compact:
        kw["separators"] = (",", ":")
    if json_default is not None:
        kw["default"] = json_default
    payload = json.dumps(data, **kw)
    if escape_close:
        payload = payload.replace("</", "<\\/")
    html = template.replace(token, payload)
    html = inline_assets(html)
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
<style>__TAILWIND_CSS__</style>
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
        inline_assets(_INDEX_TPL.format(title=title, kicker=kicker, subtitle=subtitle,
                                        accent=accent, cards="".join(cards))),
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
        # require_full_verification：记号守卫有「按默认参数解析不出坐标」的盲区时，
        # 直接拒绝出图。理由是「没验到的地方不等于没问题」—— 若只打印不阻断，
        # 生成出来的图看起来和验证过的图一模一样，读者无从分辨。14 个技能当前
        # 全部零盲区，所以这条不会误伤；将来真出现盲区，宁可 build 红，也别让它
        # 安静地画出去。需要绕过时传自己的 render= 回调。
        return render_html(data, out, template=_tpl, token=token, compact=compact,
                           escape_close=escape_close, json_default=json_default,
                           require_full_verification=True)

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
