# -*- coding: utf-8 -*-
"""
cell_library.py — 程序化细胞器 3D 库（纯几何参数，不依赖任何外部素材）。

设计目标：用最少的程序化几何（球 / 椭球 / 胶囊 / 圆环 / 扁盘堆 / 管束 / 立方壳）
拼出可辨认的细胞结构，供 template/cell.html 的 Three.js 场景按参数直接建 mesh。

每个细胞返回：
{
  "kind": "animal" | "plant" | "prokaryotic",
  "boundary": [...],          # 最外层（细胞膜 / 细胞壁+膜 / 荚膜），由外到内
  "organelles": [ {...}, ... ],
  "views": [...],             # 分步讲解时的相机位姿（每步一个）
}

细胞器条目字段：
  id / label / geom / pos / size / color / rot / detail(讲解一句) / steps(在第几步讲解)
geom 取值：sphere, ellipsoid, capsule, disc_stack, tube_bundle, torus, rod, lobe, box, grana, centriole

坐标约定：细胞居中在原点，半径 ~4 个单位；y 向上。
"""

# ---- 调色板（生物示意图常用配色）----
C = {
    "membrane": "#f2c4ce", "wall": "#b7d9a8", "cytoplasm": "#fdf6ec",
    "nucleus": "#8e6bb5", "nucleolus": "#5b3f8a", "mito": "#e07a5f",
    "chloro": "#4c9a52", "er": "#d98cb3", "golgi": "#f2b134",
    "ribosome": "#7a5c3e", "vacuole": "#9fd3e8", "lysosome": "#f4a261",
    "centriole": "#6c757d", "dna": "#3d5a80", "flagellum": "#adb5bd",
}


def _org(id, label, geom, pos, size, color, detail, steps, rot=None, extra=None):
    d = {"id": id, "label": label, "geom": geom, "pos": list(pos), "size": size,
         "color": color, "detail": detail, "steps": list(steps)}
    if rot:
        d["rot"] = list(rot)
    if extra:
        d.update(extra)
    return d


# ==================== 动物细胞 ====================
def animal_cell():
    """动物细胞：细胞膜、细胞核、线粒体、内质网、高尔基体、核糖体、溶酶体、中心体。"""
    boundary = [
        {"geom": "sphere", "size": 4.0, "color": C["membrane"], "opacity": 0.14,
         "label": "细胞膜", "detail": "控制物质进出的边界，动物细胞的最外层"},
        {"geom": "sphere", "size": 3.93, "color": "#fdf6ec", "opacity": 0.06,
         "label": "细胞质基质", "detail": "各种细胞器悬浮其中的胶状液体"},
    ]
    organelles = [
        _org("nucleus", "细胞核", "lobe", (-0.6, 0.5, 0.2), 1.35, C["nucleus"],
             "遗传信息库，内含 DNA（染色质），是细胞代谢与遗传的控制中心", [2]),
        _org("nucleolus", "核仁", "sphere", (-0.6, 0.5, 0.2), 0.42, C["nucleolus"],
             "合成 rRNA、组装核糖体的场所", [2]),
        _org("mito1", "线粒体", "capsule", (2.1, -1.5, 0.6), [1.35, 0.55], C["mito"],
             "有氧呼吸的主要场所，把有机物分解释放能量，称「动力车间」", [3]),
        _org("mito2", "线粒体", "capsule", (-2.3, -1.1, -0.9), [1.15, 0.48], C["mito"],
             "有氧呼吸的主要场所（细胞内可有多个）", [3], rot=(0.4, 0.9, 0.2)),
        _org("er1", "内质网", "tube_bundle", (1.0, 1.5, -0.6), [1.7, 0.85], C["er"],
             "蛋白质与脂质的「合成车间」和运输通道；附着核糖体时称粗面内质网", [4]),
        _org("golgi", "高尔基体", "disc_stack", (1.6, -0.1, 0.9), [1.05, 0.32], C["golgi"],
             "对蛋白质进行加工、分类与包装，再「发送」到细胞各处", [4]),
        _org("ribo1", "核糖体", "sphere", (0.2, 2.0, 1.0), 0.17, C["ribosome"],
             "蛋白质的「装配机器」，由 rRNA 和蛋白质组成（最小的细胞器）", [4]),
        _org("ribo2", "核糖体", "sphere", (-1.6, 2.1, -0.4), 0.15, C["ribosome"],
             "蛋白质的「装配机器」", [4]),
        _org("ribo3", "核糖体", "sphere", (2.6, 0.4, -1.3), 0.14, C["ribosome"],
             "蛋白质的「装配机器」", [4]),
        _org("lyso", "溶酶体", "sphere", (-1.9, -0.2, 1.4), 0.34, C["lysosome"],
             "含多种水解酶，消化衰老细胞器与侵入的病菌，称「消化车间」", [4]),
        _org("centro", "中心体", "centriole", (-0.1, -2.0, -1.2), 0.42, C["centriole"],
             "动物细胞特有，与细胞分裂时纺锤体的形成有关", [5],
             extra={"count": 2}),
    ]
    views = [
        {"pos": (0, 1.5, 11), "target": (0, 0, 0), "label": "整体观察"},
        {"pos": (2.5, 2.0, 8.5), "target": (-0.6, 0.5, 0.2), "label": "细胞核"},
        {"pos": (5.0, -1.0, 7.0), "target": (1.6, -1.3, 0.4), "label": "线粒体"},
        {"pos": (1.0, 4.2, 8.0), "target": (0.6, 1.4, 0.2), "label": "内质网 / 高尔基体"},
        {"pos": (-3.5, -2.5, 7.5), "target": (-0.4, -1.2, -0.5), "label": "中心体"},
    ]
    return {"kind": "animal", "boundary": boundary, "organelles": organelles, "views": views}


