# -*- coding: utf-8 -*-
"""
generate.py — 计算机科学：注入模板 + 范例 build_* + CLI + 随机出题。

唯一模板 template/board.html —— 数据驱动的「算法步骤回放」画板：
  · 右栏 Canvas 按 LESSON.scene.kind 分发到 11 种渲染器
    （bars / curve / linear / linked / tree / graph / table / bits / call / coins / interval）；
  · 每一帧都直接取自 lib/cs_kernel.py 录下的 steps[i]，动画不编造状态；
  · 左栏「动态控制台」的滑块驱动表达式实时求值，读数可链式引用，
    讲义文字里的数字与画板读数同源。

用法：
  python generate.py verify                              # 注册表 + 契约校验（推荐先跑）
  python generate.py list
  python generate.py sort_bubble ./out/sort_bubble.html
  python generate.py all ./out
  python generate.py random ./out
"""

import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SKILL_DIR.parent.parent / "shared"))   # 共享运行时（edulab/shared/skillkit.py）
sys.path.insert(0, str(SKILL_DIR / "lib"))

import cs_kernel as K                          # noqa: E402
from skillkit import cli, inline_assets                       # noqa: E402


# ==================== 载荷构造 ====================
# 渲染由 skillkit.render_html 负责：紧凑分隔符 + `</` 转义 + default=str，
# 这三项由 main() 传给 cli(...) 的参数保持与历史产物逐字节一致。
def mk(*, title, subtitle, module, intro, scene, steps, explain, answer,
       console=None, counters=None, pills=None, **top):
    d = {
        "title": title, "subtitle": subtitle, "module": module, "intro": intro,
        "scene": scene, "steps": list(steps or []),
        "console": console or {"params": [], "readouts": [], "lights": [], "constant": None},
        "explain": explain or [], "answer": answer,
        "counters": counters or {}, "pills": pills or [],
    }
    d.update(top)
    return d


# ==================== 控制台 DSL ====================
def PARAM(id, label, value, mn=2, mx=100000, step=1, unit=""):
    return {"id": id, "label": label, "value": value, "min": mn, "max": mx,
            "step": step, "unit": unit}


def READ(id, label, expr, color="#0f766e"):
    return {"id": id, "label": label, "expr": expr, "color": color}


def LIGHT(id, label, expr):
    return {"id": id, "label": label, "expr": expr}


def cx_console(big, n0=32, nmax=100000, params=(), reads=(), lights=(),
               constant=None, extra_pills=None):
    """通用「复杂度控制台」：拖动规模 n，实时看操作数 / 耗时 / 相对线性的倍数。"""
    ps = [PARAM("n", "问题规模 n", n0, 2, nmax, 1)] + list(params)
    rs = [READ("ops", f"本算法操作数 · {big}", big, "#0f766e"),
          READ("lin", "线性 O(n) 作参照", "n", "#0ea5e9"),
          READ("sec", "按 1e8 次/秒 折算的秒数", "ops/1e8", "#b45309")] + list(reads)
    lt = [LIGHT("slow", "规模已进入不划算区", "ops > 5e7")] + list(lights)
    cst = constant or {"label": "相对线性算法的倍数", "expr": "ops/n",
                       "note": "n 越大、这个倍数涨得越快，就是「复杂度的代价」"}
    return {"params": ps, "readouts": rs, "lights": lt, "constant": cst}


def STATIC(console=None, params=(), reads=(), lights=(), constant=None):
    """静态场景（无步骤序列）的控制台。"""
    return {"params": list(params), "readouts": list(reads),
            "lights": list(lights), "constant": constant}


def STATIC_STEPS(note):
    return [{"note": note}]


def pill(text, color="#0f766e", bg="#f0fdfa"):
    return {"text": text, "color": color, "bg": bg}


def _c(d, k):
    return (d or {}).get(k, 0)


# ==================== ① 算法可视化 ====================
ARR = [5, 3, 8, 1, 9, 2, 7, 4]


def build_sort_bubble():
    r = K.bubble_sort(ARR)
    return mk(
        title="冒泡排序：把最大的逐步「冒」到末尾",
        subtitle=f"数组 [{', '.join(map(str, ARR))}] · 实测比较 {_c(r['counters'],'compare')} 次",
        module="① 算法可视化",
        intro="相邻两个数两两比较，大的就交换。一趟走完，最大的数一定已经沉到末尾，"
              "下一趟就不用再管它了。逐帧回放可以看到：橙色是正在比较的一对，"
              "玫红色是刚刚交换的一对，青色是已经最终就位的元素。",
        scene=dict(kind="bars", caption="数组 · 相邻比较与交换"),
        steps=r["steps"], counters=r["counters"],
        console=cx_console("n*(n-1)/2", n0=len(ARR), nmax=2000),
        explain=[
            {"h": "① 一趟冒泡",
             "body": "从左往右把相邻元素两两比较，只要左边比右边大就交换。"
                     "这一趟一定能把当前区间最大的数推到最右边。"},
            {"h": "② 就位一个",
             "body": f"本例共交换 {_c(r['counters'],'swap')} 次、比较 "
                     f"{_c(r['counters'],'compare')} 次。每结束一趟，"
                     "右侧青色区域就多一个「已就位」的元素，下次不必再进区间。"},
            {"h": "③ 复杂度从哪来",
             "body": "第一趟比 n−1 次，第二趟 n−2 次……总和是 $\\frac{n(n-1)}{2}$，"
                     "所以最坏与平均都是 $O(n^2)$。"},
        ],
        answer=f"排序完成：{sorted(ARR)}。冒泡是稳定排序，"
               f"实测比较 {_c(r['counters'],'compare')} 次、交换 {_c(r['counters'],'swap')} 次。",
        pills=[pill("O(n²)", "#be123c", "#fff1f2"), pill("稳定", "#0f766e")],
    )


def build_sort_merge():
    arr = [5, 3, 8, 1, 9, 2, 7, 4]
    r = K.merge_sort(arr)
    return mk(
        title="归并排序：先对半拆开，再有序地合回来",
        subtitle=f"数组 [{', '.join(map(str, arr))}] · 实测比较 {_c(r['counters'],'compare')} 次",
        module="① 算法可视化",
        intro="分治的典型：把数组一路对半拆到只剩单个元素（天然有序），"
              "再把两个有序段合并成一个更长的有序段。回放里可以看到"
              "蓝框标出的「当前正在合并的区间」。",
        scene=dict(kind="bars", caption="数组 · 分治与归并区间"),
        steps=r["steps"], counters=r["counters"],
        console=cx_console("n*lg(n)", n0=len(arr), nmax=100000),
        explain=[
            {"h": "① 拆",
             "body": "不断对半划分，直到每段长度为 1 —— 长度为 1 的段天然有序，这是递归的出口。"},
            {"h": "② 并",
             "body": "两个有序段各放一个指针，每次取较小的那个写回。"
                     f"本例共比较 {_c(r['counters'],'compare')} 次，每一层合并的总代价都是 $O(n)$。"},
            {"h": "③ 为什么是 n log n",
             "body": "拆的深度是 $\\log_2 n$ 层，每层都要做总计 $O(n)$ 的合并，"
                     "所以总代价 $O(n\\log n)$ —— 比冒泡的 $O(n^2)$ 快一个数量级。"},
        ],
        answer=f"排序完成：{sorted(arr)}。归并是稳定排序，复杂度 $O(n\\log n)$，"
               f"实测比较 {_c(r['counters'],'compare')} 次。",
        pills=[pill("O(n log n)", "#0f766e"), pill("稳定", "#0f766e")],
    )


def build_sort_quick():
    arr = [5, 3, 8, 1, 9, 2, 7, 4]
    r = K.quick_sort(arr)
    return mk(
        title="快速排序：选个枢轴，把小的左边大的右边",
        subtitle=f"数组 [{', '.join(map(str, arr))}] · 实测比较 {_c(r['counters'],'compare')} 次",
        module="① 算法可视化",
        intro="每轮挑一个枢轴，把区间重排成「左边都 ≤ 枢轴、右边都 > 枢轴」，"
              "枢轴就此落定，再对左右两半递归。回放中红字标出枢轴，"
              "蓝框是当前正在处理的区间。",
        scene=dict(kind="bars", caption="数组 · 枢轴划分"),
        steps=r["steps"], counters=r["counters"],
        console=cx_console("n*lg(n)", n0=len(arr), nmax=100000,
                           reads=[READ("worst", "最坏情况退化到", "n*(n-1)/2", "#e11d48")],
                           constant={"label": "分裂得越均匀越快", "expr": "lg(n)",
                                     "note": "理想时每次对半分，深度 log₂n；退化时只分出 1 个，深度 n"},
                           ),
        explain=[
            {"h": "① 选枢轴",
             "body": "本例取区间最后一个元素作枢轴。枢轴是这一轮的「裁判」，"
                     "它最后会停在排好后自己的位置上。"},
            {"h": "② 一次划分",
             "body": f"从左找比枢轴大的、从右找比枢轴小的，找到就交换，两边相遇时把枢轴换过来。"
                     f"本例比较 {_c(r['counters'],'compare')} 次、交换 {_c(r['counters'],'swap')} 次。"},
            {"h": "③ 平均 O(n log n)，最坏 O(n²)",
             "body": "每次对半分就是 $O(n\\log n)$；若每次只分出一个（数组已有序又取端点），"
                     "退化成 $O(n^2)$ —— 这就是实际实现要随机化枢轴的原因。"},
        ],
        answer=f"排序完成：{sorted(arr)}。快速排序通常原地、不稳定，"
               f"平均 $O(n\\log n)$，实测比较 {_c(r['counters'],'compare')} 次。",
        pills=[pill("平均 O(n log n)", "#0f766e"), pill("原地 · 不稳定", "#b45309", "#fffbeb")],
    )


