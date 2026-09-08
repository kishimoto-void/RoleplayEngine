#!/usr/bin/env python3
from __future__ import annotations

import json
import threading
import unittest
import urllib.request

from demo import DemoHandler, PAGE, SAMPLE, run_demo
from http.server import ThreadingHTTPServer


class TestDemo(unittest.TestCase):
    def test_terminal_bundle(self):
        out = run_demo(SAMPLE)
        self.assertTrue(out["ok"])
        self.assertIn("【タイトル】", out["script"])
        self.assertIn("ゆっくりしていってね", out["script"])
        self.assertFalse(out["world_written"])

    def test_page_hides_internals(self):
        self.assertIn("台本にする", PAGE)
        self.assertNotIn("Hash-A", PAGE)
        self.assertNotIn("1 + ? = 0", PAGE)

    def test_web_make(self):
        httpd = ThreadingHTTPServer(("127.0.0.1", 0), DemoHandler)
        port = httpd.server_address[1]
        th = threading.Thread(target=httpd.serve_forever, daemon=True)
        th.start()
        try:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}/make",
                data=json.dumps({"text": SAMPLE}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as res:
                body = json.loads(res.read().decode("utf-8"))
            self.assertIn("魔理沙「", body["script"])
            self.assertFalse(body["world_written"])
        finally:
            httpd.shutdown()


if __name__ == "__main__":
    unittest.main()