# ==================== 植物细胞 ====================
def plant_cell():
    """植物细胞：细胞壁 + 细胞膜、大液泡、叶绿体、细胞核、线粒体、内质网、高尔基体、核糖体。"""
    boundary = [
        {"geom": "box", "size": [4.6, 4.0, 4.0], "color": C["wall"], "opacity": 0.28,
         "label": "细胞壁", "detail": "植物细胞特有，主要成分纤维素，起支持和保护作用"},
        {"geom": "box", "size": [4.42, 3.82, 3.82], "color": C["membrane"], "opacity": 0.16,
         "label": "细胞膜", "detail": "紧贴细胞壁内侧，控制物质进出"},
    ]
    organelles = [
        _org("vacuole", "液泡", "sphere", (0.55, 0.1, 0.1), 1.85, C["vacuole"],
             "植物细胞特有且很大，贮存水分、糖类和色素，维持细胞形态（成熟植物细胞）", [2],
             extra={"opacity": 0.42}),
        _org("chloro1", "叶绿体", "grana", (-2.6, 1.6, 0.9), [1.05, 0.45], C["chloro"],
             "光合作用的场所，含叶绿素，把光能转变成化学能储存在有机物中", [3]),
        _org("chloro2", "叶绿体", "grana", (-2.4, -1.7, -1.0), [0.95, 0.42], C["chloro"],
             "光合作用的场所", [3], rot=(0.3, -0.8, 0.5)),
        _org("chloro3", "叶绿体", "grana", (2.4, 2.2, -1.2), [0.9, 0.4], C["chloro"],
             "光合作用的场所", [3], rot=(-0.5, 0.6, 0.2)),
        _org("nucleus", "细胞核", "lobe", (2.3, -1.9, 1.1), 1.05, C["nucleus"],
             "遗传信息库，控制细胞的代谢和遗传", [4]),
        _org("mito1", "线粒体", "capsule", (-0.9, -2.4, 1.2), [1.05, 0.42], C["mito"],
             "有氧呼吸的主要场所，为细胞生命活动提供能量", [5]),
        _org("er1", "内质网", "tube_bundle", (2.2, 0.9, -1.2), [1.4, 0.7], C["er"],
             "蛋白质与脂质的合成和运输通道", [5]),
        _org("golgi", "高尔基体", "disc_stack", (2.6, -0.6, -0.5), [0.9, 0.28], C["golgi"],
             "植物细胞中还与细胞壁的形成有关", [5]),
        _org("ribo1", "核糖体", "sphere", (1.1, 2.0, 1.3), 0.16, C["ribosome"],
             "蛋白质的「装配机器」", [5]),
        _org("ribo2", "核糖体", "sphere", (0.1, -1.1, -2.2), 0.15, C["ribosome"],
             "蛋白质的「装配机器」", [5]),
    ]
    views = [
        {"pos": (0, 1.5, 12), "target": (0, 0, 0), "label": "整体观察"},
        {"pos": (1.0, 0.5, 9.0), "target": (0.55, 0.1, 0.1), "label": "大液泡"},
        {"pos": (-4.5, 3.0, 8.0), "target": (-2.5, 0.0, 0.0), "label": "叶绿体"},
        {"pos": (4.5, -3.5, 8.0), "target": (2.3, -1.9, 1.1), "label": "细胞核"},
        {"pos": (-1.0, -4.0, 8.5), "target": (-0.6, -1.2, 0.4), "label": "线粒体"},
    ]
    return {"kind": "plant", "boundary": boundary, "organelles": organelles, "views": views}