def build_search_binary():
    arr = [1, 3, 5, 8, 12, 17, 24, 31, 38]
    target = 24
    r = K.binary_search(arr, target)
    pos = r.get("pos")
    return mk(
        title="二分查找：每次砍掉一半",
        subtitle=f"有序数组 [{', '.join(map(str, arr))}] · 找 {target}",
        module="① 算法可视化",
        intro="数组必须**有序**。每次取中点与目标比较：相等就命中，"
              "目标更大就丢掉左半边，否则丢掉右半边。回放里蓝框标出"
              "「还可能藏着答案」的区间，mid 指向中点。",
        scene=dict(kind="bars", caption="有序数组 · 区间对半收缩", target=target),
        steps=r["steps"], counters=r["counters"], target=target,
        console=cx_console("lg(n)", n0=len(arr), nmax=10 ** 9,
                           reads=[READ("linmax", "线性查找要比较的次数上界", "n", "#0ea5e9"),
                                  READ("gap", "二分相对线性省下", "n-ops", "#0f766e")],
                           constant={"label": "10 亿里找一个最多几次", "expr": "lg(1e9)",
                                     "note": "log₂(10⁹) ≈ 30，这就是二分的力量"},
                           ),
        explain=[
            {"h": "① 取中点",
             "body": "令 $lo=0, hi=n-1$，取 $mid=\\lfloor (lo+hi)/2 \\rfloor$。"
                     "蓝框就是 $[lo, hi]$，答案只可能在里面。"},
            {"h": "② 砍一半",
             "body": "若 $a[mid] < target$，则 $lo=mid+1$（左半连同 mid 都不可能有答案）；"
                     "反之 $hi=mid-1$。每一步区间长度至少减半。"},
            {"h": "③ 代价",
             "body": "区间长度 $n \\to n/2 \\to n/4 \\to \\cdots \\to 1$，"
                     "最多 $\\lceil \\log_2 n\\rceil + 1$ 步。"
                     f"本例实测比较 {_c(r['counters'],'compare')} 次。"},
        ],
        answer=(f"在第 {_c(r['counters'],'compare')} 次比较时命中，下标 {pos}（值 {target}）。"
                if pos is not None else f"未找到 {target}。")
               + f"复杂度 $O(\\log n)$，线性查找则需最多 {len(arr)} 次。",
        pills=[pill("O(log n)", "#0f766e"), pill("要求有序", "#b45309", "#fffbeb")],
    )


def build_complexity():
    kinds = ["1", "logn", "n", "nlogn", "n2", "n3", "2n"]
    nmax = 32
    g = K.growth_values(kinds, nmax)
    series = [{"label": g[k]["label"], "values": g[k]["values"]} for k in kinds]
    return mk(
        title="复杂度曲线：同一台机器，不同「增长速度」差多少",
        subtitle=f"横轴 n = 1 … {nmax}，纵轴是操作数的相对量级",
        module="① 算法可视化",
        intro="把常见复杂度画在同一张图上。拖动 n 看它们在同一点的读数差："
              "O(n²) 是 O(n log n) 的多少倍？O(2ⁿ) 为什么在几十以后就完全没法用？",
        scene=dict(kind="curve", caption="增长曲线对比", series=series, nmax=nmax),
        steps=STATIC_STEPS("静态对照：曲线由 growth_values 精确算出"),
        console=STATIC(
            params=[PARAM("n", "规模 n", 32, 1, 1000, 1)],
            reads=[READ("lin", "O(n)", "n", "#0ea5e9"),
                   READ("nlogn", "O(n log n)", "n*lg(n)", "#0f766e"),
                   READ("n2", "O(n²)", "n*n", "#f59e0b"),
                   READ("n3", "O(n³)", "n*n*n", "#e11d48"),
                   READ("exp", "O(2ⁿ)", "Math.pow(2,n)", "#8b5cf6")],
            lights=[LIGHT("boom", "O(2ⁿ) 已爆表", "Math.pow(2,n) > 1e9"),
                    LIGHT("heavy", "O(n²) 已超 10⁷", "n*n > 1e7")],
            constant={"label": "n² 相对 n log n 的倍数", "expr": "n*n/(n*lg(n))",
                      "note": "这个比值就是「换一个更好的算法」能赚到的便宜"},
        ),
        explain=[
            {"h": "① 常数阶 O(1)",
             "body": "无论 n 多大，操作数不变 —— 数组按下标取值、哈希查表（平均）。"},
            {"h": "② 对数 O(log n) 与线性 O(n)",
             "body": "二分查找是 $\\log n$，线性扫描是 $n$。n=10⁶ 时前者约 20 次、后者要 100 万次。"},
            {"h": "③ n log n 与 n²",
             "body": "归并/快排的 $n\\log n$ 与冒泡的 $n^2$，在 n=10⁵ 时差约 17 倍，"
                     "n=10⁶ 时差约 170 倍 —— 差距随 n **持续拉大**，这就是复杂度的意义。"},
            {"h": "④ 指数 O(2ⁿ)",
             "body": "n=50 时 $2^{50}\\approx 1.1\\times10^{15}$，按 10⁸ 次/秒要跑 130 天；"
                     "n=100 则远远超过宇宙年龄量级。指数级是「能不能算」的分界线。"},
        ],
        answer="复杂度比较的是**增长趋势**，不是某一点的绝对值：n 越大，高阶的那个一定被甩开。",
        pills=[pill("看增长趋势", "#0f766e")],
    )


# ==================== ② 数据结构 ====================
def build_stack_lifo():
    ops = [("push", 3), ("push", 1), ("push", 4), ("pop",), ("push", 2)]
    r = K.stack_demo(ops)
    return mk(
        title="栈：只能从顶上进出（后进先出）",
        subtitle=f"执行 {len(ops)} 次 push/pop",
        module="② 数据结构",
        intro="栈只允许在一端（栈顶）插入和删除：最后放进去的必须最先出来。"
              "回放里青色格子是当前栈顶，右侧 op 显示正在执行的操作。",
        scene=dict(kind="linear", caption="栈 · 顶进顶出", rule="后进先出 LIFO"),
        steps=r["steps"], counters=r["counters"],
        console=STATIC(
            params=[PARAM("cap", "栈的容量上限", 8, 1, 32, 1, " 格")],
            reads=[READ("used", "本例用到的深度", "4", "#0f766e"),
                   READ("rest", "还剩多少空位", "cap-4", "#0ea5e9")],
            lights=[LIGHT("full", "会溢出（栈满）", "cap < 4")],
            constant={"label": "进出规则", "expr": "'最后进的最先出'",
                      "note": "顺序被固定死了 —— 这既是限制，也是栈可用的原因"},
        ),
        explain=[
            {"h": "① push：压栈",
             "body": "把新元素放到栈顶之上，栈顶指针上移。"},
            {"h": "② pop：出栈",
             "body": "取走栈顶元素，栈顶指针下移。**不能**跳过栈顶去取中间的。"},
            {"h": "③ 为什么要这样设计",
             "body": "「后进先出」正好匹配**嵌套**结构：函数调用、括号匹配、撤销操作、"
                     "表达式求值、深度优先搜索，都靠它。"},
        ],
        answer="栈内变化完整记录在左中两栏；记住一句话：栈是「一条道走到头，再原路返回」。",
        pills=[pill("LIFO", "#0f766e"), pill("O(1) 进出", "#0ea5e9", "#f0f9ff")],
    )


def build_queue_fifo():
    ops = [("enq", 3), ("enq", 1), ("enq", 4), ("deq",), ("enq", 2)]
    r = K.queue_demo(ops)
    return mk(
        title="队列：尾巴进、头出（先进先出）",
        subtitle=f"执行 {len(ops)} 次 enqueue/dequeue",
        module="② 数据结构",
        intro="队列两端分工明确：只能在队尾入队、在队头出队。"
              "最早进来的人最早出去 —— 排队买票的模型。",
        scene=dict(kind="linear", caption="队列 · 尾进头出", rule="先进先出 FIFO"),
        steps=r["steps"], counters=r["counters"],
        console=STATIC(
            params=[PARAM("cap", "队列容量", 8, 1, 32, 1, " 格")],
            reads=[READ("used", "本例用到的长度", "4", "#0f766e"),
                   READ("rest", "还剩多少空位", "cap-4", "#0ea5e9")],
            lights=[LIGHT("full", "会溢出（队满）", "cap < 4")],
            constant={"label": "进出规则", "expr": "'最早进的最早出'",
                      "note": "与栈正好相反 —— 选哪个取决于要不要「嵌套回溯」"},
        ),
        explain=[
            {"h": "① enqueue：入队",
             "body": "加到队尾，tail 后移。"},
            {"h": "② dequeue：出队",
             "body": "从队头取走，head 后移。**不能**从队尾出。"},
            {"h": "③ 用在哪里",
             "body": "排队、消息缓冲、BFS（广度优先搜索按层扩展）、"
                     "生产者—消费者模型，都要「先来先服务」。"},
        ],
        answer="队列保证了**顺序公平**；栈保证了**能原路回溯**。两者都是 O(1) 进出。",
        pills=[pill("FIFO", "#0f766e"), pill("BFS 的底座", "#0ea5e9", "#f0f9ff")],
    )


