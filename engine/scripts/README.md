# `engine/scripts/` — chat-mining & claim-extraction engine

Parameterized, cross-platform (Windows/macOS/Linux), **stdlib-only** Python
scripts. They process **untrusted input** (your own Telegram exports) defensively
and confine all output to a directory you choose (default: the user workspace).

> Requirements: Python 3.8+. No pip packages — the standard library is enough.
> Run with `python` or `python3` — never a hardcoded interpreter path.

## The chat pipeline

```
raw export(s) ──merge──► merged ──anonymize──► anon ──filter──► filtered ──slice──► slices/
                                      │
                                 build_digest ──► knowledge_base/practice/ (publishable)
```

All intermediate + output files belong under `user/` (gitignored). Only the
aggregated **digest** is ever publishable.

| Step | Script | Purpose |
|---|---|---|
| merge | `chat/merge_chat_dumps.py` | dedup + sort overlapping raw exports (idempotent) |
| **anonymize** | `chat/anonymize_chat.py` | **privacy gate**: keep-allowlist fields, salted pseudonym from `from_id`, strip names/contacts. Also does extraction (flatten text) — replaces the old per-name extractor. |
| filter | `chat/filter_chat.py` | tag DNV topics + reconstruct reply threads (config-driven) |
| slice | `chat/slice_by_topic.py` | one small file per topic for downstream Grep |
| digest | `chat/build_digest.py` | de-identified aggregate (counts→bands, k-anon, no keys) |
| claims | `extract_claims.py` | pull tagged claims from `user/spec.md` for verification |

`chat/_common.py` holds the shared guards (size + JSON-depth limits, output
path-containment, salted pseudonyms and salted corpus refs).
`config.example.json` holds the filter's keyword groups (copy to `config.json`
for local edits).

## Quickstart (on your own exports — everything stays in `user/`)

```bash
# 0. put your Telegram JSON export(s) in user/
python engine/scripts/chat/merge_chat_dumps.py user/dump_old.json user/dump_new.json user/merged.json --allowed-root user
python engine/scripts/chat/anonymize_chat.py user/merged.json user/anon.json --salt-file user/.anon_salt --allowed-root user
python engine/scripts/chat/filter_chat.py user/anon.json user/filtered.json --allowed-root user
python engine/scripts/chat/slice_by_topic.py user/filtered.json user/slices all --allowed-root user

# aggregate YOUR OWN curation into a digest (stays in user/ — nothing published)
python engine/scripts/chat/build_digest.py --curation user/my-curation.json \
    --slices user/anon.json --out-dir user/digest --allowed-root user --min-authors 3
```

> Single-export users can skip `merge` and feed the export straight to `anonymize`.

> **Where `.anon_salt` ends up — the rule.** `anonymize_chat.py` defaults
> `--salt-file` to `<dirname(output)>/.anon_salt`. The line above writes to
> `user/anon.json`, so the salt lands in `user/.anon_salt`; a corpus anonymized
> to `user/anon/corpus.json` puts it in `user/anon/.anon_salt` instead. Both
> paths appear across the docs because they are **different corpora**, not a
> contradiction. **Always pass `--salt-file` explicitly** for anything that must
> resolve against an existing corpus — the default would quietly mint a *fresh*
> salt in the wrong directory, and a fresh salt resolves nothing. The salt is
> gitignored: it is what makes published refs non-reversible.

> **The shipped `knowledge_base/practice/` digest is not yours to rebuild.** Its
> `curation.json` references supporting messages as SALTED REFS (`m_<hex>`) rather
> than raw message ids — a raw id plus a known chat reconstructs the message and
> its author, so it has no business in a published file. Resolving those refs
> needs the maintainer's salt, which is not shipped, and `build_digest.py` refuses
> the job rather than silently resolving them to nothing. Your own curation uses
> plain ids and needs no salt; the maintainer path is `_private/DIGEST_REBUILD.md`.

## Safety properties (why these are safe on untrusted input)

- **Size + depth limits** before parsing (`--max-bytes`, `--max-depth`): a giant
  or pathologically-nested JSON fails with a clear error, not a crash/OOM.
- **Output path-containment** (`--allowed-root`): absolute paths and `..`
  escapes are rejected — scripts cannot write outside the chosen root.
- **Fail-closed shape checks**: missing `messages`, raw (non-anonymized) input to
  `filter`/`build_digest`, bad regex in config — all refuse with a message.
- **Keep-allowlist** in the anonymizer: unknown future identity fields are
  dropped by construction (never copied), not blocklisted.