# ==================== 原核细胞（细菌） ====================
def prokaryotic_cell():
    """原核细胞：细胞壁 + 细胞膜、拟核（无核膜）、核糖体、荚膜、鞭毛。"""
    boundary = [
        {"geom": "capsule", "size": [3.6, 2.1], "color": C["wall"], "opacity": 0.25,
         "label": "细胞壁", "detail": "维持细胞形态、保护细胞"},
        {"geom": "capsule", "size": [3.42, 1.95], "color": C["membrane"], "opacity": 0.16,
         "label": "细胞膜", "detail": "控制物质进出"},
    ]
    organelles = [
        _org("nucleoid", "拟核", "dna_loop", (0.0, 0.0, 0.0), [1.5, 0.85], C["dna"],
             "没有核膜包被的环状 DNA，是最原始形态的细胞核", [2],
             extra={"opacity": 0.9}),
        _org("ribo1", "核糖体", "sphere", (1.5, 0.7, 0.6), 0.16, C["ribosome"],
             "原核细胞唯一的细胞器——蛋白质的装配机器", [3]),
        _org("ribo2", "核糖体", "sphere", (-1.2, -0.8, 0.7), 0.15, C["ribosome"],
             "唯一的细胞器", [3]),
        _org("ribo3", "核糖体", "sphere", (0.6, -1.0, -0.8), 0.14, C["ribosome"],
             "唯一的细胞器", [3]),
        _org("capsule", "荚膜", "capsule", (0.0, 0.0, 0.0), [3.85, 2.25], C["membrane"],
             "位于细胞壁外，有保护和抗吞噬作用（并非所有细菌都有）", [4],
             extra={"opacity": 0.10, "wireframe": True}),
        _org("flagellum", "鞭毛", "rod", (-4.6, 0.0, 0.0), [1.6, 0.07], C["flagellum"],
             "用于运动的结构", [4], rot=(0, 0, 1.5708)),
    ]
    views = [
        {"pos": (0, 1.0, 10), "target": (0, 0, 0), "label": "整体观察"},
        {"pos": (1.5, 1.2, 7.5), "target": (0, 0, 0), "label": "拟核"},
        {"pos": (3.0, 2.0, 6.5), "target": (0.6, 0, 0), "label": "核糖体"},
        {"pos": (-4.0, -2.0, 6.5), "target": (-2.0, 0, 0), "label": "荚膜 / 鞭毛"},
    ]
    return {"kind": "prokaryotic", "boundary": boundary, "organelles": organelles, "views": views}


# ==================== 对比表（植物 vs 动物 vs 原核） ====================
COMPARE = {
    "headers": ["结构", "植物细胞", "动物细胞", "原核细胞（细菌）"],
    "rows": [
        ["细胞壁", "有（纤维素）", "无", "有（肽聚糖）"],
        ["细胞膜", "有", "有", "有"],
        ["细胞核（核膜包被）", "有", "有", "无（只有拟核）"],
        ["叶绿体", "有", "无", "无"],
        ["大液泡", "有", "无", "无"],
        ["中心体", "无（高等植物）", "有", "无"],
        ["线粒体", "有", "有", "无"],
        ["核糖体", "有", "有", "有"],
        ["高尔基体", "有", "有", "无"],
        ["内质网", "有", "有", "无"],
    ],
}

CELLS = {"animal": animal_cell, "plant": plant_cell, "prokaryotic": prokaryotic_cell}


def get_cell(kind):
    assert kind in CELLS, f"未知细胞类型 {kind}，可用：{list(CELLS)}"
    return CELLS[kind]()


def build_payload(kind, steps=None):
    """产出注入 cell.html 的场景数据：细胞结构 + 分步高亮 + 对比表。"""
    cell = get_cell(kind)
    orgs = cell["organelles"]
    n_steps = len(cell["views"])
    steps = steps or [v["label"] for v in cell["views"]]
    # 每步高亮的细胞器 id 列表
    highlight = []
    for i in range(1, n_steps + 1):
        highlight.append([o["id"] for o in orgs if i in o["steps"]])
    return {
        "kind": cell["kind"], "boundary": cell["boundary"], "organelles": orgs,
        "views": cell["views"], "steps": steps, "highlight": highlight,
        "compare": COMPARE,
    }


if __name__ == "__main__":
    for kind in CELLS:
        p = build_payload(kind)
        ids = [o["id"] for o in p["organelles"]]
        assert len(ids) == len(set(ids)), f"{kind} 细胞器 id 有重复"
        assert len(p["views"]) == len(p["highlight"]) == len(p["steps"])
        for o in p["organelles"]:
            assert o["steps"], f"{kind} 的 {o['id']} 没有分配讲解步骤"
            assert max(o["steps"]) <= len(p["views"]), f"{kind} 的 {o['id']} 步骤越界"
        # 第 2 步起每步都要有高亮对象（第 1 步是整体观察，允许为空）
        for i, hl in enumerate(p["highlight"]):
            if i == 0:
                continue
            assert hl, f"{kind} 第 {i+1} 步没有高亮任何结构"
        print(f"{kind:12s} 结构 {len(p['organelles'])} 个，步骤 {len(p['steps'])} 步")
    assert all(len(r) == len(COMPARE["headers"]) for r in COMPARE["rows"]), "对比表列数不齐"
    print("cell_library self-check OK ✓")