def build_linked_list():
    vals = [10, 20, 30]
    r = K.linked_list_demo(vals, insert_after=0, value=15, delete_index=1)
    return mk(
        title="单链表：靠指针串起来，插入删除不用搬数据",
        subtitle="10 → 20 → 30，先在下标 0 后面插入 15，再删掉 20",
        module="② 数据结构",
        intro="链表的每个结点存「数据 + 下一个结点的地址」，只要改指针就能"
              "插入或删除，不必像数组那样整体搬移。回放里能看到 head 指针"
              "与每个结点的 next 指向：先插入 15（两步改指针），再删掉 20。",
        scene=dict(kind="linked", caption="单链表 · 指针重连"),
        steps=r["steps"], counters=r["counters"],
        console=STATIC(
            params=[PARAM("pos", "想访问第 k 个元素（0 起）", 1, 0, 20, 1)],
            reads=[READ("hops", "需要走几跳", "pos", "#0f766e"),
                   READ("arr", "数组取同样的元素要几次", "1", "#0ea5e9")],
            lights=[LIGHT("slow", "链表明显更慢", "pos > 8")],
            constant={"label": "链表 vs 数组", "expr": "'改指针 O(1)（已知位置）· 随机访问 O(n)'",
                      "note": "数组反过来：随机访问 O(1)，中间插入要搬 O(n) 个元素"},
        ),
        explain=[
            {"h": "① 建表",
             "body": f"把 {vals} 逐个挂上去，head 指向第一个结点，末尾的 next 是 null（∅）。"},
            {"h": "② 插入：改两个指针，且顺序不能反",
             "body": "第一步让新结点 15 的 next 指向后继（20）；第二步才让前驱（10）的 next 指向 15。"
                     "**若先改前驱，后继就找不到了** —— 这是链表插入最经典的坑。"},
            {"h": "③ 删除：让前驱越过它",
             "body": "删除 20 就是把 15 的 next 直接连到 30。"
                     "若删的是**头结点**，没有前驱可改，就得移动 head 指针 —— 所以工程上常加一个"
                     "「哑结点（dummy head）」把表头情况统一掉。"},
        ],
        answer="链表插入/删除只改 O(1) 个指针（前提是已拿到前驱），但代价是**不能按下标直达**："
               "找第 k 个必须从 head 走 k 步，O(n)。",
        pills=[pill("插入/删除 O(1)*", "#0f766e"), pill("访问 O(n)", "#b45309", "#fffbeb")],
    )


def build_tree_traversal():
    vals = [4, 2, 6, 1, 3, 5, 7]
    r = K.binary_tree_traversals(vals)
    orders = r["orders"]
    steps = r["steps"]["in"]
    seq = [vals[i] for i in orders["in"]]
    return mk(
        title="二叉树的三种遍历：左根右的顺序游戏",
        subtitle=f"完全二叉树（层序给值 {vals}） · 演示中序遍历",
        module="② 数据结构",
        intro="遍历就是「每个结点都访问一次，但访问顺序不同」。三种顺序只差"
              "「根」的位置：前序=根左右、中序=左根右、后序=左右根。"
              "回放逐个点亮访问过的结点。",
        scene=dict(kind="tree", caption="二叉树 · 中序遍历",
                   nodes=r["nodes"], pos=r["pos"],
                   orders=orders, names=r["names"], traversal="in"),
        steps=steps,
        console=STATIC(
            params=[PARAM("depth", "树的深度", 3, 1, 20, 1)],
            reads=[READ("cnt", "结点数 2^d − 1", "Math.pow(2,depth)-1", "#0f766e"),
                   READ("leaf", "叶子数 2^(d−1)", "Math.pow(2,depth-1)", "#0ea5e9")],
            lights=[LIGHT("full", "满二叉树", "true")],
            constant={"label": "中序遍历的结果", "expr": "'1 → 2 → 3 → 4 → 5 → 6 → 7'",
                      "note": "对二叉搜索树做中序遍历，一定得到有序序列"},
        ),
        explain=[
            {"h": "① 前序（根→左→右）",
             "body": "先处理根，适合**复制一棵树**（先建根再递归建子树）。"
                     f"本树结果：{[vals[i] for i in orders['pre']]}"},
            {"h": "② 中序（左→根→右）",
             "body": f"本回放演示的就是它：{seq}。对二叉搜索树来说，中序遍历的结果"
                     "**一定是升序**的 —— 这也是检验 BST 的常用手段。"},
            {"h": "③ 后序（左→右→根）",
             "body": f"最后才处理根：{[vals[i] for i in orders['post']]}。"
                     "适合**释放/销毁**（先拆子树再拆根）或统计子树汇总值。"},
        ],
        answer=f"中序遍历访问顺序：{seq}。三种遍历都是 O(n)，只是「根」的处理时机不同。",
        pills=[pill("O(n)", "#0f766e"), pill("递归天然契合", "#0ea5e9", "#f0f9ff")],
    )


def build_bst_search():
    vals = [4, 2, 7, 1, 3, 6, 9]
    target = 6
    r = K.bst_insert(vals, target=target)
    return mk(
        title="二叉搜索树：左小右大，查找走一条路",
        subtitle=f"插入序列 {vals} · 查找 {target}",
        module="② 数据结构",
        intro="BST 的约定：每个结点左子树都比它小、右子树都比它大。"
              "于是查找时每次比较都能干掉一整棵子树。回放里青色路径"
              "就是从根走到目标的比较链。",
        scene=dict(kind="tree", caption="二叉搜索树 · 比较路径",
                   nodes=r["nodes"], pos=r["pos"]),
        steps=r["steps"], counters=r["counters"], target=target,
        console=STATIC(
            params=[PARAM("n", "树中结点数 n", len(vals), 1, 100000, 1)],
            reads=[READ("h", "树高（最坏）", "n", "#e11d48"),
                   READ("hb", "平衡时树高", "lg(n)", "#0f766e"),
                   READ("steps", "平衡时最多比较", "lg(n)", "#0ea5e9")],
            lights=[LIGHT("skew", "退化成链表", "n > 1000")],
            constant={"label": "平衡时的比较次数", "expr": "lg(n)",
                      "note": "退化时变成 n —— 这就是要有 AVL/红黑树的原因"},
        ),
        explain=[
            {"h": "① 三条不变量",
             "body": "对任意结点 x：左子树所有值 < x < 右子树所有值；"
                     "左、右子树各自也是 BST。"},
            {"h": "② 查找只走一条路",
             "body": f"每比较一次，整棵子树都不用看了。本例查找 {target} 只比较了 "
                     f"{_c(r['counters'],'compare')} 次（含插入过程）。"},
            {"h": "③ 平衡才快",
             "body": "若插入序列有序，BST 会退化成一条链，查找退回 O(n)。"
                     "工程上因此使用自平衡树（AVL、红黑树）。"},
        ],
        answer=f"查找 {target} 命中，比较路径 {' → '.join(map(str, r.get('found') or []))}。"
               f"平衡时复杂度 $O(\\log n)$，最坏 $O(n)$。",
        pills=[pill("平均 O(log n)", "#0f766e"), pill("需保持平衡", "#b45309", "#fffbeb")],
    )


def build_min_heap():
    arr = [3, 1, 4, 1, 5, 9, 2]
    r = K.heap_demo(arr, pop_count=2)
    return mk(
        title="最小堆：数组里住着一棵完全二叉树",
        subtitle=f"依次插入 {arr}，再弹出 2 次堆顶",
        module="② 数据结构",
        intro="堆用数组存储：下标 i 的孩子是 2i+1、2i+2。最小堆保证堆顶"
              "永远是最小值，但**只保证堆顶有序**，不是整表有序。"
              "回放可以看到插入时的「上浮」与弹出后的「下沉」。",
        scene=dict(kind="tree", caption="最小堆（数组下标即树形）",
                   caption2="下标 i 的孩子是 2i+1 / 2i+2"),
        steps=r["steps"], counters=r["counters"],
        console=STATIC(
            params=[PARAM("n", "堆中元素个数", len(arr), 1, 100000, 1)],
            reads=[READ("h", "树高 ≈ log₂n", "lg(n)", "#0f766e"),
                   READ("peek", "取最小值只需", "1", "#0ea5e9"),
                   READ("sort", "全部弹出排完序要", "n*lg(n)", "#b45309")],
            lights=[LIGHT("big", "已属大规模", "n > 65536")],
            constant={"label": "堆顶性质", "expr": "'堆顶一定是当前最小值'",
                      "note": "只维护「父子有序」这一条局部约束，代价就只有 log n"},
        ),
        explain=[
            {"h": "① 上浮（插入）",
             "body": "新元素放在数组末尾（树的最后一个叶子），若比父节点小就不断与父交换，"
                     "直到满足最小堆性质。最多走上树高 $\\log n$ 层。"},
            {"h": "② 下沉（弹出堆顶）",
             "body": "把末尾元素放到堆顶，再与**较小的**那个孩子反复交换，直到落定。"},
            {"h": "③ 用来做什么",
             "body": "优先队列（任务调度、Dijkstra 取最小 dist）、堆排序、"
                     "求 Top-K / 中位数 —— 都靠「$O(1)$ 取极值、$O(\\log n)$ 更新」。"},
        ],
        answer=f"弹出 2 次堆顶得到 {r.get('popped')}。建堆 $O(n)$，每次插入/弹出 $O(\\log n)$；"
               "堆只保证**堆顶最小**，其余元素之间毫无顺序 —— 这正是它比排序便宜的原因。",
        pills=[pill("取极值 O(1)", "#0f766e"), pill("插入/弹出 O(log n)", "#0ea5e9", "#f0f9ff")],
    )


def build_hash_table():
    keys = [10, 22, 31, 15, 7]
    r = K.hash_table_demo(keys, size=5)
    return mk(
        title="哈希表：用算式直接算出位置",
        subtitle=f"h(k) = k mod 5 · 插入 {keys}",
        module="② 数据结构",
        intro="哈希表用哈希函数把键映射到桶下标，理想情况下 O(1) 直达。"
              "但不同的键可能算出同一个下标 —— 这就是冲突。本例用"
              "**链地址法**：同一个桶挂一条链表。",
        scene=dict(kind="table", mode="buckets", caption="哈希表 · 链地址法"),
        steps=r["steps"], counters=r["counters"],
        console=STATIC(
            params=[PARAM("size", "桶个数 size", 5, 1, 100, 1),
                    PARAM("key", "要插入的键 k", 7, 0, 9999, 1)],
            reads=[READ("slot", "h(k) = k mod size", "key % size", "#0f766e"),
                   READ("load", "装填因子 α = 键数/桶数", "5/size", "#0ea5e9"),
                   READ("avg", "平均链长（≈ α）", "5/size", "#b45309")],
            lights=[LIGHT("clash", "本次会撞车", "(key % size) == 0"),
                    LIGHT("dense", "α > 1，链已很长", "5/size > 1")],
            constant={"label": "哈希的意义", "expr": "'平均 O(1)，不依赖元素顺序'",
                      "note": "数组要 O(n) 扫，有序数组要 O(log n) 查 —— 哈希直接算出来"},
        ),
        explain=[
            {"h": "① 哈希函数",
             "body": "本例 $h(k) = k \\bmod 5$。好哈希要**快、均匀、确定**："
                     "同一个键永远落在同一个桶。"},
            {"h": "② 冲突不可避免",
             "body": f"5 mod 5 = 0 与 10 mod 5 = 0 撞在一起。由抽屉原理，"
                     "桶数少于键数时**一定**有冲突。本例冲突 "
                     f"{_c(r['counters'],'collision')} 次。"},
            {"h": "③ 链地址法",
             "body": "冲突的键挂到同一条链尾部。装填因子 $\\alpha$ 越大链越长："
                     "$\\alpha \\le 1$ 时接近 O(1)，$\\alpha \\gg 1$ 时退化成链表 O(n)。"},
        ],
        answer=f"插入完成：桶内分布 {[b for b in r['steps'][-1]['buckets']]}。"
               f"平均 O(1)，最坏 O(n)；工程上靠扩容把 α 控制在 1 以下。",
        pills=[pill("平均 O(1)", "#0f766e"), pill("不保持顺序", "#b45309", "#fffbeb")],
    )


