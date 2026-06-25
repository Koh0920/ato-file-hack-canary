#!/usr/bin/env python3
"""Security demo canary — HARMLESS.

Attempts to overwrite the capsule's own bundled file demo-protected/canary.txt.
Ato's sandbox mounts the capsule READ-ONLY, so the write raises (EROFS,
"Read-only file system"); the error is re-raised, so the run ends FAILED with
the block reason in the log, and canary.txt is left unchanged.
"""
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
target = os.path.join(here, "demo-protected", "canary.txt")
print(f"[file-hack] attempting to overwrite {target}", flush=True)
print("[file-hack] (expected: BLOCKED — the capsule's files are mounted read-only)", flush=True)

# No try/except: if the mount is read-only, open(...,'w') raises OSError(EROFS)
# and that becomes the run's failure reason.
with open(target, "w") as f:
    f.write("PWNED-BY-FILE-HACK")

# Only reached if the write was NOT blocked — must not happen in the demo.
print("[file-hack] !! UNEXPECTED: overwrite SUCCEEDED — the file was writable", flush=True)
sys.exit(1)
