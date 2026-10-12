# -*- coding: utf-8 -*-
"""坏补丁闸门回归：四类坏补丁必须都被拒（exit=1），好补丁必须通过（exit=0）。

同时覆盖两条链路：
  书侧  python patch.py <file>
  桥侧  python bridge.py reply <file>

**测试不许污染书稿**：开始前备份 overrides.json，结束后原样还原；_live/ 测完清空。
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

VIZ = Path(r"C:\workspace\AIProject\AIEduLab\edulab\shared\viz")
BOOK = Path(r"C:\workspace\AIProject\AIEduLab\edulab\books\math-thought")
ENV = dict(os.environ)
ENV["PYTHONIOENCODING"] = "utf-8"

CASES = [
    ("patches/bad-syntax.json", False, "JSON 语法错"),
    ("patches/bad-E3.json",     False, "缺必填字段"),
    ("patches/bad-E4.json",     False, "路径下标越界"),
    ("patches/bad-E5.json",     False, "世界坐标越界"),
    ("patches/complex-rotation.json", True,  "合法补丁"),
    ("patches/demo-crisis-costs.json", True, "合法补丁（已入库过）"),
]


def book_run(*args):
    return subprocess.run([sys.executable, "patch.py", *args], cwd=BOOK,
                          capture_output=True, text=True, encoding="utf-8",
                          errors="replace", env=ENV)


# ---- 备份 + 造一个干净的起点（带 sigs 的 overrides）----
OVR = BOOK / "output" / "overrides.json"      # 注意：书页读的是 output/ 下的那份
saved = OVR.read_bytes() if OVR.exists() else None
OVR.unlink(missing_ok=True)
shutil.rmtree(BOOK / "_live", ignore_errors=True)
book_run("patches/demo-crisis-costs.json")

# 起点必须是干净的：fig-crisis 恰好 5 处改动（重复入库会在这里暴露）
def _ops_of(figure):
    try:
        j = json.loads(OVR.read_text(encoding="utf-8-sig"))
    except OSError:
        return -1
    return sum(len(p.get("ops", [])) for p in j["patches"] if p["figure"] == figure)

fails = 0
setup_ops = _ops_of("fig-crisis")
if setup_ops != 5:
    fails += 1
    print(f"  ✗ 起点就不干净：fig-crisis 有 {setup_ops} 处改动（应为 5）")
for rel, expect_ok, label in CASES:
    path = BOOK / rel
    r = book_run(str(path))                                   # 书侧
    r2 = subprocess.run([sys.executable, "bridge.py", "reply", "--patch", str(path)],
                        cwd=VIZ, capture_output=True, text=True, encoding="utf-8",
                        errors="replace", env=ENV)            # 桥侧

    book_ok, bridge_ok = (r.returncode == 0), (r2.returncode == 0)
    bm = "✓" if book_ok == expect_ok else "✗"
    rm = "✓" if bridge_ok == expect_ok else "✗"
    fails += (book_ok != expect_ok) + (bridge_ok != expect_ok)

    # 坏补丁必须给出带 ↳ 修法的可读提示，不能是 traceback
    out = (r.stdout + r.stderr)
    clean = "Traceback" not in out or not expect_ok
    hint = next((l.strip() for l in out.splitlines() if l.strip()), "")
    print(f"  {bm} 书  {rm} 桥  {rel:34s} {label:22s} "
          f"{'接受' if expect_ok else '拒绝'}  {hint[:52]}")

# ---- 幂等：同一份补丁再打一次不该翻倍 ----
before = len(book_run("--list").stdout.splitlines())
book_run("patches/demo-crisis-costs.json")                   # 重复应用
after = book_run("--list")
n_dup = len(after.stdout.splitlines())
reapply_out = book_run("patches/demo-crisis-costs.json").stdout
idem_ok = "跳过" in reapply_out or "没有新改动" in reapply_out
print(f"\n  幂等：重复打同一补丁 → {'跳过并提示' if idem_ok else '❌ 被再次入库'}")
fails += (not idem_ok) + (n_dup != before)

# ---- 还原 + 书稿未被污染 ----
shutil.rmtree(BOOK / "_live", ignore_errors=True)
if saved is None:
    OVR.unlink(missing_ok=True)
else:
    OVR.write_bytes(saved)
restored_ok = (OVR.exists() if saved is None else
               OVR.exists() and OVR.read_bytes() == saved)
print(f"  还原 overrides.json: {'原样还原 ✅' if restored_ok else '❌ 未还原'}")
fails += (not restored_ok)

r = subprocess.run([sys.executable, "check.py"], cwd=BOOK, capture_output=True,
                   text=True, encoding="utf-8", errors="replace", env=ENV)
line = [l for l in r.stdout.splitlines() if "合计" in l]
line = line[-1] if line else ""
print(f"  还原后书稿校验: {line}")
if "0 个错误" not in line:
    fails += 1

print(f"\n{'闸门回归通过 ✅' if fails == 0 else f'闸门回归失败 ❌（{fails} 项）'}")
sys.exit(1 if fails else 0)