# ==================== ③ 图算法 ====================
GN = ["a", "b", "c", "d", "e", "f"]
GE = [("a", "b"), ("a", "c"), ("b", "d"), ("c", "e"), ("d", "f")]


def build_bfs():
    r = K.bfs(GN, GE, "a")
    return mk(
        title="广度优先搜索 BFS：一层一层往外扩",
        subtitle="从 a 出发 · 队列驱动",
        module="③ 图算法",
        intro="BFS 用队列保证「先访问近的、后访问远的」，因此第一次到达"
              "某个结点时走的一定是最少边数的路。回放里青色=已访问，"
              "紫色=刚入队，黄色=正在处理的队头。",
        scene=dict(kind="graph", caption="无权图 · BFS 扩展",
                   pos=r["pos"], edges=r["edges"]),
        steps=r["steps"], counters=r["counters"], order=r["order"],
        console=STATIC(
            params=[PARAM("d", "图的层数（层数=最短跳数）", 3, 0, 20, 1)],
            reads=[READ("layer", "最宽一层有多少结点（队列峰值）", "Math.pow(2,d)", "#e11d48"),
                   READ("total", "结点总数 2^(d+1)−1", "Math.pow(2,d+1)-1", "#0f766e"),
                   READ("time", "每个结点只进出队一次", "Math.pow(2,d+1)-1", "#0ea5e9")],
            lights=[LIGHT("wide", "队列会很宽 —— 这就是 BFS 的软肋", "Math.pow(2,d) > 1024")],
            constant={"label": "本例实际访问顺序", "expr": "'a → b → c → d → e → f'",
                      "note": "BFS 的访问顺序 = 到起点的最少边数从小到大"},
        ),
        explain=[
            {"h": "① 队列驱动",
             "body": "起点入队 → 取队头 → 把它所有未访问邻居入队 → 标记已访问 → 重复。"
                     "队列保证了**按层扩展**。"},
            {"h": "② 时间复杂度",
             "body": "每个结点入队、出队各一次 O(V)，每条边被看常数次 O(E)，"
                     "总计 $O(V+E)$ —— 邻接表表示下的线性复杂度。"},
            {"h": "③ 关键性质：无权图最短路",
             "body": "**第一次**访问到某结点时经过的边数最少。若要带权最短路，"
                     "得换 Dijkstra 或 Bellman-Ford。"},
        ],
        answer=f"BFS 访问顺序：{' → '.join(r['order'])}。$O(V+E)$，"
               "同时得到起点到所有结点的最少边数。",
        pills=[pill("O(V+E)", "#0f766e"), pill("无权最短路", "#0ea5e9", "#f0f9ff")],
    )


def build_dijkstra():
    nodes = ["a", "b", "c", "d"]
    edges = [("a", "b", 2), ("a", "c", 5), ("b", "c", 1), ("c", "d", 3)]
    r = K.dijkstra(nodes, edges, "a")
    return mk(
        title="Dijkstra：每次锁定当前最近的那个点",
        subtitle="带权图 · 从 a 出发求到各点的最短距离",
        module="③ 图算法",
        intro="维护 dist[]（起点到各点的当前已知最短距离），每轮从未确定的点里"
              "挑 dist 最小的锁定，再用它去「松弛」邻居。前提是**边权非负**。",
        scene=dict(kind="graph", caption="带权图 · Dijkstra 松弛",
                   pos=r["pos"], edges=r["edges"]),
        steps=r["steps"], counters=r["counters"],
        console=STATIC(
            params=[PARAM("w", "把 a→c 这条边的权改成 w", 5, 1, 20, 1)],
            reads=[READ("viaC", "直走 a→c→d 的代价", "5+3", "#0ea5e9"),
                   READ("viaB", "实际最短路 a→b→c→d", "2+1+3", "#0f766e"),
                   READ("ifsmall", "若把 a→c 改小成 w", "w+3", "#b45309")],
            lights=[LIGHT("shorter", "改小后 a→c→d 才更优", "w+3 < 2+1+3")],
            constant={"label": "a 到 d 的最短距离", "expr": str(r["dist"]["d"]),
                      "note": "路径 a→b→c→d：绕道反而更短，因为直连边 a→c 的权 5 太大"},
        ),
        explain=[
            {"h": "① 三步循环",
             "body": "（1）在未确定的点中取 dist 最小者 u；（2）把 u 标为已确定；"
                     "（3）对 u 的每条边做松弛：$dist[v] = \\min(dist[v], dist[u]+w(u,v))$。"},
            {"h": "② 为什么贪心是对的",
             "body": "边权非负时，dist 最小的未确定点**不可能**再被更短的路更新 —— "
                     "所以可以直接锁定。若存在负权边，这个前提就崩了（要 Bellman-Ford）。"},
            {"h": "③ 复杂度",
             "body": "朴素实现 $O(V^2)$；用二叉堆优化后 $O((V+E)\\log V)$，"
                     "本例松弛了 " + str(_c(r['counters'], 'relax')) + " 次。"},
        ],
        answer="最短距离：" + "，".join(
            f"{k}={v}" for k, v in r["dist"].items())
            + f"。总代价 $O((V+E)\\log V)$，松弛 {_c(r['counters'], 'relax')} 次。",
        pills=[pill("非负权", "#0f766e"), pill("贪心正确", "#0ea5e9", "#f0f9ff")],
    )


def build_mst():
    nodes = ["a", "b", "c", "d"]
    edges = [("a", "b", 2), ("a", "c", 5), ("b", "c", 1), ("c", "d", 3)]
    r = K.prim_mst(nodes, edges)
    return mk(
        title="Prim 最小生成树：把「树内外最小的边」一条条接进来",
        subtitle=f"连通无向加权图 · 总权 {r.get('total')}",
        module="③ 图算法",
        intro="从任意一点开始，维护一棵生长中的树：每次挑「一端在树内、"
              "另一端在树外」的边里权最小的那条，把外面的点并进来。"
              "直到所有点都在树上。青色就是已选的边。",
        scene=dict(kind="graph", caption="带权图 · Prim 生长",
                   pos=r["pos"], edges=r["edges"]),
        steps=r["steps"], counters=r["counters"],
        console=STATIC(
            params=[PARAM("v", "结点数 V", len(nodes), 2, 10000, 1)],
            reads=[READ("need", "生成树必有的边数 V−1", "v-1", "#0f766e"),
                   READ("cand", "候选边总数", "v*(v-1)/2", "#0ea5e9"),
                   READ("ratio", "实际只需占", "(v-1)/(v*(v-1)/2)*100", "#b45309", )],
            lights=[LIGHT("tiny", "稠密图中只需极少边", "v > 100")],
            constant={"label": "本例选了几条边", "expr": "3",
                      "note": "4 个点的生成树一定是 3 条边（V−1），多一条成环、少一条不连通"},
        ),
        explain=[
            {"h": "① 关键约束",
             "body": "候选边必须**跨在树的边界上**：一端已连通、另一端还没。"
                     "这样永远不会成环。"},
            {"h": "② 贪心为什么对",
             "body": "**切割性质**：把顶点分成「树内/树外」两半，横跨两边的最小权边"
                     "一定属于某棵最小生成树。所以每步取最小是安全的。"},
            {"h": "③ 复杂度与姊妹算法",
             "body": "堆优化后 $O((V+E)\\log V)$；稀疏图用 Prim，"
                     "稀疏且边已排序可用 Kruskal（并查集，$O(E\\log E)$）。"},
        ],
        answer=f"最小生成树总权 = {r.get('total')}，"
               "选边 " + str(_c(r['counters'], 'edge')) + " 条（= V−1）。生成树必连通、必无环。",
        pills=[pill("O((V+E) log V)", "#0f766e"), pill("V−1 条边", "#0ea5e9", "#f0f9ff")],
    )


