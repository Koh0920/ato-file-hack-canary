# file-hack — sandbox file-access canary (WORKS)

A harmless canary capsule that **attempts to overwrite its own bundled file**
(`demo-protected/canary.txt`). Ato's source sandbox mounts the capsule **read-only**,
so the write is **blocked** and the file is left unchanged.

> ✅ **Verified blocking** on a Linux Connected Runner (Ubuntu 24.04, kernel 6.17,
> bubblewrap 0.9.0 + Landlock, `ato 0.7.0`). The write fails with
> `OSError: [Errno 30] Read-only file system: '/app/demo-protected/canary.txt'`,
> the run ends **FAILED (exit 1)** with that reason, and `canary.txt` stays
> intact. Evidence: `../../docs/security-demo-evidence/file-hack-runtime-log.txt`.

## What it does (harmless)

`payload.py` does exactly one thing: `open("demo-protected/canary.txt", "w")`. It
writes a fixed string, deletes nothing, touches no real user data. The capsule's
own files are bind-mounted read-only by the sandbox, so the open() raises and the
run fails — that failure **is** the "Ato blocked it" evidence.

## Runtime / where enforcement comes from

- `runtime = "source/python"`, `[isolation] sandbox = true`, **no writable paths
  declared**. Ato mounts the capsule source read-only (`/app`), so any write into
  it fails with `EROFS`.
- **Must run on a Linux runner** (bubblewrap). The macOS sandbox profile is
  `(allow default)` and would NOT block this — run it on the Linux Connected Runner.
- Run with default strict sandbox: `ato run --sandbox .` (or via the PWA on a Linux
  runner). Do **not** use `-U` / `CAPSULE_ALLOW_UNSAFE` — those disable the sandbox.

## Verify (CLI, on a Linux runner)

```bash
ato run --sandbox .
# -> child traceback: OSError [Errno 30] Read-only file system: /app/demo-protected/canary.txt
# -> run FAILED (exit 1); demo-protected/canary.txt unchanged
```

## Note on runtime choice

This uses `source/python` (not `source/native`) because shell/native source
capsules currently fail to launch under `--sandbox` (ato-run/ato#785). The
`source/python` FS isolation is real and verified here. (Network isolation is a
separate, unrelated gap — see `../network-hack/README.md` and ato-run/ato#786.)
