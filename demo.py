#!/usr/bin/env python3
"""デモ入口。文章を入れる → 台本が出る。

  python3 demo.py
  python3 demo.py --web
"""
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from yukkuri_super import super_make

ROOT = Path(__file__).resolve().parent
SAMPLE = "魔理沙が森でキノコを探してたら、霊夢に会って神社に行くことになった"
SAMPLES = {
    "forest": SAMPLE,
    "scenario": "1. 魔理沙が森へ行く\n2. キノコを探す\n3. 神社へ向かう\n4. 霊夢と会話する",
}


PAGE = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ゆっくり実況台本メーカー</title>
<style>
  :root { color-scheme: light; }
  body { font: 16px/1.55 sans-serif; max-width: 880px; margin: 24px auto; padding: 0 16px; color: #222; }
  h1 { font-size: 1.35rem; margin: 0 0 8px; }
  p.lead { color: #555; margin-top: 0; }
  textarea { width: 100%; min-height: 120px; font: 15px/1.5 sans-serif; padding: 10px; }
  button { margin: 8px 8px 0 0; padding: 8px 14px; font-size: 15px; }
  pre { background: #f6f3ea; padding: 14px; white-space: pre-wrap; border: 1px solid #e4ddcc; }
  .meta { color: #666; font-size: 13px; }
  .row { margin: 10px 0; }
</style>
</head>
<body>
  <h1>ゆっくり実況台本メーカー</h1>
  <p class="lead">文章を入れる。キャラと場面を整えて台本にする。内部の穴は見せない。</p>
  <textarea id="src">__SAMPLE__</textarea>
  <div class="row">
    <button type="button" id="go">台本にする</button>
    <button type="button" data-sample="forest">森の例</button>
    <button type="button" data-sample="scenario">シナリオの例</button>
  </div>
  <p class="meta" id="meta"></p>
  <pre id="out">（まだ作っていない）</pre>
<script>
const src = document.getElementById("src");
const out = document.getElementById("out");
const meta = document.getElementById("meta");
document.getElementById("go").onclick = async () => {
  meta.textContent = "作成中…";
  const res = await fetch("/make", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({text: src.value})
  });
  const data = await res.json();
  out.textContent = data.script || data.error || "";
  const p = data.panel || {};
  meta.textContent = [
    p.title || "",
    "不明: " + ((p.unknown || []).join(" / ") || "なし"),
    "Worldには書いていない"
  ].filter(Boolean).join("  /  ");
};
document.querySelectorAll("[data-sample]").forEach((btn) => {
  btn.onclick = async () => {
    const res = await fetch("/sample/" + btn.dataset.sample);
    const data = await res.json();
    src.value = data.text || "";
  };
});
</script>
</body>
</html>
"""


def run_demo(text: str = SAMPLE) -> dict:
    out = super_make(text)
    return {
        "ok": bool(out.get("ok")),
        "script": out.get("script") or "",
        "panel": out.get("panel") or {},
        "material": out.get("material") or {},
        "world_written": False,
    }


def show(bundle: dict) -> None:
    print("ゆっくり実況台本メーカー / DEMO")
    print("素材", (bundle.get("material") or {}).get("facts"))
    print("不明", (bundle.get("material") or {}).get("unknown"))
    print()
    print(bundle.get("script") or "")
    print("world_written", bundle.get("world_written"))


class DemoHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        print("[demo]", fmt % args)

    def _send(self, code: int, body: bytes, kind: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/index"):
            html = PAGE.replace("__SAMPLE__", SAMPLE)
            self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
            return
        if self.path.startswith("/sample/"):
            key = self.path.rsplit("/", 1)[-1]
            text = SAMPLES.get(key) or SAMPLE
            self._send(200, json.dumps({"text": text}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
            return
        self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:
        if self.path != "/make":
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        text = SAMPLE
        if raw:
            ctype = self.headers.get("Content-Type") or ""
            if "json" in ctype:
                obj = json.loads(raw.decode("utf-8") or "{}")
                text = str(obj.get("text") or SAMPLE)
            else:
                form = parse_qs(raw.decode("utf-8"))
                text = (form.get("text") or [SAMPLE])[0]
        bundle = run_demo(text)
        self._send(200, json.dumps(bundle, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")


def serve(host: str = "127.0.0.1", port: int = 8765) -> None:
    httpd = ThreadingHTTPServer((host, port), DemoHandler)
    print(f"DEMO  http://{host}:{port}/")
    httpd.serve_forever()


def main() -> None:
    p = argparse.ArgumentParser(description="ゆっくり実況台本メーカー DEMO")
    p.add_argument("text", nargs="*")
    p.add_argument("--web", action="store_true")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--out", default="")
    args = p.parse_args()
    if args.web:
        serve(args.host, args.port)
        return
    text = " ".join(args.text).strip() or SAMPLE
    bundle = run_demo(text)
    show(bundle)
    if args.out:
        Path(args.out).write_text(bundle["script"], encoding="utf-8")
        print("wrote", args.out)


if __name__ == "__main__":
    main()