# ==================== ④ 计算原理 ====================
def build_base_convert():
    value, base = 255, 2
    r = K.base_convert(value, base)
    return mk(
        title=f"进制转换：{value} 怎么变成 {r['result']}",
        subtitle=f"十进制 → {base} 进制 · 短除法",
        module="④ 计算原理",
        intro="任何整数反复除以目标基数，把每次的余数记下来，"
              "最后**倒序**拼接就是答案 —— 因为先得到的余数是最低位。"
              "回放里可以看到每一轮的商与余。",
        scene=dict(kind="bits", mode="convert", caption="短除法 · 除基取余",
                   value=value, base=base, result=r["result"]),
        steps=r["steps"],
        console=STATIC(
            params=[PARAM("value", "十进制数", 255, 0, 65535, 1),
                    PARAM("base", "目标基数", 2, 2, 16, 1)],
            reads=[READ("bits", "至少需要几位", "lg(value+1)", "#0f766e"),
                   READ("reps", "2 的幂能否整除", "value % 2", "#0ea5e9"),
                   READ("asHex", "转十六进制看", "hex(value)", "#b45309")],
            lights=[LIGHT("pow2", "恰好是 2 的幂", "value > 0 && (value & (value-1)) === 0")],
            constant={"label": "位数下界", "expr": "Math.ceil(lg(value+1))",
                      "note": "n 位二进制能表示 0 … 2ⁿ−1，所以位数 = ⌈log₂(值+1)⌉"},
        ),
        explain=[
            {"h": "① 除基取余",
             "body": f"$255 \\div 2 = 127 \\cdots 1$，再拿 127 继续除……"
                     "把余数依次记下。商变成 0 时停止。"},
            {"h": "② 为什么要倒序",
             "body": "第一次得到的余数是**最低位**（最右边），最后一次是最高位。"
                     "所以读的时候要从最后一个余数往回读。"},
            {"h": "③ 位权的视角",
             "body": "255 = 128+64+32+16+8+4+2+1，每位的权是 2 的幂。"
                     f"转成 {base} 进制就是换一套权（{base}⁰, {base}¹, …）。"},
        ],
        answer=f"{value}₁₀ = {r['result']}₍{base}₎，共 {len(r['rems'])} 位。"
               "十六进制只是二进制的紧凑写法（4 位 → 1 位）。",
        pills=[pill("短除法", "#0f766e"), pill("余数倒序", "#0ea5e9", "#f0f9ff")],
    )


def build_bitwise():
    a, b, w = 12, 10, 8
    r = K.bitwise_ops(a, b, w)
    return mk(
        title="位运算：把数摊成 0 和 1 逐位操作",
        subtitle=f"A = {a}，B = {b}（{w} 位）",
        module="④ 计算原理",
        intro="CPU 只认 0 和 1。与/或/异或是逐位独立进行的，"
              "取反和移位则改变整串。拖动 A、B 滑块，"
              "下方读数会实时重算（用的就是同一个位运算表达式）。",
        scene=dict(kind="bits", mode="ops", caption=f"{w} 位逐位对照",
                   rows=r["rows"], width=w),
        steps=STATIC_STEPS("静态对照表：每一行都由位运算精确算出"),
        console=STATIC(
            params=[PARAM("a", "A", a, 0, 255, 1),
                    PARAM("b", "B", b, 0, 255, 1),
                    PARAM("sh", "左移位数 k", 2, 0, 8, 1)],
            reads=[READ("and", "A & B（都有才为 1）", "a&b", "#0f766e"),
                   READ("or", "A | B（有一个就为 1）", "a|b", "#0ea5e9"),
                   READ("xor", "A ^ B（不同才为 1）", "a^b", "#b45309"),
                   READ("inv", "~A（{} 位补码）".format(w), "twos(~a,8)", "#8b5cf6"),
                   READ("shl", "A << k", "(a<<sh)&255", "#e11d48"),
                   READ("pop", "A 里 1 的个数", "pc(a)", "#64748b")],
            lights=[LIGHT("disjoint", "A、B 无公共位", "(a&b) === 0"),
                    LIGHT("same", "A == B", "a === b")],
            constant={"label": "位运算恒等式", "expr": "(a&b) + (a|b) === a + b",
                      "note": "对任意 A、B 都成立：把每一位拆成「都有 / 只有一方有」两类"},
        ),
        explain=[
            {"h": "① 与、或、异或",
             "body": "AND 取交集、OR 取并集、XOR 是「不同为 1」。"
                     "XOR 有个妙处：$A \\oplus A = 0$，$A \\oplus 0 = A$ —— 可以用来"
                     "**无临时变量交换两数**和**校验/纠错**。"},
            {"h": "② 取反与移位",
             "body": f"取反在 {w} 位下要用补码解释（最高位是符号位）；"
                     "$A \\ll k$ 等于乘 $2^k$，$A \\gg k$ 等于除 $2^k$ 取整 —— "
                     "编译器常用移位替代乘除小常数。"},
            {"h": "③ 实际用途",
             "body": "掩码取位、状态标志（权限位）、哈希打散、"
                     "位图（bitmap）、网络字节序，全是位运算的主场。"},
        ],
        answer=f"{a} & {b} = {a & b}，{a} | {b} = {a | b}，{a} ^ {b} = {a ^ b}。"
               f"恒等式 (A&B)+(A|B) = A+B 恒成立。",
        pills=[pill("逐位独立", "#0f766e"), pill("O(1)", "#0ea5e9", "#f0f9ff")],
    )


def build_encoding():
    ch = "A"
    r = K.encode_char(ch)
    return mk(
        title="字符编码：一个字是怎么变成一串字节的",
        subtitle=f"'{ch}' → 码点 {r['codepoint']} → {r['bytes_hex']}",
        module="④ 计算原理",
        intro="字符先查表得到码点（Unicode），再按 UTF-8 规则编码成字节。"
              "ASCII 范围（< 128）的字符 UTF-8 只用 1 个字节，且**与 ASCII 完全相同**"
              "—— 这就是向后兼容。拖动码点看规则怎么变。",
        scene=dict(kind="bits", mode="encode", caption="UTF-8 字节位模式",
                   char=ch, codepoint=r["codepoint"], utf8_bits=r["utf8_bits"],
                   bytes_hex=r["bytes_hex"], nbytes=r["nbytes"], bytes_=r["bytes"]),
        steps=STATIC_STEPS("静态编码表：位模式由 UTF-8 规则精确算出"),
        console=STATIC(
            params=[PARAM("cp", "码点 U+____（0–1114111）", r["codepoint"], 0, 1114111, 1)],
            reads=[READ("nb", "UTF-8 需要的字节数",
                        "cp<0x80?1:cp<0x800?2:cp<0x10000?3:4", "#0f766e"),
                   READ("ascii", "是否就是 ASCII", "cp<0x80", "#0ea5e9"),
                   READ("asHex", "十六进制码点", "hex(cp)", "#b45309"),
                   READ("asBin", "二进制码点", "bin(cp)", "#64748b")],
            lights=[LIGHT("asciiOnly", "ASCII 兼容（1 字节）", "cp<0x80"),
                    LIGHT("bmp", "在基本多文种平面 BMP 内", "cp<0x10000"),
                    LIGHT("astral", "需要 4 字节（emoji 区）", "cp>=0x10000")],
            constant={"label": "本例的字节序列", "expr": "'0x{} → {}'".format(r["bytes_hex"], r["utf8_bits"]),
                      "note": "UTF-8：1 字节 0xxxxxxx；2 字节 110xxxxx 10xxxxxx；"
                              "3 字节 1110xxxx + 2×10xxxxxx；4 字节 11110xxx + 3×10xxxxxx"},
        ),
        explain=[
            {"h": "① 字符 → 码点",
             "body": "Unicode 给全世界每个字符分配一个编号（码点），"
                     f"'{ch}' 的码点是 U+{r['hex'][2:]} = {r['codepoint']}。"},
            {"h": "② 码点 → UTF-8 字节",
             "body": "UTF-8 是**变长**编码：ASCII 1 字节、汉字常用 3 字节、"
                     "emoji 4 字节。首字节的前缀（0xxxxxxx / 110xxxxx / 1110xxxx / 11110xxx）"
                     "直接表明本字符占几字节，因此可以逐字节切分，不会串码。"},
            {"h": "③ 为什么 UTF-8 赢了",
             "body": "兼容 ASCII、自同步、无需字节序、前缀即长度 —— "
                     "今天互联网上超过 98% 的页面用 UTF-8。"},
        ],
        answer=f"'{ch}' 的 UTF-8 就是它的码点本身：{r['utf8_bits']}₂ = 0x{r['bytes_hex']}，"
               f"共 {r['nbytes']} 个字节。",
        pills=[pill(f"{r['nbytes']} 字节", "#0f766e"), pill("变长自同步", "#0ea5e9", "#f0f9ff")],
    )


# ==================== ⑤ 算法思想 ====================
def _call_tree(steps):
    """把朴素递归的调用序列还原成一棵调用树。
    内核每步给 {node:"f3", path:[祖先的值...], calls:第几次调用}；
    值会重复（fib(1) 被调用多次），所以按「最近一次出现」配父子，id 用步号保证唯一。
    """
    nodes, last_of = [], {}
    for i, s in enumerate(steps):
        nid = f"c{i}"
        v = int(s["node"][1:])
        path = list(s.get("path") or [])
        parent = last_of.get(path[-1]) if path else None
        nodes.append({"id": nid, "label": f"f({v})", "parent": parent,
                      "depth": len(path), "val": v})
        last_of[v] = nid
    return nodes


def build_recursion_tree():
    n = 5
    r = K.fib_recursive_calls(n)
    raw = r["steps"]
    tree = _call_tree(raw)
    steps, anc = [], {}
    for i, s in enumerate(raw):
        nid = tree[i]["id"]
        p = tree[i]["parent"]
        chain = ([p] + anc[p]) if p else []      # 完整祖先链（根在后）
        anc[nid] = chain
        steps.append({"node": nid, "path": chain, "note": s["note"]})
    total = r["calls"]
    rep = r.get("repeat") or {}
    return mk(
        title="递归调用树：看清函数是怎么一层层展开的",
        subtitle=f"fib({n}) 的朴素递归 · 共 {total} 次函数调用",
        module="⑤ 算法思想",
        intro="递归 = 自己调用自己 + 一个出口。画成树之后，"
              "每个结点是一次函数调用、每条边是「这次调用了谁」。"
              "回放高亮的绿线就是当前正在展开的调用链，"
              "注意同一个 f(1) 出现了好几次 —— 那就是「重复子问题」。",
        scene=dict(kind="call", caption="fib(n) 的调用树",
                   calls=tree, n=n),
        steps=steps,
        console=STATIC(
            params=[PARAM("n", "递归深度 n", n, 0, 30, 1)],
            reads=[READ("calls", "朴素递归的调用次数", "Math.pow(2,n+1)-1", "#e11d48"),
                   READ("dp", "动态规划只需要", "n", "#0f766e"),
                   READ("ratio", "浪费了多少倍", "(Math.pow(2,n+1)-1)/n", "#b45309")],
            lights=[LIGHT("blow", "调用次数爆炸", "Math.pow(2,n+1)-1 > 1e6")],
            constant={"label": "各子问题被算了几次", "expr": "'见右下统计：值越小被算得越多'",
                      "note": "f(1) 被调用 5 次、f(2) 三次 —— 同一棵子树被反复展开"},
        ),
        explain=[
            {"h": "① 递归的两个要素",
             "body": "**出口**（base case）：$fib(0)=0,\\;fib(1)=1$；"
                     "**递推**：$fib(n)=fib(n-1)+fib(n-2)$。缺一个就会无限下钻，直到栈溢出。"},
            {"h": "② 调用树长什么样",
             "body": f"fib({n}) 展开成 fib({n-1}) 与 fib({n-2})，各自再展开……"
                     f"本例共 {total} 个结点，最深 " + str(max(t['depth'] for t in tree)) + " 层。"},
            {"h": "③ 指数级的病根：重复子问题",
             "body": "调用次数满足 $T(n)=T(n-1)+T(n-2)+1=O(2^n)$。"
                     "本例各子问题被计算的次数：" +
                     "，".join(f"fib({k})×{v}" for k, v in sorted(rep.items(), key=lambda x: int(x[0]))) +
                     "。**同一个子问题被算了好几遍**，这就是记忆化能救的原因。"},
        ],
        answer=f"fib({n}) = {r['result']}，朴素递归展开成 {total} 次函数调用；"
               f"而自底向上的 DP 只需 {n} 次加法。同样的答案，代价差一个数量级。",
        pills=[pill("O(2ⁿ)", "#e11d48", "#fff1f2"), pill("重复子问题", "#0f766e")],
    )


