# -*- coding: utf-8 -*-
"""
patch.py — 把补丁合入书稿，产出 output/overrides.json（**经校验才写入**）。

这是「把 AI 的改动写回书里」的那一步：
    对话里生成补丁 → validate → patch.py 合入 → overrides.json → 书页下次打开就带上

    python patch.py <patch.json> [...]        # 合入（会先校验，不通过则拒绝）
    python patch.py --list                    # 看当前 overrides.json
    python patch.py --clear                   # 清空

补丁文件格式（与书页里「导出草稿」的产物一致）：
    { "kind":"edu-viz-patch", "book":"...", "chapter":"ch01",
      "patches":[ {"figure":"fig-crisis", "ops":[{"path":"...","value":"..."}], "note":"..."} ] }
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "shared" / "viz"))
sys.path.insert(0, str(HERE))
import vizkit as vk          # noqa: E402
import figures as FIGS       # noqa: E402

OUT = HERE / "output"
OVERRIDES = OUT / "overrides.json"
PAGE_CANVAS_W = 783


def figure_sizes():
    sizes = {}
    for p in sorted((HERE / "chapters").glob("*.json")):
        ch = json.loads(p.read_text(encoding="utf-8"))
        for b in ch.get("blocks", []):
            if b.get("type") == "figure":
                sizes[b["id"]] = int(b.get("height") or 300)
    return sizes


def patch_sig(ops):
    """补丁内容签名——用来做幂等：同一份补丁（内容完全相同）反复应用应被识别并跳过。"""
    import hashlib
    blob = json.dumps(ops, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]


def load(path):
    # utf-8-sig：容忍带 BOM 的 JSON（Windows 工具与部分 AI 产出会写 BOM）
    try:
        return json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as e:
        raise SystemExit(
            f"❌ {path} 不是合法 JSON：{e}\n"
            f"   ↳ 检查逗号 / 引号 / 尾逗号；"
            f"用 `python -m json.tool \"{path}\"` 定位到第 {e.lineno} 行"
        ) from None
    except FileNotFoundError:
        raise SystemExit(f"❌ 找不到文件：{path}\n   ↳ 检查路径是否写对") from None
    except OSError as e:
        raise SystemExit(f"❌ 读不了 {path}：{e}") from None


def main(argv):
    if not argv:
        print(__doc__)
        return 0
    if argv[0] == "--list":
        if not OVERRIDES.exists():
            print("（还没有 overrides.json）")
            return 0
        j = load(OVERRIDES)
        for p in j.get("patches", []):
            print(f"  {p['figure']:18s} {len(p.get('ops',[]))} 处改动  {p.get('note','')}")
        return 0
    if argv[0] == "--clear":
        if OVERRIDES.exists():
            OVERRIDES.unlink()
            print("已清空 overrides.json（书页恢复原始插图）")
        return 0

    base = FIGS.build()
    sizes = figure_sizes()
    existing = load(OVERRIDES)["patches"] if OVERRIDES.exists() else []

    # 合并已有改动（同图多条时**拼接 ops**，而不是互相覆盖）
    merged = {}
    for p in existing:
        fid = p["figure"]
        e = {"figure": fid, "ops": list(p.get("ops", [])), "note": p.get("note", ""),
             "sigs": list(p.get("sigs", []))}
        if not e["sigs"] and e["ops"]:          # 旧格式兼容：补算签名
            e["sigs"] = [patch_sig(e["ops"])]
        merged[fid] = e

    n_new, n_skip = 0, 0
    for path in argv:
        j = load(path)
        for p in j.get("patches", []):
            fid = p["figure"]
            sig = patch_sig(p.get("ops", []))
            # 幂等：同一份补丁（内容完全相同）反复应用不该把 ops 翻倍
            if fid in merged and sig in merged[fid].get("sigs", []):
                print(f"  · 已应用过，跳过 {fid}（补丁内容签名 {sig} 重复）")
                n_skip += 1
                continue
            if fid in merged and "ops" in p and "ops" in merged[fid]:
                merged[fid]["ops"].extend(p["ops"])
                merged[fid].setdefault("sigs", []).append(sig)
                merged[fid]["note"] = (merged[fid]["note"] + "；" + p.get("note", "")).strip("；")
            else:
                merged[fid] = {"figure": fid, "ops": list(p.get("ops", [])),
                               "note": p.get("note", ""), "sigs": [sig]}
            n_new += 1
    if n_new == 0:
        print(f"✓ 没有新改动（{n_skip} 条重复，已跳过），书稿未变")
        return 0

    # ---- 逐图校验（用「原始 spec + 该图全部改动」）----
    bad = []
    for fid, p in merged.items():
        if fid not in base:
            bad.append((fid, f"图中不存在 {fid}"))
            continue
        rep = vk.validate_patch({fid: base[fid]}, p, W=PAGE_CANVAS_W, H=sizes.get(fid, 300))[1]
        if rep is not None and not rep.ok:
            bad.append((fid, rep.format()))
    if bad:
        print("❌ 以下改动未通过校验，整批拒绝（书稿未被修改）：")
        for fid, msg in bad:
            print(f"\n[{fid}]\n{msg}")
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    OVERRIDES.write_text(json.dumps({"kind": "edu-viz-patch", "version": 1,
                                     "patches": list(merged.values())},
                                    ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✓ 校验通过，已写入 {OVERRIDES}")
    print(f"  共 {len(merged)} 张图有改动（本次新增/更新 {n_new} 条）")
    print("  重新打开书页即生效（书页启动时自动载入 overrides.json）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
