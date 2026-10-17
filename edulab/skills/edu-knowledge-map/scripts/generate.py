# -*- coding: utf-8 -*-
"""
generate.py —— 知识结构图：把「概念之间的前置关系」画成可交互网页。

    python scripts/generate.py list                  # 列出领域
    python scripts/generate.py all <目录>            # 生成全部（+ index.html）
    python scripts/generate.py fraction ./out.html   # 单个领域
    python scripts/generate.py random 7 ./out.html   # 随机一个领域

画面上的一切都由 lib/ks_kernel.py 现算：合法知识状态、覆盖关系、可学边界、
最短学习路径、到目标的缺口。改一条前置关系，全图跟着重算，不需要手改图。

依赖：只用标准库。
"""

import random as _random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
PLACEHOLDER = "__LESSON_DATA__"

sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))
sys.path.insert(0, str(SKILL_DIR / "lib"))

import ks_kernel as K                      # noqa: E402
from skillkit import cli                   # noqa: E402


# ---------------------------------------------------------------- 布局

def prereq_layout(d):
    """前置关系图的分层布局：无前置在第 0 层，每层内均分横坐标。

    这里只是**排版**，不是数学：层号来自 kernel 的最长路径分层。
    """
    lv = d.levels()
    groups = {}
    for c in d.ids:
        groups.setdefault(lv[c], []).append(c)
    top = max(lv.values()) if lv else 0
    out = []
    for c in d.ids:
        g = groups[lv[c]]
        i = g.index(c)
        out.append({
            "id": c,
            "label": d.label[c],
            "level": lv[c],
            "x": (i + 0.5) / len(g),
            "y": lv[c] / (top + 1) if top else 0.0,
        })
    return out


def board_of(d, target):
    """把内核算出的结构整理成画板数据。"""
    states = d.states()
    pos = d.lattice_layout()
    idx = {s: i for i, s in enumerate(states)}

    # 状态格：只保留能画得下的规模
    if pos:
        st_out = [{
            "id": idx[s],
            "members": [c for c in d.ids if c in s],
            "size": len(s),
            "x": pos[s][0],
            "y": pos[s][1] / (max(pos[t][1] for t in pos) + 1) if pos else 0,
            "layer": pos[s][1],
        } for s in states]
        cov_out = [[idx[a], idx[b]] for a, b, _c in d.covers()]
    else:
        st_out, cov_out = [], []

    path = d.learning_path(target)
    path_ids = [idx[s] for s in path]

    # 每一步加进来的概念（用于旁白与读数）
    steps_added = []
    for a, b in zip(path, path[1:]):
        steps_added.append(sorted(set(b) - set(a))[0])

    return {
        "title": d.title,
        "note": d.note,
        "goal": target,
        "concepts": prereq_layout(d),
        "edges": [{"from": p, "to": c} for c in d.ids for p in d.prereqs.get(c, [])],
        "states": st_out,
        "covers": cov_out,
        "path": path_ids,
        "steps_added": steps_added,
        "summary": d.summary(),
        "param": {
            "name": "k", "label": "学习到第几步",
            "min": 0, "max": max(0, len(path_ids) - 1), "step": 1, "value": 0,
            "ticks": ["起点"] + [d.label[c] for c in steps_added],
        },
        "readouts": [
            {"id": "mastered", "label": "已掌握概念", "type": "count"},
            {"id": "fringe", "label": "现在可学", "type": "fringe"},
            {"id": "gaps", "label": "到目标还差", "type": "gaps"},
            {"id": "size", "label": "状态大小", "type": "size"},
        ],
        "constant": {
            "label": f"合法知识状态总数 = {d.summary()['states']}（与学习到第几步无关）",
        },
    }


