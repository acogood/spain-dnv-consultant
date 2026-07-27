"""
Shared helpers for the chat-processing engine scripts.

Why this exists: forkers run these scripts on THEIR OWN Telegram exports —
untrusted input from the script's point of view. A malformed or hostile dump
must fail in a controlled way (clear error, non-zero exit) rather than crash,
hang, or exhaust memory. Output must never escape the user's workspace.

These helpers are deliberately dependency-free (stdlib only) so the scripts
stay copy-pasteable into any environment.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Limits for untrusted input. Override via env or the CLI of each script.
# ---------------------------------------------------------------------------
DEFAULT_MAX_BYTES = 512 * 1024 * 1024   # 512 MB — a Telegram export of a busy
                                        # chat is tens of MB; 512 is generous.
DEFAULT_MAX_DEPTH = 200                  # JSON nesting guard (anti-stack-bomb).


class SafeIOError(Exception):
    """Raised for any controlled refusal (bad input, path escape, limits)."""


def _fail(msg: str) -> "SafeIOError":
    return SafeIOError(msg)


def check_json_depth(raw: str, max_depth: int = DEFAULT_MAX_DEPTH) -> None:
    """Reject pathologically nested JSON BEFORE handing it to json.loads.

    Scans braces/brackets while respecting string literals and escapes, so a
    deeply-nested payload is rejected cheaply instead of blowing the parser's
    C stack. O(n), no allocation.
    """
    depth = 0
    in_str = False
    escape = False
    for ch in raw:
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch in "[{":
            depth += 1
            if depth > max_depth:
                raise _fail(
                    f"JSON nesting exceeds max depth {max_depth} — refusing "
                    f"to parse (possible malformed/hostile input)."
                )
        elif ch in "]}":
            depth -= 1


def load_json_safe(
    path: str | os.PathLike,
    *,
    max_bytes: int = DEFAULT_MAX_BYTES,
    max_depth: int = DEFAULT_MAX_DEPTH,
):
    """Load a JSON file with size + depth guards. Raises SafeIOError on refusal."""
    p = Path(path)
    if not p.is_file():
        raise _fail(f"Input file not found: {p}")
    size = p.stat().st_size
    if size > max_bytes:
        raise _fail(
            f"Input file is {size:,} bytes, over the {max_bytes:,}-byte limit. "
            f"Raise --max-bytes only if you trust this file."
        )
    raw = p.read_text(encoding="utf-8")
    check_json_depth(raw, max_depth=max_depth)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise _fail(f"Input is not valid JSON ({p}): {e}") from e


def messages_of(data) -> list:
    """Return the message list from a raw Telegram export ({...,'messages':[...]})
    or from an already-extracted list ([...]). Validates shape (fail-closed)."""
    if isinstance(data, dict):
        msgs = data.get("messages")
        if not isinstance(msgs, list):
            raise _fail("Expected a 'messages' array in the export object.")
        return msgs
    if isinstance(data, list):
        return data
    raise _fail("Unexpected JSON shape: expected an object or an array.")


def resolve_output(path: str | os.PathLike, allowed_root: str | os.PathLike) -> Path:
    """Resolve an output path and guarantee it stays inside allowed_root.

    Relative paths are interpreted against the current working directory (the
    intuitive CLI behavior); `allowed_root` is purely the containment guardrail.
    Absolute paths and `..` escapes that land outside allowed_root are rejected.
    Returns the resolved Path (parent dirs created by the caller).
    """
    root = Path(allowed_root).resolve()
    candidate = Path(path)
    resolved = (candidate if candidate.is_absolute() else (Path.cwd() / candidate)).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise _fail(
            f"Refusing to write outside the allowed root.\n"
            f"  output : {resolved}\n"
            f"  allowed: {root}\n"
            f"Outputs must stay inside the allowed root (default: the user workspace)."
        )
    return resolved


def _hmac_token(salt: bytes, material: str, prefix: str, length: int) -> str:
    """Prefixed, truncated HMAC-SHA256 over `material`. One construction for
    every salted token in the pipeline, so they cannot drift apart."""
    digest = hmac.new(salt, material.encode("utf-8"), hashlib.sha256).hexdigest()
    return prefix + digest[:length]


def stable_pseudonym(identity: str, salt: bytes, length: int = 12) -> str:
    """Deterministic, salted pseudonym for an author identity (e.g. from_id).

    Same (salt, identity) -> same pseudonym (enables distinct-author counts and
    idempotent re-imports). The salt is local and secret; the pseudonyms must
    NOT be published (see build_digest.py) — with a known author roster and a
    public salt they would be reversible.
    """
    return _hmac_token(salt, identity, "u_", length)


CORPUS_REF_PREFIX = "m_"


def stable_corpus_ref(message_id, salt: bytes, length: int = 12) -> str:
    """Deterministic, salted reference to a CORPUS MESSAGE id.

    Why this exists: `curation.json` ships in the public repo, and it used to
    carry raw Telegram message ids in `supporting_ids`. A raw id is a
    re-identification key — with the chat known, it reconstructs the message and
    therefore its author. The regex PII gate cannot see that class at all: an
    integer is indistinguishable from any other integer.

    A salted ref keeps what the curation actually needs — a stable handle the
    maintainer can resolve against their own corpus, and proof that a claim rests
    on named messages rather than on a broad regex (the third case of the band
    contract) — while publishing nothing that points back at a person. The salt
    is gitignored and never shipped, so the ref is not reversible by a reader.

    WHERE THE SALT LIVES — the rule, not a fixed path. `anonymize_chat.py`
    defaults `--salt-file` to `<dirname(output)>/.anon_salt`, so the location
    follows whatever output path you anonymized to: `user/anon.json` puts it in
    `user/.anon_salt`, `user/anon/corpus.json` in `user/anon/.anon_salt`. Both
    appear in the docs because they are different corpora, not a contradiction —
    the maintainer's corpus lives under `user/anon/`, the quick-start in
    `engine/scripts/README.md` writes to `user/anon.json`.

    Consequence: for anything that must resolve against an EXISTING corpus
    (`build_digest.py --salt-file`, `_private/hash_curation_ids.py`) always pass
    `--salt-file` EXPLICITLY. Relying on the default silently mints a fresh salt
    against the wrong directory, and a fresh salt resolves nothing.

    Domain-separated from stable_pseudonym() by the `mid:` prefix on the HMAC
    input: an author identity and a message id can never collide into the same
    token even if their string forms coincide.
    """
    return _hmac_token(salt, "mid:" + str(message_id), CORPUS_REF_PREFIX, length)


def is_corpus_ref(value) -> bool:
    """Is `value` a salted corpus ref (as opposed to a raw id)? Shape-only check
    — used to decide, fail-closed, which resolution mode a curation file needs."""
    return (isinstance(value, str)
            and value.startswith(CORPUS_REF_PREFIX)
            and len(value) > len(CORPUS_REF_PREFIX)
            and all(c in "0123456789abcdef" for c in value[len(CORPUS_REF_PREFIX):]))


def load_or_create_salt(salt_file: str | os.PathLike) -> bytes:
    """Read a persisted salt, or create one on first use. Local & secret.

    A stable salt makes pseudonyms reproducible across sessions (needed for
    idempotent mining). It lives under user/ and is gitignored — never shipped.
    """
    p = Path(salt_file)
    if p.is_file():
        val = p.read_text(encoding="utf-8").strip()
        if val:
            return bytes.fromhex(val)
    salt = os.urandom(32)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(salt.hex(), encoding="utf-8")
    return salt


def load_salt_readonly(salt_file: str | os.PathLike) -> bytes:
    """Read an EXISTING salt, refusing to create one. Use this when the salt must
    match tokens that were minted earlier.

    The difference from load_or_create_salt() is not cosmetic. On a mistyped path
    that function silently mints a FRESH salt, and every token derived from it
    then fails to match the ones already on disk — pseudonyms split one person
    into two (inflating author bands), and corpus refs resolve to nothing (bands
    collapse and claims vanish under k-anonymity). Both failures look like data,
    not like an error. Anything RESOLVING existing tokens must fail loudly instead.
    """
    p = Path(salt_file)
    if not p.is_file():
        raise _fail(
            f"Salt file not found: {p}\n"
            f"Refusing to create one here: a fresh salt would silently fail to "
            f"match the tokens it is supposed to resolve. Point --salt-file at the "
            f"salt those tokens were minted with (maintainer corpus: "
            f"user/anon/.anon_salt)."
        )
    val = p.read_text(encoding="utf-8").strip()
    if not val:
        raise _fail(f"Salt file is empty: {p}")
    try:
        return bytes.fromhex(val)
    except ValueError as e:
        raise _fail(f"Salt file is not hex ({p}): {e}") from e


def die(err: Exception, code: int = 2) -> None:
    """Print a controlled error to stderr and exit non-zero (no traceback)."""
    print(f"error: {err}", file=sys.stderr)
    sys.exit(code)
