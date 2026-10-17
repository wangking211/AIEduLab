#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bridge.py — 书页 ⇄ agent 的本地桥（纯标准库，无第三方依赖）。

它同时干两件事：
  1. **静态服务器**：把书稿目录（默认 ./output）原样服务出去——书页照常离线可开；
  2. **实时通道**：书页可以向它提问、并实时接收 agent 推回的补丁。

协议（全部 JSON，同源，无 CORS 问题）
------------------------------------
  POST /api/ask          {figure, question, state}   → {id}      书页提问
  GET  /api/patches?since=N                          → {seq, patches:[...]}
                                                                 书页轮询/SSE 拉补丁
  GET  /api/events?since=N                           SSE 长连接（有补丁立即推）
  GET  /api/status                                   → {asks, pending, patches}
  POST /api/patch        {patches:[{figure,ops,note,reply,askId}]}  agent 推补丁
                                                                 （**先校验，不通过则拒**）

agent 侧的 CLI（与 HTTP 等价，人/agent 直接用）
--------------------------------------------
  python bridge.py serve [--port 8810] [--dir output] [--open]
  python bridge.py asks                     # 看待回答的问题
  python bridge.py show <id>                # 看问题 + 它当时的状态（含图的完整 spec）
  python bridge.py reply <id> --patch p.json [--say "回答文字"]
  python bridge.py reply <id> --figure fig-crisis --ops '[{"path":...,"value":...}]' --say "..."
  python bridge.py log                      # 看已推的补丁