def lesson_of(d, target):
    """题面与答案。所有数字来自内核。"""
    path = d.learning_path(target)
    added = []
    for a, b in zip(path, path[1:]):
        added.append(d.label[sorted(set(b) - set(a))[0]])

    tgt = "、".join(d.label[c] for c in target)
    return {
        "language": "zh-CN",
        "title": d.title,
        "problem": (
            "<p class='font-medium text-slate-800'>【题目】</p>"
            f"<p>下面是「{d.title}」的概念表与前置关系。约定：一个概念只有在它的"
            f"<b>全部前置</b>都已掌握时才学得动。</p>"
            f"<ol class='list-decimal pl-5 space-y-1'>"
            f"<li>从零开始，学会 <b>{tgt}</b> 最少要按什么顺序学？</li>"
            f"<li>学到一半时，下一步能学哪些概念？</li>"
            f"<li>这个领域一共有多少个<b>合法的知识状态</b>？</li></ol>"
        ),
        "answerLabel": "到目标的最短学习顺序",
        "answer": " → ".join(added),
    }


def steps_of(d, target):
    """分步解析。数值全部来自内核，文字只解释「为什么」。"""
    path = d.learning_path(target)
    states = d.states()
    pos = d.lattice_layout()
    added = []
    for a, b in zip(path, path[1:]):
        added.append(sorted(set(b) - set(a))[0])

    # 取一个「学到中途」的状态演示可学边界
    mid = path[len(path) // 2] if path else frozenset()
    fringe = d.outer_fringe(mid)
    missing = d.gaps(mid, target)

    s = d.summary()
    return [
        {"title": "什么是「知识状态」",
         "content": (
             "<p>把「学生已掌握的概念」看成一个集合 K。K 合法，当且仅当"
             "<b>只要 c ∈ K，c 的所有前置也都在 K 里</b>——这种集合叫<b>下闭集</b>。</p>"
             f"<p>所以合法状态数不是 2<sup>{s['concepts']}</sup>，而是 <b>{s['states']}</b> 个："
             "前置关系把大部分组合排除掉了。</p>")},
        {"title": "前置关系是一张分层的图",
         "content": (
             f"<p>按「最长前置链」分层，这个领域有 <b>{s['levels']}</b> 层。"
             "最左边（第 0 层）是没有前置的概念，也是唯一能起步的地方。</p>"
             f"<p>整张图有 <b>{len(d.covers())}</b> 条覆盖关系（状态格上的边），"
             "每一条都对应「再学会一个概念」。</p>")},
        {"title": "最短学习路径",
         "content": (
             "<p>目标闭包里一共有 "
             f"<b>{len(d.closure(target))}</b> 个概念，所以最短路径必然恰好是 "
             f"<b>{len(path) - 1}</b> 步——每步只能加一个概念，少一步都学不动。</p>"
             f"<p>路径：{' → '.join(d.label[c] for c in added)}</p>")},
        {"title": "可学边界与缺口",
         "content": (
             f"<p>学到中途（已掌握 {len(mid)} 个概念）时，"
             f"<b>现在可学</b>的是：{'、'.join(d.label[c] for c in fringe) or '（无）'}。</p>"
             f"<p>要到目标还差：{'、'.join(d.label[c] for c in missing) or '（已达成）'}。</p>"
             "<p>注意「可学」与「该学」不是一回事：可学边界上是所有前置已满足的概念，"
             "但其中只有一部分在通往目标的路上。跳过顺序硬学，就是背公式。</p>")},
    ]


# ---------------------------------------------------------------- 构建

def build(domain_name, target=None):
    d = K.get(domain_name)
    probs = d.problems()
    if probs:
        raise ValueError(f"领域 {domain_name!r} 不合法：\n  · " + "\n  · ".join(probs))
    if target is None:
        # 默认取「前置最深」的那个概念作为目标
        lv = d.levels()
        target = [max(d.ids, key=lambda c: (lv[c], -d.ids.index(c)))]
    return {"lesson": lesson_of(d, target), "steps": steps_of(d, target),
            "board": board_of(d, target)}


def build_fraction():
    return build("fraction", ["add2"])


def build_derivative():
    return build("derivative", ["opt"])


def build_probability():
    return build("probability", ["bayes"])


REGISTRY = {
    "fraction": build_fraction,
    "derivative": build_derivative,
    "probability": build_probability,
}


def _random_build(seed=None):
    rng = _random.Random(seed)
    key = rng.choice(sorted(REGISTRY))
    return key, REGISTRY[key]()


def main(argv):
    return cli(REGISTRY, doc=__doc__, random_build=_random_build,
               template_name="board.html", token=PLACEHOLDER,
               index="知识结构图 · 前置关系与学习路径", argv=argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
