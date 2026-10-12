# -*- coding: utf-8 -*-
"""
make-complex-rotation.py — 针对读者提问生成补丁：
「为什么说 i 是旋转 90°？把四次旋转标出来」

这是 agent 侧的标准做法：**用 Python 算几何 → 产出补丁 JSON**（不手写坐标）。
输出：patches/complex-rotation.json
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

R_ARC = 1.30          # 圆弧半径（画在单位圆外侧一点）
R_LAB = 1.62          # 序号标签半径
N = 14                # 每段弧的采样点数

A_BLUE = "#0f766e"    # 与图的 accent 家族协调

ops = []

# ---- 1) 顶部点题 ----
ops.append({"path": "layers", "op": "append", "value": {
    "geom": "text", "x": -1.55, "y": 1.34,
    "text": "每乘一次 i：逆时针转 90°",
    "align": "left", "size": 10, "color": "#7d756a", "dy": 0, "weight": "normal"}})

# ---- 2) 四段四分之一圆弧（1→i→−1→−i→1）----
for k in range(4):
    a0, a1 = k * 90, (k + 1) * 90
    pts = []
    for i in range(N + 1):
        a = math.radians(a0 + (a1 - a0) * i / N)
        pts.append([round(R_ARC * math.cos(a), 4), round(R_ARC * math.sin(a), 4)])
    ops.append({"path": "layers", "op": "append", "value": {
        "geom": "line", "data": pts, "stroke": A_BLUE, "width": 2.0}})
    # 弧末端的小箭头（用一个小三角点表示方向）
    a_end = math.radians(a1)
    ax, ay = R_ARC * math.cos(a_end), R_ARC * math.sin(a_end)
    ops.append({"path": "layers", "op": "append", "value": {
        "geom": "point", "data": [{"x": round(ax, 4), "y": round(ay, 4), "r": 3.2, "fill": A_BLUE}]}})

# ---- 3) 四个序号标签（放在各弧中点外侧）----
for k, num in enumerate("①②③④"):
    am = math.radians(k * 90 + 45)
    ops.append({"path": "layers", "op": "append", "value": {
        "geom": "text", "x": round(R_LAB * math.cos(am), 4), "y": round(R_LAB * math.sin(am), 4),
        "text": num, "align": "center", "size": 10.5, "color": A_BLUE, "dy": 0}})

# ---- 4) 结论：接到右侧文字栏下方（避免压住坐标轴与 ③④ 标签）----
ops.append({"path": "layers", "op": "append", "value": {
    "geom": "text", "x": 1.35, "y": -1.12,
    "text": "转四次回到原处\n⟹ i⁴ = 1；转两次反向 ⟹ i² = −1",
    "align": "left", "size": 10.5, "color": "#b45309", "dy": 0}})

patch = {
    "kind": "edu-viz-patch", "version": 1,
    "book": "数学思想：从计数到无穷", "chapter": "ch01",
    "patches": [{
        "figure": "fig-complex",
        "replace": True,          # 修订：替换该图的实时叠加（而不是在旧叠加之上再追加）
        "note": "补上四次旋转的圆弧与序号 ①②③④，并点明 i⁴=1、i²=−1",
        "ops": ops,
    }],
}
out = HERE / "complex-rotation.json"
out.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"已生成 {out}（{len(ops)} 条 ops）")