数据落盘在 <book>/_live/：asks.jsonl、patches.jsonl（纯文本，可 git diff、可清理）。
"""
import json
import sys
import time
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# ---- 控制台编码自愈：日志里有 ✗ ✓ ① 之类字符，GBK 控制台会直接抛
# UnicodeEncodeError 把整个请求打断（变成"连接被重置"而不是干净的 400）。
# 无论调用方有没有设 PYTHONIOENCODING，桥自己先把 stdio 切到 utf-8。
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = Path(__file__).resolve().parent
DEFAULT_BOOK = HERE.parent.parent / "books" / "math-thought"


# =====================================================================
# 存储：两个 append-only 的 jsonl
# =====================================================================
class Store:
    def __init__(self, book_dir):
        self.dir = Path(book_dir) / "_live"
        self.dir.mkdir(parents=True, exist_ok=True)
        self.asks = self.dir / "asks.jsonl"
        self.patches = self.dir / "patches.jsonl"
        self._lock = __import__("threading").Lock()

    @staticmethod
    def _read(path):
        out = []
        if path.exists():
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                line = line.strip()
                if line:
                    try:
                        out.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return out

    @staticmethod
    def _append(path, obj):
        Path(path).parent.mkdir(parents=True, exist_ok=True)   # 目录可能被外部清掉
        with Path(path).open("a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    @staticmethod
    def _write_all(path, items):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(
            "".join(json.dumps(a, ensure_ascii=False) + "\n" for a in items),
            encoding="utf-8")

    # ---- asks ----
    def add_ask(self, figure, question, state):
        with self._lock:
            rec = {"id": "ask_" + uuid.uuid4().hex[:8], "ts": time.time(),
                   "figure": figure, "question": question, "state": state, "answered": False}
            self._append(self.asks, rec)
        return rec["id"]

    def all_asks(self):
        return self._read(self.asks)

    def get_ask(self, aid):
        for a in self.all_asks():
            if a["id"] == aid:
                return a
        return None

    def mark_answered(self, aid):
        with self._lock:
            items = self.all_asks()
            for a in items:
                if a["id"] == aid:
                    a["answered"] = True
            self._write_all(self.asks, items)

    # ---- patches ----
    def add_patches(self, patches, reply=None, ask_id=None):
        with self._lock:
            have = self.all_patches()
            seq0 = have[-1]["seq"] + 1 if have else 0
            added = []
            for i, p in enumerate(patches):
                rec = {"seq": seq0 + i, "ts": time.time(), "figure": p.get("figure"),
                       "ops": p.get("ops"), "spec": p.get("spec"), "note": p.get("note", ""),
                       "replace": bool(p.get("replace")),          # 修订：替换该图的实时叠加，而不是追加
                       "reply": reply if i == 0 else None, "askId": ask_id}
                self._append(self.patches, rec)
                added.append(rec)
        return added

    def all_patches(self):
        return self._read(self.patches)


# =====================================================================
# 校验：推补丁前必须过闸
# =====================================================================
def make_validator(book_dir):
    """载入该书的 figures，返回 validate_patch(patches) → (ok, msg)。"""
    book_dir = Path(book_dir)
    sys.path.insert(0, str(HERE))
    sys.path.insert(0, str(book_dir))
    try:
        import vizkit as vk
        import figures as figs
    except Exception as e:                       # 没装书也能跑（跳过校验，但会告警）
        return lambda patches: (True, f"⚠ 未能载入校验器（{e}），补丁未经校验"), None
    base = figs.build()

    def sizes():
        out = {}
        for p in sorted((book_dir / "chapters").glob("*.json")):
            ch = json.loads(p.read_text(encoding="utf-8-sig"))
            for b in ch.get("blocks", []):
                if b.get("type") == "figure":
                    out[b["id"]] = int(b.get("height") or 300)
        return out
    sz = sizes()

    def validate(patches):
        # 同图多条：拼接 ops 后再校验（与书页/ patch.py 同语义）
        merged = {}
        for p in patches:
            fid = p.get("figure")
            if fid not in base:
                return False, f"图中不存在 {fid!r}"
            if fid in merged and "ops" in p and "ops" in merged[fid] and not p.get("replace"):
                merged[fid]["ops"] = merged[fid]["ops"] + p["ops"]
            else:
                merged[fid] = dict(p)
        for fid, p in merged.items():
            _, rep = vk.validate_patch({fid: base[fid]}, p, W=vk.PAGE_CANVAS_W, H=sz.get(fid, 300))
            if rep is not None and not rep.ok:
                return False, f"[{fid}]\n" + rep.format()
        return True, "ok"
    return validate, base


# =====================================================================
# HTTP
# =====================================================================
def make_handler(store, book_dir, validate):
    class H(SimpleHTTPRequestHandler):
        def __init__(self, *a, **kw):
            super().__init__(*a, directory=str(book_dir), **kw)

        def log_message(self, fmt, *args):
            if "/api/" in (self.path or ""):
                sys.stderr.write("  bridge %s\n" % (fmt % args))

        def _json(self, obj, code=200):
            body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _body(self):
            n = int(self.headers.get("Content-Length") or 0)
            if not n:
                return {}
            try:
                return json.loads(self.rfile.read(n).decode("utf-8-sig"))
            except Exception:
                return {}

        def do_GET(self):
            path = self.path.split("?")[0]
            qs = dict(p.split("=", 1) for p in self.path.split("?", 1)[1].split("&")) \
                if "?" in self.path else {}
            if path == "/api/status":
                asks = store.all_asks()
                return self._json({"asks": len(asks), "pending": sum(1 for a in asks if not a["answered"]),
                                   "patches": len(store.all_patches()), "figureCount": "n/a"})
            if path == "/api/patches":
                since = int(qs.get("since", -1))
                ps = [p for p in store.all_patches() if p["seq"] > since]
                return self._json({"seq": store.all_patches()[-1]["seq"] if store.all_patches() else -1,
                                   "patches": ps})
            if path == "/api/asks":
                return self._json({"asks": store.all_asks()})
            if path == "/api/events":                     # SSE
                since = int(qs.get("since", -1))
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                last = since
                try:
                    while True:
                        for p in store.all_patches():
                            if p["seq"] > last:
                                self.wfile.write(f"data: {json.dumps(p, ensure_ascii=False)}\n\n".encode())
                                self.wfile.flush()
                                last = p["seq"]
                        self.wfile.write(b": ping\n\n")
                        self.wfile.flush()
                        time.sleep(1.0)
                except (BrokenPipeError, ConnectionResetError):
                    return
                return
            return super().do_GET()

        def do_POST(self):
            try:
                self._do_POST_inner()
            except BrokenPipeError:
                pass
            except Exception as e:          # 兜底：绝不能把连接直接打断
                import traceback
                traceback.print_exc()
                try:
                    self._json({"ok": False, "error": f"{type(e).__name__}: {e}"}, 500)
                except Exception:
                    pass

        def _do_POST_inner(self):
            path = self.path.split("?")[0]
            if path == "/api/ask":
                b = self._body()
                aid = store.add_ask(b.get("figure"), b.get("question", ""), b.get("state"))
                print(f"  ← 收到提问 {aid}（{b.get('figure')}）：{str(b.get('question'))[:60]}")
                return self._json({"id": aid})
            if path == "/api/patch":
                b = self._body()
                patches = b.get("patches") or [b]
                ok, msg = validate(patches)
                if not ok:
                    print("  ✗ 补丁未通过校验：\n" + msg)
                    return self._json({"ok": False, "error": msg}, 400)
                added = store.add_patches(patches, reply=b.get("reply"), ask_id=b.get("askId"))
                for p in patches:
                    if p.get("askId"):
                        store.mark_answered(p["askId"])
                print(f"  ✓ 已推 {len(added)} 条补丁：" +
                      ", ".join(r["figure"] for r in added))
                return self._json({"ok": True, "seq": [r["seq"] for r in added]})
            return self._json({"error": "not found"}, 404)
    return H


def cmd_serve(args):
    port = 8810
    book = DEFAULT_BOOK
    do_open = "--open" in args
    for i, a in enumerate(args):
        if a == "--port" and i + 1 < len(args):
            port = int(args[i + 1])
        if a == "--dir" and i + 1 < len(args):
            book = Path(args[i + 1]).resolve()
    # 书稿目录里页面在 output/ 下；_live/ 与 overrides 留在书稿目录，不混进被服务的页面
    serve_dir = (book / "output") if (book / "output").is_dir() else book
    store = Store(book)
    validate, _ = make_validator(book)
    h = make_handler(store, serve_dir, validate)
    srv = ThreadingHTTPServer(("127.0.0.1", port), h)
    print(f"桥已启动： http://127.0.0.1:{port}/")
    print(f"  · 服务目录：{serve_dir}")
    print(f"  · 书页：   http://127.0.0.1:{port}/ch01.html")
    print(f"  · 状态：   http://127.0.0.1:{port}/api/status")
    print(f"  · 待回答问题：python bridge.py asks")
    print("  Ctrl-C 退出\n")
    if do_open:
        import webbrowser
        webbrowser.open(f"http://127.0.0.1:{port}/index.html")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n桥已停止")
    return 0


def cmd_asks(args):
    store = Store(_book_of(args))
    items = [a for a in store.all_asks() if not a["answered"]]
    if not items:
        print("（没有待回答的问题）")
        return 0
    for a in items:
        q = a["question"].replace("\n", " ")[:70]
        print(f"  {a['id']}  [{a['figure']}]  {q}")
    print(f"\n共 {len(items)} 条待回答。用 `python bridge.py show <id>` 看详情。")
    return 0


def cmd_show(args):
    store = Store(_book_of(args))
    aid = next((a for a in args if a.startswith("ask_")), None)
    a = store.get_ask(aid) if aid else None
    if not a:
        print("找不到该问题。先跑 `python bridge.py asks`")
        return 1
    print(f"问题 {a['id']}（{a['figure']}）")
    print(f"  提问：{a['question']}")
    st = a.get("state") or {}
    print(f"  读者看到第 {[v for v in st.get('viewing', []) if v['figure']==a['figure']][:1]} 步")
    if st.get("selection"):
        print(f"  选中的文字：{st['selection'][:120]}")
    sp = (st.get("figures") or {}).get(a["figure"])
    if sp:
        print(f"  该图当前 spec：{len(sp.get('layers', []))} 个图层"
              f"{'，' + str(len(sp.get('steps', []))) + ' 步' if sp.get('steps') else ''}")
        print("  （完整 spec 在 state.figures 里，改图时按路径引用）")
    return 0


def cmd_reply(args):
    store = Store(_book_of(args))
    aid = next((a for a in args if a.startswith("ask_")), None)
    patch_file = _opt(args, "--patch")
    ops_raw = _opt(args, "--ops")
    figure = _opt(args, "--figure")
    say = _opt(args, "--say")
    note = _opt(args, "--note") or ""

    if patch_file:
        try:
            j = json.loads(Path(patch_file).read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as e:
            print(f"❌ {patch_file} 不是合法 JSON：{e}\n"
                  f"   ↳ 用 `python -m json.tool \"{patch_file}\"` 定位到第 {e.lineno} 行")
            return 1
        except OSError as e:
            print(f"❌ 读不了 {patch_file}：{e}")
            return 1
        patches = j.get("patches") or ([j] if j.get("figure") else [])
    elif ops_raw and figure:
        try:
            ops_val = json.loads(ops_raw)
        except json.JSONDecodeError as e:
            print(f"❌ --ops 不是合法 JSON：{e}\n"
                  f"   ↳ 形如 --ops '[{{\"path\":\"/layers/0/label\",\"value\":\"新标题\"}}]'")
            return 1
        patches = [{"figure": figure, "ops": ops_val, "note": note}]
    else:
        print("需要 --patch <file> 或（--figure + --ops）")
        return 1
    for p in patches:
        p.setdefault("askId", aid)
        if note:
            p["note"] = (p.get("note") or "") + ("；" if p.get("note") else "") + note

    validate, _ = make_validator(_book_of(args))
    ok, msg = validate(patches)
    if not ok:
        print("❌ 补丁未通过校验，未推送：\n" + msg)
        return 1
    added = store.add_patches(patches, reply=say, ask_id=aid)
    if aid:
        store.mark_answered(aid)
    print(f"✓ 已推 {len(added)} 条补丁（{', '.join(r['figure'] for r in added)}）")
    print("  书页会在 1 秒内自动应用")
    return 0


def cmd_log(args):
    store = Store(_book_of(args))
    ps = store.all_patches()
    if not ps:
        print("（还没有推送过补丁）")
        return 0
    for p in ps:
        n = len(p.get("ops") or []) if p.get("ops") else 1
        print(f"  #{p['seq']}  {p['figure']:18s} {n} 处改动  {str(p.get('note') or '')[:50]}")
    return 0


def _opt(args, name, default=None):
    for i, a in enumerate(args):
        if a == name and i + 1 < len(args):
            return args[i + 1]
    return default


def _book_of(args):
    d = _opt(args, "--dir")
    return Path(d).resolve() if d else DEFAULT_BOOK


def main(argv):
    if not argv:
        print(__doc__)
        return 0
    cmd, rest = argv[0], argv[1:]
    return {"serve": cmd_serve, "asks": cmd_asks, "show": cmd_show,
            "reply": cmd_reply, "log": cmd_log}.get(cmd, lambda a: (print(__doc__), 0)[1])(rest)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