def build_dp_fib():
    n = 6
    r = K.fib_dp(n)
    return mk(
        title="动态规划斐波那契：从底往上，一次都不重算",
        subtitle=f"f({n}) = {r['result']} · 朴素递归要 {r.get('naive_calls')} 次调用",
        module="⑤ 算法思想",
        intro="换个方向：先算 f(0)、f(1)，再一路往后推。"
              "每个格子只填一次，答案出来时整行表都填满了。"
              "回放里青色是刚算出的格、蓝色是它的两个来源。",
        scene=dict(kind="table", mode="dp", caption="一维 DP 表 · 自底向上",
                   title=f"DP 表：f(0) … f({n})", table=[0] * (n + 1)),
        steps=r["steps"], counters=r["counters"], result=r["result"],
        console=STATIC(
            params=[PARAM("n", "求 f(n)", n, 0, 60, 1)],
            reads=[READ("naive", "朴素递归调用次数", "Math.pow(2,n+1)-1", "#e11d48"),
                   READ("dp", "DP 的计算次数", "n", "#0f766e"),
                   READ("ratio", "加速倍数", "Math.pow(2,n+1)-1/n", "#b45309")],
            lights=[LIGHT("blow", "朴素版已不可行", "Math.pow(2,n+1)-1 > 1e7")],
            constant={"label": "状态转移方程", "expr": "'f(n) = f(n-1) + f(n-2)'",
                      "note": "DP 的核心：把问题写成方程 + 明确边界"},
        ),
        explain=[
            {"h": "① 找状态与转移",
             "body": "状态：$f(i)$；转移：$f(i)=f(i-1)+f(i-2)$；边界：$f(0)=0, f(1)=1$。"
                     "**把递归式反过来自底向上填，就是 DP**。"},
            {"h": "② 逐格填表",
             "body": f"本例从 f(0)、f(1) 开始一路推到 f({n})={r['result']}，"
                     f"只用了 {n + 1} 次加法（计数器 {_c(r['counters'], 'add')} 次加法）。"},
            {"h": "③ 两个特征",
             "body": "**重叠子问题**（每个子问题只解一次）+ **最优子结构**"
                     "（大问题的最优解由小问题的最优解拼成）。满足这两条才能用 DP。"},
        ],
        answer=f"f({n}) = {r['result']}，计算 {n + 1} 次；"
               f"朴素递归要 {r.get('naive_calls')} 次 —— 时间从 $O(2^n)$ 降到 $O(n)$。",
        pills=[pill("O(n)", "#0f766e"), pill("空间 O(n) 可优化到 O(1)", "#0ea5e9", "#f0f9ff")],
    )


def _knapsack_pick(weights, values, capacity, table):
    """从 DP 表回溯出具体选了哪几件（返回 1 起编号）。"""
    i, c, picked = len(weights), capacity, []
    while i > 0:
        if table[i][c] != table[i - 1][c]:
            picked.append(i)
            c -= weights[i - 1]
        i -= 1
    return sorted(picked)


def build_dp_knapsack():
    weights = [2, 3, 4]
    values = [3, 4, 5]
    capacity = 5
    r = K.knapsack_dp(weights, values, capacity)
    picked = _knapsack_pick(weights, values, capacity, r["table"])
    tw = sum(weights[i - 1] for i in picked)
    tv = sum(values[i - 1] for i in picked)
    rows = len(weights) + 1
    cols = capacity + 1
    rowLabels = ["∅"] + [f"物品{i+1}(w={weights[i]},v={values[i]})" for i in range(len(weights))]
    colLabels = [f"c={c}" for c in range(cols)]
    return mk(
        title="0-1 背包：每个格子都是一次「拿还是不拿」的抉择",
        subtitle=f"{len(weights)} 件物品 · 容量 {capacity} · 最优值 {r['result']}",
        module="⑤ 算法思想",
        intro="dp[i][c] = 只看前 i 件物品、背包容量为 c 时能装的最大价值。"
              "对第 i 件物品只有两种选择：不拿（等于 i−1 那行），"
              "或者拿（先腾出它的重量，再加它的价值）。取较大者。",
        scene=dict(kind="table", mode="dp", caption="二维 DP 表 · 逐格填写",
                   title=f"dp[i][c] · 行=考虑的物品数，列=剩余容量",
                   rowLabels=rowLabels, colLabels=colLabels,
                   table=[[0] * cols for _ in range(rows)]),
        steps=r["steps"], counters=r["counters"], result=r["result"],
        console=STATIC(
            params=[PARAM("cap", "背包容量 W", capacity, 1, 500, 1)],
            reads=[READ("cells", "要填的格子数", "(3+1)*(cap+1)", "#0f766e"),
                   READ("subs", "穷举子集数 2^3", "Math.pow(2,3)", "#e11d48"),
                   READ("gain", "DP 相对穷举省下", "Math.pow(2,3)-(3+1)*(cap+1)/8", "#b45309")],
            lights=[LIGHT("big", "容量已较大", "cap > 100")],
            constant={"label": "转移方程", "expr": "'dp[i][c] = max(dp[i-1][c], v + dp[i-1][c-w])'",
                      "note": "第二个选择的前半句是「先腾出 w 的空间」—— 这就是 0-1 的精髓"},
        ),
        explain=[
            {"h": "① 定义状态",
             "body": "二维表：行 i = 允许考虑前 i 件物品，列 c = 容量恰好为 c 时的最优值。"
                     "第 0 行（没有物品可选）全为 0。"},
            {"h": "② 写出转移",
             "body": "对第 i 件物品："
                     "$dp[i][c] = \\max\\big(dp[i-1][c],\\; v_i + dp[i-1][c-w_i]\\big)$。"
                     "第二项要求 $c \\ge w_i$，否则拿不了。"},
            {"h": "③ 回溯方案",
             "body": f"本例 {r['result']}：从最后一格往回看是「拿了」还是「没拿」，"
                     "就能还原出具体选了哪几件 —— 表格里蓝色格就是它的来源。"},
        ],
        answer=f"最大价值 {r['result']}：选第 {'、'.join(map(str, picked))} 件"
               f"（重量 {' + '.join(str(weights[i-1]) for i in picked)} = {tw} ≤ {capacity}，"
               f"价值 {' + '.join(str(values[i-1]) for i in picked)} = {tv}）。"
               f"复杂度 $O(nW)$，属伪多项式（$W$ 很大时仍然慢）。",
        pills=[pill("O(nW)", "#0f766e"), pill("伪多项式", "#b45309", "#fffbeb")],
    )


def build_greedy_coins():
    coins = [25, 10, 5, 1]
    amount = 41
    r = K.greedy_coins(coins, amount)
    return mk(
        title="贪心找零：每次先拿最大的面额",
        subtitle=f"面额 {coins} · 要凑 {amount} · 用了 {r.get('count')} 枚",
        module="⑤ 算法思想",
        intro="贪心 = 每一步都做「当下看起来最好」的选择，从不回头。"
              "找零时就是「先拿不超过剩余金额的最大面额」。"
              "回放里可以看到剩余金额的进度条和每种面额已取走的枚数。",
        scene=dict(kind="coins", caption="找零 · 贪心取大面额",
                   coins=coins, amount=amount),
        steps=r["steps"],
        console=STATIC(
            params=[PARAM("amount", "要凑的金额", amount, 1, 999, 1),
                    PARAM("ncoin", "可用面额种数", 4, 1, 4, 1)],
            reads=[READ("left", "当前 amount 除以 25 的余数", "amount % 25", "#e11d48"),
                   READ("by25", "用 25 能拿几枚", "Math.floor(amount/25)", "#0f766e"),
                   READ("worst", "最坏情况几枚（全用 1）", "amount", "#b45309")],
            lights=[LIGHT("clean", "amount 恰好能被 25 整除", "amount % 25 === 0"),
                    LIGHT("ok", "面额含 1，必能凑齐", "ncoin >= 4")],
            constant={"label": "贪心用掉", "expr": "4",
                      "note": "对 [1,5,10,25] 这套面额贪心永远最优 —— 这是「规范硬币系统」的性质"},
        ),
        explain=[
            {"h": "① 贪心的选择",
             "body": "每一步取**不超过剩余金额的最大面额**，然后问题规模变小，重复。"
                     "代码极短、无需建表。"},
            {"h": "② 什么时候对",
             "body": "本例面额 [25,10,5,1] 是**规范（canonical）硬币系统**，贪心恰好最优。"
                     "但换成 [1,3,4] 凑 6：贪心拿 4+1+1 = 3 枚，而 3+3 = 2 枚更优 —— "
                     "**贪心会失手**。"},
            {"h": "③ 失手了怎么办",
             "body": "退回动态规划或回溯：把「子金额的最优解」算出来再组合。"
                     "代价是 O(amount×种类数)，换来的是**保证最优**。"},
        ],
        answer=f"凑 {amount}：用了 {r.get('count')} 枚 {r.get('used')}。"
               f"贪心 $O(n)$ 极快，但只在特定面额体系下保证最优。",
        pills=[pill("O(n) 超快", "#0f766e"), pill("不保证最优", "#e11d48", "#fff1f2")],
    )


