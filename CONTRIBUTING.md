# Contributing to `spain-dnv-consultant`

Thanks for helping improve this template. It is a **public** repository built by
copying **PII-free** assets out of a private real immigration case, so the single
most important contribution rule is:

> **Never commit real personal data — yours or anyone else's.**
>
> *Никогда не коммить реальные персональные данные — ни свои, ни чужие.*

Your own documents, filled forms, chat exports, and case details belong under
`user/` (which is fully gitignored) — never in a tracked file. See the README
"Safety" section and `.gitignore` (the always-on privacy net).

---

## The PII gate

`engine/scripts/pii_scan.py` is a **fail-closed** scanner that refuses to pass
if it finds personal data on any of **three surfaces**:

1. the **tracked working tree** (`git ls-files`);
2. **every reachable blob in the whole history** — every stored version of every
   file, including ones deleted from the current tree (this is where past PII
   audits actually found leaks, not the working tree);
3. **commit metadata** — author/committer identity on every commit.

It reports `path:line` (or `blob:path`) references and **never prints the raw
value**, so it is safe to run in CI logs. Exit codes: `0` clean, `1` finding(s),
`2` operational error.

It runs two kinds of check:

- **Structural sweeps** (always on, no private data needed): any email / phone /
  social `@handle` in a tracked file must be a *reserved* value (RFC 2606
  `example.com`, `.invalid`, `.test`, documented dummy phones); real-format NIE,
  `REGAGE…`/15-digit expediente numbers, and secret patterns (`sk-`, `pplx-`,
  `ghp_`, `AKIA`, `PRIVATE KEY`, bearer/JWT) are rejected. This is what protects
  **you** — it catches third-party contact data a denylist could never enumerate.
- **Denylist matching** (maintainer only): matches the private, gitignored
  `_pii_denylist.txt` of real case values, with NFD/diacritic/case folding,
  Cyrillic declension **stems**, and separator variants. The denylist is **never
  shipped**, so on a fork / in CI this layer is simply skipped and the structural
  sweeps carry the load.

## Install the local pre-commit hook (recommended)

Git hooks can't ship inside the tree, so opt into the tracked hook once per clone:

```sh
git config core.hooksPath .githooks
```

Now every `git commit` runs the fast, fork-friendly profile (tracked-tree
structural sweep + denylist if you happen to have one) and **blocks the commit**
on any finding. If your Python is named oddly, set `PYTHON=/path/to/python`.

## Run it manually

```sh
# Fork-friendly full scan (tree + history + metadata, structural; identity OK):
python engine/scripts/pii_scan.py --allow-any-identity

# Fast tree-only check:
python engine/scripts/pii_scan.py --tree-only --allow-any-identity

# Maintainer release check (requires the private denylist + template identity):
python engine/scripts/pii_scan.py --require-denylist
```

**Flags that matter for forkers:**

- `--allow-any-identity` — do **not** require commit identities to be the
  template identity. You commit under your own name, so use this locally and note
  that CI's structural job passes it for you (the strict identity job is scoped to
  the canonical repo and skipped on forks).
- absent `_pii_denylist.txt` is expected off the maintainer's machine — the gate
  says so and runs structural-only. `--require-denylist` turns absence into a
  failure (maintainer use only).

## CI

`.github/workflows/pii-gate.yml` runs on every push and PR:

- **structural** job — everywhere, incl. forks: scans tree **+ full history** for
  structural PII / secrets (checkout uses `fetch-depth: 0`).
- **template-identity** job — canonical repo only (`github.repository ==` guard):
  additionally requires every commit's identity to be `DNV Template
  <noreply@example.com>`.

## Tests

Stdlib `unittest`, synthetic fixtures only (never real data):

```sh
# the gate's own tests
python -m unittest test_pii_scan            # run from engine/scripts/

# the chat-engine tests
python -m unittest discover -s engine/scripts/chat -p "test_*.py"
```

## Scope guardrails

- The engine **never files, pays, or registers** anything — it only produces
  drafts for you to verify. Please keep it that way.
- Do not edit `.gitignore` or the denylist to "make git see" your documents —
  that defeats the entire privacy design.
- Keep the scripts **stdlib-only** (no pip dependencies) and cross-platform.
