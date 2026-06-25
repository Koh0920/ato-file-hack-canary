#!/usr/bin/env python3
"""Security demo canary (service form) — HARMLESS.

On startup it tries to overwrite its own bundled file demo-protected/canary.txt.
Ato's sandbox mounts the capsule READ-ONLY, so the write raises EROFS. The canary
catches that, then serves a small report page on the readiness port: the run goes
Ready and the PWA shows that Ato denied the unauthorized write. The write genuinely
fails and canary.txt is left unchanged — nothing here is faked.
"""
import html
import http.server
import os
import socketserver

PORT = int(os.environ.get("PORT", "8000"))
here = os.path.dirname(os.path.abspath(__file__))
target = os.path.join(here, "demo-protected", "canary.txt")

# Attempt the forbidden write to the read-only capsule mount.
try:
    with open(target, "w") as f:
        f.write("PWNED-BY-FILE-HACK")
    blocked, detail = False, "the write SUCCEEDED — the sandbox did NOT protect the file"
except OSError as e:
    blocked, detail = True, f"{type(e).__name__}: {e}"

try:
    canary = open(target).read().strip()
except Exception as e:  # pragma: no cover
    canary = f"<unreadable: {e}>"

status = "BLOCKED ⛔" if blocked else "NOT BLOCKED ❌"
color = "#0a7d2c" if blocked else "#c0142b"
PAGE = f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Ato sandbox canary</title>
<style>body{{font-family:system-ui,-apple-system,sans-serif;max-width:680px;margin:3rem auto;padding:0 1.2rem;line-height:1.55}}
h1{{margin-bottom:.2rem}}.status{{color:{color};font-weight:700;font-size:1.35rem}}
code,pre{{background:#f3f4f6;border-radius:6px;padding:.15rem .4rem}}pre{{padding:.8rem;overflow:auto}}
.muted{{color:#666}}</style></head>
<body>
<h1>\U0001f512 Ato sandbox canary</h1>
<p class=muted>This capsule deliberately tried to overwrite its own bundled file
<code>demo-protected/canary.txt</code>.</p>
<p>File write: <span class=status>{status}</span></p>
<p>{html.escape(detail)}</p>
<h3>Proof &mdash; the file is unchanged:</h3>
<pre>{html.escape(canary)}</pre>
<p class=muted>Ato's source sandbox mounts the capsule read-only, so the
unauthorized write fails with <code>Read-only file system</code> and the file is
left intact. Ato didn't make the code safe &mdash; it controlled what the code
could do.</p>
</body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(PAGE.encode())

    def log_message(self, *a):  # quiet
        pass

print(f"[file-hack] file write {'BLOCKED' if blocked else 'NOT BLOCKED'}: {detail}", flush=True)
print(f"[file-hack] serving canary report on 127.0.0.1:{PORT}", flush=True)
with socketserver.TCPServer(("127.0.0.1", PORT), H) as httpd:
    httpd.serve_forever()