def build_greedy_interval():
    tasks = [(1, 3), (2, 5), (4, 6), (5, 7)]
    r = K.greedy_interval(tasks)
    return mk(
        title="区间调度：先按结束时间排序，再一个个收",
        subtitle=f"任务 {tasks} · 最多选 {r.get('count')} 个",
        module="⑤ 算法思想",
        intro="要安排尽可能多的不重叠任务：把它们按**结束时间**从小到大排，"
              "然后从头扫，只要和已选的不冲突就选上。"
              "回放里青色是已选、玫红是因冲突被跳过的。",
        scene=dict(kind="interval", caption="时间轴 · 贪心区间选择", tasks=tasks),
        steps=r["steps"],
        console=STATIC(
            params=[PARAM("n", "任务总数 n", 4, 1, 100000, 1)],
            reads=[READ("sort", "按结束时间排序的比较数", "n*lg(n)", "#b45309"),
                   READ("scan", "扫描一遍的次数", "n", "#0ea5e9"),
                   READ("all", "总代价（排序 + 扫描）", "n*lg(n)+n", "#0f766e")],
            lights=[LIGHT("big", "10 万个任务也只是 nlogn 量级", "n >= 100000"),
                    LIGHT("small", "本例只有 4 个任务", "n <= 4")],
            constant={"label": "关键顺序", "expr": "'必须按结束时间排序，不是按开始时间'",
                      "note": "按开始时间排会先占住长任务，反而少安排 —— 这是本题最反直觉的点"},
        ),
        explain=[
            {"h": "① 为什么按结束时间",
             "body": "越早结束，留给后面的任务空间越大。这是**交换论证**能证明的最优策略："
                     "任何更晚结束的方案都可以换成这个而不变差。"},
            {"h": "② 扫描过程",
             "body": "维护「上一个已选任务的结束时间」，只要当前任务的开始 ≥ 它，"
                     "就选中并更新结束时间；否则跳过。"},
            {"h": "③ 复杂度与推广",
             "body": "排序 $O(n\\log n)$ + 扫描 $O(n)$。"
                     "同样框架还能解：活动选择、区间覆盖、Huffman 编码 —— "
                     "它们的贪心都可证明最优。"},
        ],
        answer=f"最多安排 {r.get('count')} 个：{r.get('chosen')}。"
               "注意这不是求总时长最长（那是另一个问题），而是**个数最多**。",
        pills=[pill("O(n log n)", "#0f766e"), pill("可证最优", "#0ea5e9", "#f0f9ff")],
    )


# ==================== 数据契约校验器 ====================
# 约束直接来自模板的真实行为，不是拍脑袋定的：
#   · 控制台 id 必须是合法 JS 标识符、非保留字、不与求值助手重名、不重复
#     —— 否则表达式会被静默求值成 null（这正是踩过的坑）；
#   · 表达式里引用的每个标识符都必须有来源（参数 / 助手 / Math / 字面量）；
#   · 每种场景必须带齐它渲染必需的字段。
HELPERS = {"pc", "lg", "ln", "bin", "hex", "twos", "pct"}
SCENE_KINDS = {"bars", "curve", "linear", "linked", "tree",
               "graph", "table", "bits", "call", "coins", "interval"}
SCENE_REQUIRED = {
    "curve": ("series",), "call": ("calls",),
    "coins": ("coins", "amount"), "interval": ("tasks",),
}
_JS_RESERVED = set(
    "break case catch class const continue debugger default delete do else enum export extends "
    "false finally for function if import in instanceof new null return super switch this throw "
    "true try typeof var void while with yield let static await implements interface package "
    "private protected public arguments eval".split())
_IDENT = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")
_IDENT_TOK = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*")
_STR_LIT = re.compile(r"""'(\\.|[^'\\])*'|"(\\.|[^"\\])*\"""")
_NUM_LIT = re.compile(r"\b0[xX][0-9a-fA-F]+\b|\b\d+(\.\d+)?([eE][+-]?\d+)?\b")
_MATH_MEM = re.compile(r"\bMath\s*\.\s*[A-Za-z_$][\w$]*")
# JS 全局对象白名单（这些在 Function 作用域里天然可用）
_JS_GLOBALS = {"Math", "Number", "String", "Boolean", "Array", "Object", "JSON",
               "true", "false", "null", "undefined", "Infinity", "NaN"}


def _expr_idents(src):
    """从表达式里提取「自由标识符」：先剥掉字符串、数字、Math.x 成员访问。"""
    s = _STR_LIT.sub(" ", str(src or ""))
    s = _NUM_LIT.sub(" ", s)
    s = _MATH_MEM.sub(" Math ", s)
    return _IDENT_TOK.findall(s)


def validate_lesson(key, d):
    """校验一个课件载荷。返回错误清单（空 = 通过）。"""
    errs = []
    for f in ("title", "subtitle", "module", "intro", "scene", "steps", "explain"):
        if d.get(f) in (None, "", [], {}):
            errs.append(f"缺少字段 {f}")

    sc = d.get("scene") or {}
    kind = sc.get("kind")
    if kind not in SCENE_KINDS:
        errs.append(f"未知场景 kind={kind!r}（可选：{sorted(SCENE_KINDS)}）")
    else:
        for f in SCENE_REQUIRED.get(kind, ()):
            if sc.get(f) in (None, [], {}):
                errs.append(f"场景 {kind} 缺少必需字段 {f}")

    steps = d.get("steps") or []
    if not steps:
        errs.append("steps 为空（回放至少需要 1 帧）")
    for i, s in enumerate(steps):
        if not isinstance(s, dict):
            errs.append(f"steps[{i}] 不是对象（{type(s).__name__}）")
        elif not (s.get("note") or s.get("op")):
            errs.append(f"steps[{i}] 既没有 note 也没有 op")

    c = d.get("console") or {}
    ids = []
    known = set(HELPERS) | _JS_GLOBALS

    def chk(id_, where):
        if not isinstance(id_, str) or not _IDENT.match(id_):
            errs.append(f"{where}: {id_!r} 不是合法 JS 标识符")
            return
        if id_ in _JS_RESERVED:
            errs.append(f"{where}: {id_!r} 是 JS 保留字 —— 表达式会整段编译失败")
        if id_ in HELPERS:
            errs.append(f"{where}: {id_!r} 与求值助手重名 —— 会被助手遮蔽")
        if id_ in ids:
            errs.append(f"{where}: {id_!r} 重复")
        ids.append(id_)

    for p in c.get("params", []):
        chk(p.get("id"), f"{key} params")
        for f in ("label", "value", "min", "max"):
            if p.get(f) is None:
                errs.append(f"{key} params[{p.get('id')}] 缺少 {f}")
        if p.get("min") is not None and p.get("max") is not None \
                and p["max"] < p["min"]:
            errs.append(f"{key} params[{p.get('id')}] max < min")
    for r in c.get("readouts", []):
        chk(r.get("id"), f"{key} readouts")
        if not r.get("expr"):
            errs.append(f"{key} readouts[{r.get('id')}] 缺少 expr")
    for l in c.get("lights", []):
        chk(l.get("id"), f"{key} lights")
        if not l.get("expr"):
            errs.append(f"{key} lights[{l.get('id')}] 缺少 expr")

    # 先登记所有 id，再校验表达式引用（读数可链式引用其它读数）
    known |= set(ids)
    targets = [(f"readouts[{r.get('id')}]", r.get("expr")) for r in c.get("readouts", [])]
    targets += [(f"lights[{l.get('id')}]", l.get("expr")) for l in c.get("lights", [])]
    if c.get("constant"):
        targets.append(("constant", c["constant"].get("expr")))
    for where, src in targets:
        for tok in _expr_idents(src):
            if tok not in known:
                errs.append(f"{key} {where} 表达式引用了未声明的标识符 {tok!r}")
    return errs


# ==================== 注册表 ====================
REGISTRY = {
    # ① 算法可视化
    "sort_bubble": build_sort_bubble,
    "sort_merge": build_sort_merge,
    "sort_quick": build_sort_quick,
    "search_binary": build_search_binary,
    "complexity": build_complexity,
    # ② 数据结构
    "stack_lifo": build_stack_lifo,
    "queue_fifo": build_queue_fifo,
    "linked_list": build_linked_list,
    "tree_traversal": build_tree_traversal,
    "bst_search": build_bst_search,
    "min_heap": build_min_heap,
    "hash_table": build_hash_table,
    # ③ 图算法
    "bfs": build_bfs,
    "dijkstra": build_dijkstra,
    "mst": build_mst,
    # ④ 计算原理
    "base_convert": build_base_convert,
    "bitwise": build_bitwise,
    "encoding": build_encoding,
    # ⑤ 算法思想
    "recursion_tree": build_recursion_tree,
    "dp_fib": build_dp_fib,
    "dp_knapsack": build_dp_knapsack,
    "greedy_coins": build_greedy_coins,
    "greedy_interval": build_greedy_interval,
}

MODULES = {
    "① 算法可视化": ["sort_bubble", "sort_merge", "sort_quick", "search_binary", "complexity"],
    "② 数据结构": ["stack_lifo", "queue_fifo", "linked_list", "tree_traversal",
                   "bst_search", "min_heap", "hash_table"],
    "③ 图算法": ["bfs", "dijkstra", "mst"],
    "④ 计算原理": ["base_convert", "bitwise", "encoding"],
    "⑤ 算法思想": ["recursion_tree", "dp_fib", "dp_knapsack", "greedy_coins",
                   "greedy_interval"],
}

