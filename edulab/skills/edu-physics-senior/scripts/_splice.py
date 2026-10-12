# -*- coding: utf-8 -*-
"""一次性拼接脚本：把高中力学模板里的初中场景段替换为新场景段。"""
from pathlib import Path

root = Path(__file__).resolve().parent.parent
tpl = root / "template" / "board.html"
scenes = root / "template" / "_scenes_new.js"
html = tpl.read_text(encoding="utf-8")
new_scenes = scenes.read_text(encoding="utf-8")

start = html.index("// ---- 1) 杠杆 ----")
end = html.index("// ===================== 渲染主入口 =====================")
html = html[:start] + new_scenes + "\n" + html[end:]

old_switch = """        case 'lever': drawLever(S); break;
        case 'pressure': drawPressure(S); break;
        case 'buoyancy': drawBuoyancy(S); break;
        case 'pulley': drawPulley(S); break;
        case 'circuit': drawCircuit(S); break;"""
new_switch = """        case 'belt': drawBelt(S); break;
        case 'chase': drawChase(S); break;
        case 'ramp': drawRamp(S); break;
        case 'projectile': drawProjectile(S); break;
        case 'ground': drawGround(S); break;
        case 'circle': drawCircle(S); break;
        case 'vt': drawVT(S); break;"""
assert old_switch in html, "switch 分支未找到"
html = html.replace(old_switch, new_switch)
html = html.replace("<title>初中物理互动学习</title>", "<title>高中物理力学互动学习</title>")

tpl.write_text(html, encoding="utf-8")
scenes.unlink()
print("spliced ok, lines =", html.count("\n") + 1)
