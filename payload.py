#!/usr/bin/env python3
"""Security demo canary (service + alert) — HARMLESS.

On startup it tries to overwrite its own bundled file demo-protected/canary.txt.
Ato's sandbox mounts the capsule READ-ONLY, so the write raises EROFS. The canary
catches that and serves a page that immediately pops up a SECURITY ALERT saying Ato
blocked the unauthorized write. The write genuinely fails and canary.txt is left
unchanged — nothing here is faked. It writes a fixed string, deletes nothing, reads
no secrets.
"""
import html
import http.server
import json
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

if blocked:
    title = "⛔ Ato blocked this capsule"
    line = "It tried to overwrite its own file, and Ato's sandbox denied the write."
    accent = "#c0142b"
else:
    title = "⚠️ NOT blocked"
    line = "The write SUCCEEDED — the sandbox did not protect the file (unexpected)."
    accent = "#b8860b"

# The alert text (used for both the in-page modal and the native alert()).
alert_text = f"{title}\n\n{line}\n\n{detail}\n\nThe file is unchanged:\n{canary}"
alert_js = json.dumps(alert_text)  # safe JS string literal

PAGE = f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Ato sandbox canary</title>
<style>
  body{{font-family:system-ui,-apple-system,sans-serif;margin:0;background:#0b1020;color:#e7e9ee}}
  .bg{{max-width:680px;margin:3rem auto;padding:0 1.2rem;opacity:.5}}
  /* the popup / alert */
  .overlay{{position:fixed;inset:0;background:rgba(4,6,15,.72);display:flex;
    align-items:center;justify-content:center;padding:1rem;z-index:9999}}
  .alert{{background:#fff;color:#16181d;max-width:460px;width:100%;border-radius:16px;
    box-shadow:0 24px 60px rgba(0,0,0,.45);overflow:hidden;animation:pop .18s ease-out}}
  @keyframes pop{{from{{transform:scale(.92);opacity:0}}to{{transform:scale(1);opacity:1}}}}
  .alert header{{background:{accent};color:#fff;padding:1rem 1.25rem;font-size:1.15rem;font-weight:700}}
  .alert .body{{padding:1.1rem 1.25rem}}
  .alert p{{margin:.4rem 0;line-height:1.5}}
  .alert code{{background:#f3f4f6;border-radius:6px;padding:.1rem .35rem;font-size:.92em}}
  .alert .file{{background:#f3f4f6;border-radius:8px;padding:.6rem .8rem;margin-top:.6rem;
    font-family:ui-monospace,monospace;font-size:.85rem;color:#0a7d2c}}
  .alert button{{margin:1rem 1.25rem 1.25rem;padding:.6rem 1.1rem;border:0;border-radius:10px;
    background:{accent};color:#fff;font-weight:700;font-size:1rem;cursor:pointer}}
  .muted{{color:#5b6170;font-size:.9rem}}
</style></head>
<body>
  <div class=bg>
    <h1>\U0001f512 Ato sandbox canary</h1>
    <p>This capsule deliberately tried to overwrite its own bundled file
       <code>demo-protected/canary.txt</code>.</p>
  </div>

  <div class=overlay id=alert role=alertdialog aria-modal=true aria-labelledby=at>
    <div class=alert>
      <header id=at>{html.escape(title)}</header>
      <div class=body>
        <p>{html.escape(line)}</p>
        <p class=muted><code>{html.escape(detail)}</code></p>
        <p>Proof — the file is unchanged:</p>
        <div class=file>{html.escape(canary)}</div>
        <p class=muted>Ato didn't make the code safe — it controlled what the code could do.</p>
      </div>
      <button onclick="document.getElementById('alert').remove()">Dismiss</button>
    </div>
  </div>

  <script>
    // Native browser alert (fires in a full tab / when the embed allows modals).
    try {{ window.alert({alert_js}); }} catch (e) {{}}
  </script>
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
print(f"[file-hack] serving alert page on 127.0.0.1:{PORT}", flush=True)
with socketserver.TCPServer(("127.0.0.1", PORT), H) as httpd:
    httpd.serve_forever()