# 学段：与「内容模块」**正交**的第二个维度。
#
# 为什么需要它：本技能的 23 个题型横跨初中信息技术启蒙 → 高中信息技术/信息学奥赛
# → 大学数据结构与算法，只按内容模块分组时，用户（和 agent）无法判断某个题型
# 该给哪个学段用。加上这一维之后，description 与 `list` 都能说清学段。
#
# 注意：这是**建议使用场景**的划分，不是「只能在这个学段讲」。
# 同一个知识点（例如 BFS、二分查找）常在多个学段反复出现。
STAGES = {
    "初中 · 信息技术启蒙": ["base_convert", "encoding"],
    "高中 · 信息技术与信息学奥赛": [
        "complexity", "sort_bubble", "sort_merge", "sort_quick", "search_binary",
        "stack_lifo", "queue_fifo", "linked_list", "tree_traversal", "bst_search",
        "bfs", "recursion_tree", "dp_fib",
    ],
    "大学 · 数据结构与算法": [
        "min_heap", "hash_table", "bitwise", "dijkstra", "mst",
        "dp_knapsack", "greedy_coins", "greedy_interval",
    ],
}

ORDER = [k for ks in MODULES.values() for k in ks]
_ORDER_SET = set(ORDER)
_STAGE_SET = {k for ks in STAGES.values() for k in ks}
_STAGE_OF = {k: s for s, ks in STAGES.items() for k in ks}
_MODULE_OF = {k: m for m, ks in MODULES.items() for k in ks}

# 学段必须**恰好覆盖**全部题型（不重不漏）—— 漂移就让它红，别静默放过
assert _STAGE_SET == _ORDER_SET, (
    "STAGES 与 MODULES 的题型集合不一致："
    f"STAGES 多出 {sorted(_STAGE_SET - _ORDER_SET)}，"
    f"MODULES 多出 {sorted(_ORDER_SET - _STAGE_SET)}")
assert len(ORDER) == len(_ORDER_SET) == len(_STAGE_SET), "题型在两个维度里都不得重复"


def check_all():
    """自检：注册表互覆 + 每个 build 都能实例化 + 每个载荷都通过契约校验。
    返回 {key: lesson}，调用方可直接复用，避免重复构建。"""
    missing = [k for k in REGISTRY if k not in _ORDER_SET]
    extra = [k for k in ORDER if k not in REGISTRY]
    if missing or extra:
        raise SystemExit(f"✗ 注册表不一致：REGISTRY 多出 {missing}，MODULES 多出 {extra}")

    built, problems = {}, {}
    for k in ORDER:
        try:
            d = REGISTRY[k]()
            json.dumps(d, ensure_ascii=False)          # 必须可 JSON 序列化
        except Exception as e:
            problems[k] = [f"实例化/序列化失败：{type(e).__name__}: {e}"]
            continue
        built[k] = d
        errs = validate_lesson(k, d)
        if errs:
            problems[k] = errs
    if problems:
        lines = []
        for k, es in problems.items():
            lines.append(f"  ✗ {k}")
            lines += [f"      ↳ {e}" for e in es]
        raise SystemExit("✗ 契约校验未通过：\n" + "\n".join(lines))
    return built


def meta(key):
    d = REGISTRY[key]()
    return (d["module"], d["title"], d["subtitle"])


def _stage_map():
    """按学段打印全部题型（含内容模块），并附交叉统计表。"""
    print(f"共 {len(ORDER)} 个题型 · {len(STAGES)} 个学段 · {len(MODULES)} 个内容模块\n")
    for stage, keys in STAGES.items():
        print(f"[{stage}]  {len(keys)} 个题型")
        for k in keys:
            d = REGISTRY[k]()
            print(f"  {k:18s} {_MODULE_OF[k]:8s} {d['title']}")
        print()
    print("学段 × 模块 交叉统计")
    hdr = "  " + "".join(f"{m:>10s}" for m in MODULES)
    print(hdr + f"{'合计':>8s}")
    for stage, keys in STAGES.items():
        row = [sum(1 for k in keys if _MODULE_OF[k] == m) for m in MODULES]
        print(f"  {stage[:6]:8s}" + "".join(f"{v:>10d}" for v in row) + f"{len(keys):>8d}")
    tot = [sum(1 for k in ORDER if _MODULE_OF[k] == m) for m in MODULES]
    print(f"  {'合计':8s}" + "".join(f"{v:>10d}" for v in tot) + f"{len(ORDER):>8d}")
    return 0


def build_index(out, built=None):
    built = built or {k: REGISTRY[k]() for k in ORDER}
    m = {k: (built[k]["module"], built[k]["title"], built[k]["subtitle"]) for k in ORDER}
    cards = []
    for stage, skeys in STAGES.items():
        blocks = []
        for mod, mkeys in MODULES.items():
            keys = [k for k in mkeys if k in skeys]
            if not keys:
                continue
            items = "".join(
                f'<a href="{k}.html" class="block bg-white rounded-lg border border-slate-200 p-4 '
                f'hover:border-teal-500 hover:shadow transition-all">'
                f'<div class="text-[11px] font-bold text-teal-600 mb-1">{mod}</div>'
                f'<div class="text-sm font-bold text-slate-900 leading-snug">{m[k][1]}</div>'
                f'<div class="text-[11px] text-slate-500 mt-1">{m[k][2]}</div></a>'
                for k in keys)
            blocks.append(
                f'<div class="mb-4"><div class="text-[11px] uppercase tracking-widest '
                f'text-slate-400 font-bold mb-2">{mod}</div>'
                f'<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">{items}</div></div>')
        cards.append(
            f'<div class="mb-8"><div class="text-sm font-bold text-slate-700 mb-3 '
            f'border-l-4 border-teal-500 pl-3">{stage}'
            f'<span class="ml-2 text-[11px] font-normal text-slate-400">'
            f'{len(skeys)} 个题型</span></div>{"".join(blocks)}</div>')
    html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>计算机科学 · 交互课件</title>
<style>__TAILWIND_CSS__</style>
<style>body{{font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif}}</style>
</head><body class="bg-slate-100 text-slate-900">
<div class="max-w-5xl mx-auto px-6 py-8">
  <div class="text-[11px] uppercase tracking-widest text-teal-600 font-bold">Computer Science</div>
  <h1 class="text-2xl font-bold">计算机科学 · 交互课件</h1>
  <p class="text-sm text-slate-500 mt-1">全部由 cs_kernel.py 真实执行录得的步骤驱动 ——
     动画里每一步都是算出来的。共 {len(REGISTRY)} 页，按学段分三档，每档内按内容模块排列。</p>
  <div class="mt-6">{"".join(cards)}</div>
</div></body></html>"""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(inline_assets(html), encoding="utf-8")
    return out


def _validate(key, data):
    """契约校验：validate_lesson 返回错误清单，这里转成异常（skillkit 的约定）。"""
    errs = validate_lesson(key, data)
    if errs:
        raise AssertionError(f"{key} 契约校验未通过：\n"
                             + "\n".join(f"  ✗ {e}" for e in errs))
    return True


def _index(out_dir):
    return build_index(Path(out_dir) / "index.html")


def _verify(rest):
    """verify 子命令：注册表 + 契约全量校验，并**按学段**逐页打印概览。"""
    built = check_all()
    print(f"✓ 注册表与契约校验通过：{len(ORDER)} 个课件、{len(SCENE_KINDS)} 种场景")
    for stage, keys in STAGES.items():
        print(f"\n【{stage}】{len(keys)} 个题型")
        for k in keys:
            d = built[k]
            np_ = len((d.get("console") or {}).get("params", []))
            print(f"  {k:18s} {_MODULE_OF[k]:8s} [{d['scene']['kind']:8s}] "
                  f"{len(d['steps']):3d} 帧 · 控制台 {np_} 参数 · {d['title']}")
    return 0


def _stages(rest):
    """stages 子命令：按学段列出题型（含内容模块），并给出学段 × 模块交叉统计。"""
    print(f"共 {len(ORDER)} 个题型 · {len(STAGES)} 个学段 · {len(MODULES)} 个内容模块\n")
    for stage, keys in STAGES.items():
        print(f"【{stage}】{len(keys)} 个题型")
        for k in keys:
            print(f"  {k:18s} {_MODULE_OF[k]:8s} {REGISTRY[k]()['title']}")
        print()
    print("学段 × 内容模块 交叉统计")
    short = {"① 算法可视化": "算法", "② 数据结构": "数据结构", "③ 图算法": "图算法",
             "④ 计算原理": "计算原理", "⑤ 算法思想": "算法思想"}
    print(f"  {'学段':<12s}" + "".join(f"{short[m]:>10s}" for m in MODULES) + f"{'合计':>6s}")
    for stage, keys in STAGES.items():
        row = [sum(1 for k in keys if _MODULE_OF[k] == m) for m in MODULES]
        print(f"  {stage[:4]:<12s}" + "".join(f"{v:>10d}" for v in row) + f"{len(keys):>6d}")
    tot = [sum(1 for k in ORDER if _MODULE_OF[k] == m) for m in MODULES]
    print(f"  {'合计':<12s}" + "".join(f"{v:>10d}" for v in tot) + f"{len(ORDER):>6d}")
    return 0


def main(argv=None):
    # 统一入口（edulab/shared/skillkit.py）：
    #   python generate.py verify | stages | list | all <目录> | random [seed] [输出] | <key> [输出]
    #
    # list 按**学段**分组 —— 回答「这个题型该给哪个学段用」；
    # 想看按**内容模块**分组的视图并附交叉统计表，用 stages 子命令。
    return cli(REGISTRY, doc=__doc__, groups=STAGES, meta=meta,
               validate=_validate, index_writer=_index,
               commands={"verify": _verify, "stages": _stages},
               template_name="board.html", token="__LESSON_DATA__",
               compact=True, escape_close=True, json_default=str,
               argv=argv if argv is not None else sys.argv[1:])


if __name__ == "__main__":
    raise SystemExit(main())
