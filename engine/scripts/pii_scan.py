#!/usr/bin/env python3
"""
pii_scan.py — fail-closed PII release gate for the spain-dnv-consultant template.

Why this exists
---------------
This repository is a PUBLIC Claude Code template built by copying PII-free assets
out of a private real case. Across three independent adversarial PII audits, the
leak surface was NEVER the working tree — it was git HISTORY (an old version of a
file) or commit METADATA (a personal author/committer identity). A gate that only
looks at the checked-out files is blind to all three. So this gate scans THREE
surfaces and refuses to pass unless every one of them is clean:

  (a) tracked working tree      — `git ls-files`
  (b) all reachable blobs       — every version of every file in the whole history
                                  (`git rev-list --objects --all` -> `git cat-file`)
  (c) commit metadata           — author/committer identity on every commit

It is FAIL-CLOSED: any finding on any surface exits non-zero, and it prints
`path:line` / `blob:path` references, NEVER the raw offending value (printing the
value would re-leak it into CI logs).

Two classes of check
--------------------
1. DENYLIST matching (needs the private `_pii_denylist.txt`, which is gitignored
   and therefore ABSENT in CI / on a fork). Matches known real values from the
   source case — with NFD normalization, case-folding, Cyrillic declension STEMS
   (a substring scan of the nominative form misses inflected forms), and separator
   variants. When the denylist is absent the gate says so and runs structural
   checks only (see `--require-denylist` to make absence itself a failure).

2. STRUCTURAL sweeps (denylist-blind, ALWAYS run — this is what protects forkers,
   and it catches THIRD-PARTY PII a first-party denylist can never enumerate):
     * any email / phone / social @handle in a tracked file must be a RESERVED
       value (RFC 2606 example.com / .invalid / .test; documented dummy phones);
     * NIE-format tokens `[XYZ]#######[A-Z]` must be known-synthetic;
     * REGAGE / 15-digit expediente numbers, and secret patterns (sk-, pplx-,
       ghp_, AKIA, PRIVATE KEY, bearer/JWT) are rejected outright.

Allowlist exceptions (must NOT false-positive)
----------------------------------------------
  * synthetic `example/` case (Ivan Testovenko, X9999999R, @example.com);
  * the corpus-coverage date `LAST_COVERED_DATE` — read at RUNTIME from
    `knowledge_base/practice/LAST_COVERED_DATE` (so no real date is hardcoded in
    this file) — is allowed ONLY inside the corpus-metadata files it belongs to;
  * bare years / legal-source dates are never in the denylist, so they never trip.

Usage
-----
  python engine/scripts/pii_scan.py                 # full: tree + history + metadata
  python engine/scripts/pii_scan.py --tree-only     # fast: tracked tree only
  python engine/scripts/pii_scan.py --require-denylist        # maintainer strictness
  python engine/scripts/pii_scan.py --allow-any-identity      # forkers (own commits)

Exit codes: 0 = clean, 1 = PII finding(s), 2 = operational error (no git, etc.).
Stdlib only (Python 3.8+); no pip packages.
"""

from __future__ import annotations

import argparse
import io
import re
import subprocess
import sys
import threading
import unicodedata
from pathlib import Path

# Make Cyrillic console output work on Windows (the target audience runs Windows).
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
except Exception:
    pass

# --- the ONE identity every commit in the canonical repo must carry ----------
TEMPLATE_NAME = "DNV Template"
TEMPLATE_EMAIL = "noreply@example.com"

# --- structural allowlists (denylist-blind checks must not flag these) --------
# RFC 2606 / RFC 6761 reserved names + TLDs. An email or handle domain outside
# these is treated as a real contact -> FAIL.
RESERVED_EMAIL_DOMAINS = ("example.com", "example.org", "example.net")
RESERVED_TLDS = ("test", "example", "invalid", "localhost")
# Documented dummy phone numbers (digits only, no separators). Extend as needed.
DUMMY_PHONE_DIGITS = {"34600111222", "34600000000", "34000000000"}
# Known-synthetic NIE placeholders shipped in example/ and referenced in docs.
# (Real NIEs are Z-prefixed and live only in the private denylist.)
SYNTHETIC_NIE = {"X9999999R", "X9999998T", "X9099999R"}
# @handles that are technical/placeholder tokens, not people.
SAFE_HANDLES = {"handle", "example", "user", "username", "mention", "mentions",
                "channel", "everyone", "here", "someone"}

# --- month-name tables (generic language data, NOT case data) ----------------
# Used to expand the runtime-read LAST_COVERED_DATE into the forms it might take,
# so the allowlist covers RU/ES prose spellings too. No real date is hardcoded.
_RU_MONTH_GEN = ["", "января", "февраля", "марта", "апреля", "мая", "июня",
                 "июля", "августа", "сентября", "октября", "ноября", "декабря"]
_ES_MONTH = ["", "enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

_CYRILLIC_VOWELS = set("аеёиоуыэюя")


# ===========================================================================
#  Text normalization + matching primitives
# ===========================================================================
def fold(s: str) -> str:
    """NFD-normalize, drop combining marks (diacritics), and case-fold.

    Makes 'café' == 'cafe' and folds any composed accents, so the denylist and
    the scanned text are compared on the same normalized footing. Applied
    per-line, so reported line numbers stay accurate.
    """
    decomposed = unicodedata.normalize("NFD", s)
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return stripped.casefold()


def _cyrillic(word: str) -> bool:
    return any("Ѐ" <= c <= "ӿ" for c in word)


def _stem(word: str) -> str:
    """Derive a declension stem for a Cyrillic name by stripping ONE trailing
    vowel (Зорина -> зорин, so `<stem>[а-яё]*` catches Зориной/-у/-е).
    A literal scan of the nominative form misses inflected forms (see
    docs/PII_GATE_NOTES.md §1). Only strips when the stem stays >= 3 chars.
    """
    if len(word) >= 4 and word[-1] in _CYRILLIC_VOWELS and len(word) - 1 >= 3:
        return word[:-1]
    return word


def _word_subpattern(folded_word: str) -> str:
    """Regex for a single (already folded) name word, with letter boundaries."""
    lead = r"(?<![0-9a-zа-яё])"
    if _cyrillic(folded_word):
        # stem + any run of Cyrillic letters (the declension ending). The greedy
        # class supplies the trailing boundary.
        return lead + re.escape(_stem(folded_word)) + r"[а-яё]*"
    return lead + re.escape(folded_word) + r"(?![0-9a-zа-яё])"


def compile_entry(raw_entry: str):
    """Compile a denylist entry into a regex over folded text.

    - Entries containing digits (dates, NIE/passport/REGAGE/expediente/DIR,
      income figures, addresses, contract nos.) -> LITERAL match with alphanumeric
      boundaries (no stemming — the numeric forms are enumerated exactly).
    - Alpha-only entries (names, entities, roles) -> per-word name matching:
      Cyrillic words by STEM, Latin words as whole words; multi-word entries are
      joined by a flexible separator class so 'jane.doe' / 'jane_doe' match.
    """
    folded = fold(raw_entry).strip()
    if not folded:
        return None
    if any(ch.isdigit() for ch in folded):
        pat = r"(?<![0-9a-zа-яё])" + re.escape(folded) + r"(?![0-9a-zа-яё])"
        return re.compile(pat)
    words = [w for w in re.split(r"\s+", folded) if w]
    if not words:
        return None
    pat = r"[\s._\-]+".join(_word_subpattern(w) for w in words)
    return re.compile(pat)


# ===========================================================================
#  Denylist loading (category-aware, so findings name a CLASS, never a value)
# ===========================================================================
class DenylistEntry:
    __slots__ = ("category", "regex", "corpus_date")

    def __init__(self, category, regex, corpus_date=False):
        self.category = category
        self.regex = regex
        self.corpus_date = corpus_date


def _corpus_date_variants(iso: str) -> set:
    """All folded spellings of an ISO date (numeric + RU + ES) used to tag the
    denylist entry that collides with the corpus-coverage date."""
    variants = set()
    m = re.match(r"^\s*(\d{4})-(\d{2})-(\d{2})\s*$", iso)
    if not m:
        return variants
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    forms = [
        f"{y:04d}-{mo:02d}-{d:02d}",
        f"{d:02d}.{mo:02d}.{y:04d}", f"{d}.{mo:02d}.{y:04d}",
        f"{d:02d}/{mo:02d}/{y:04d}", f"{d}/{mo:02d}/{y:04d}",
    ]
    if 1 <= mo <= 12:
        forms.append(f"{d} {_RU_MONTH_GEN[mo]} {y}")
        forms.append(f"{d} de {_ES_MONTH[mo]} de {y}")
    for f in forms:
        variants.add(fold(f).strip())
    return variants


def load_denylist(path: Path, corpus_date_iso=None):
    """Parse `_pii_denylist.txt` into compiled, category-tagged entries.

    Section headers (`# --- label ---` / `# === label ===`) set the category of
    the entries beneath them; other `#` lines and blanks are ignored. Entries
    whose value equals the corpus-coverage date are tagged so the allowlist can
    let them through inside the corpus-metadata files.
    """
    corpus_variants = _corpus_date_variants(corpus_date_iso) if corpus_date_iso else set()
    entries = []
    category = "unknown"
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        header = re.match(r"^#\s*[-=]{2,}\s*(.*?)\s*[-=]{2,}\s*$", line)
        if header:
            label = header.group(1).strip()
            # Skip the file banner; keep meaningful section labels short.
            if label and "CANONICAL PII DENYLIST" not in label:
                category = label
            continue
        if line.startswith("#"):
            continue
        rx = compile_entry(line)
        if rx is None:
            continue
        entries.append(DenylistEntry(category, rx, fold(line).strip() in corpus_variants))
    return entries


# ===========================================================================
#  Structural (denylist-blind) detectors
# ===========================================================================
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
# Phone: require a leading '+' so we don't nuke years, money, or article numbers.
_PHONE = re.compile(r"\+\d[\d\s()‐-―-]{7,}\d")
_HANDLE = re.compile(r"(?<![\w@./])@([A-Za-z][A-Za-z0-9_]{2,})")
_NIE = re.compile(r"(?<![A-Za-z0-9])[XYZ]\d{7}[A-Z](?![A-Za-z0-9])")
_REGAGE = re.compile(r"REGAGE\d{2}[A-Za-z]\d{6,}", re.IGNORECASE)
_LONGNUM = re.compile(r"(?<!\d)\d{15}(?!\d)")
_SECRETS = [
    ("openai key", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9]{20,}")),
    ("perplexity key", re.compile(r"(?<![A-Za-z0-9])pplx-[A-Za-z0-9]{20,}")),
    ("github token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("aws access key", re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}(?![0-9A-Z])")),
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    ("bearer token", re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/-]{20,}={0,2}")),
]
# Prose file types where a bare @handle would be a real social-handle leak
# (code files legitimately use @decorators / @scoped-packages -> excluded).
_PROSE_SUFFIXES = (".md", ".txt", ".rst")


def _domain_reserved(domain: str) -> bool:
    d = domain.lower().rstrip(".")
    if d in RESERVED_EMAIL_DOMAINS:
        return True
    if any(d == rd or d.endswith("." + rd) for rd in RESERVED_EMAIL_DOMAINS):
        return True
    tld = d.rsplit(".", 1)[-1] if "." in d else d
    return tld in RESERVED_TLDS


def _phone_is_dummy(match: str) -> bool:
    digits = re.sub(r"\D", "", match)
    if digits in DUMMY_PHONE_DIGITS:
        return True
    # Classic test patterns: national part ending in 111222 / all-zero tails.
    return bool(re.search(r"(111222|0{6,})$", digits))


def _path_under(path: str, *needles: str) -> bool:
    norm = path.replace("\\", "/")
    return any(n in norm for n in needles)


def structural_findings(path: str, text: str):
    """Yield (category, line_no) for denylist-blind violations in one file/blob.

    Never yields the matched value — only its class and location.
    """
    is_prose = path.lower().endswith(_PROSE_SUFFIXES)
    in_example = _path_under(path, "example/")
    for i, line in enumerate(text.splitlines(), 1):
        for m in _EMAIL.finditer(line):
            domain = m.group(0).rsplit("@", 1)[-1]
            if not _domain_reserved(domain):
                yield ("non-reserved email", i)
        for m in _PHONE.finditer(line):
            if not _phone_is_dummy(m.group(0)):
                yield ("non-reserved phone", i)
        if is_prose:
            for m in _HANDLE.finditer(line):
                if m.group(1).lower() not in SAFE_HANDLES:
                    yield ("social @handle", i)
        for m in _NIE.finditer(line):
            if m.group(0) not in SYNTHETIC_NIE and not in_example:
                yield ("NIE-format identifier", i)
        if _REGAGE.search(line):
            yield ("REGAGE registro number", i)
        if _LONGNUM.search(line):
            yield ("15-digit expediente", i)
        for label, rx in _SECRETS:
            if rx.search(line):
                yield ("secret: " + label, i)


# ===========================================================================
#  Denylist matching over folded text
# ===========================================================================
def denylist_findings(path: str, text: str, entries, corpus_paths):
    """Yield (category, line_no) for denylist hits, applying the corpus-date
    path allowlist. Matched values are never yielded."""
    allowed_corpus = _path_under(path, *corpus_paths) if corpus_paths else False
    for i, line in enumerate(text.splitlines(), 1):
        folded = fold(line)
        for e in entries:
            if e.corpus_date and allowed_corpus:
                continue
            if e.regex.search(folded):
                yield ("denylist [" + e.category + "]", i)


# ===========================================================================
#  Git surfaces
# ===========================================================================
class GitError(Exception):
    pass


def git(root: Path, *args, binary=False):
    kw = dict(cwd=str(root), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not binary:
        kw.update(text=True, encoding="utf-8", errors="replace")
    proc = subprocess.run(["git", *args], **kw)
    if proc.returncode != 0:
        err = proc.stderr if not binary else proc.stderr.decode("utf-8", "replace")
        raise GitError(f"git {' '.join(args)} failed: {err.strip()}")
    return proc.stdout


def repo_root(start: Path) -> Path:
    try:
        out = subprocess.run(
            ["git", "-C", str(start), "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace",
        )
    except FileNotFoundError:
        raise GitError("git executable not found on PATH.")
    if out.returncode != 0:
        raise GitError(f"not inside a git repository ({start}).")
    return Path(out.stdout.strip())


def iter_tree_files(root: Path):
    """(path, text) for every tracked file (working-tree contents)."""
    listing = git(root, "ls-files", "-z")
    for rel in listing.split("\0"):
        if not rel:
            continue
        fp = root / rel
        try:
            data = fp.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:8192]:      # skip binary blobs
            continue
        yield rel, data.decode("utf-8", "replace")


def iter_history_blobs(root: Path):
    """(sha, path, text) for every reachable blob in the whole history.

    Uses one `git cat-file --batch` process (stdin fed from a thread to avoid a
    pipe deadlock on large histories). This is stronger than `git log -p`: it
    inspects every stored version of every file, including ones deleted from the
    current tree.
    """
    listing = git(root, "rev-list", "--objects", "--all")
    blob_paths = []
    seen = set()
    for line in listing.splitlines():
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue                  # commits/trees/tags have no path column
        sha, pth = parts[0], parts[1]
        key = (sha, pth)
        if key in seen:
            continue
        seen.add(key)
        blob_paths.append((sha, pth))
    if not blob_paths:
        return

    proc = subprocess.Popen(
        ["git", "cat-file", "--batch"], cwd=str(root),
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )

    def feed():
        try:
            proc.stdin.write(("\n".join(s for s, _ in blob_paths) + "\n").encode())
            proc.stdin.close()
        except OSError:
            pass

    writer = threading.Thread(target=feed, daemon=True)
    writer.start()
    out = proc.stdout
    try:
        for sha, pth in blob_paths:
            header = out.readline()
            if not header:
                break
            fields = header.split()
            if len(fields) < 3:
                continue              # 'missing' line: no body follows
            try:
                size = int(fields[2])
            except ValueError:
                break
            # EVERY existing object (blob/tree/commit/tag) emits a body of `size`
            # bytes + a trailing newline. We MUST drain it to stay aligned with
            # the stream, even for non-blobs we don't scan — otherwise the next
            # header read lands mid-body and every subsequent object misaligns.
            data = out.read(size)
            out.read(1)               # trailing newline
            if fields[1] != b"blob":
                continue              # drained; only blobs carry file content
            if b"\0" in data[:8192]:
                continue
            yield sha, pth, data.decode("utf-8", "replace")
    finally:
        writer.join()
        proc.stdout.close()
        proc.wait()


def metadata_identities(root: Path):
    """Set of (name, email) author/committer identities across all commits."""
    fmt = "%an%x1f%ae%x1f%cn%x1f%ce"
    out = git(root, "log", "--all", "--format=" + fmt)
    idents = set()
    for line in out.splitlines():
        if not line:
            continue
        f = line.split("\x1f")
        if len(f) >= 4:
            idents.add((f[0], f[1]))
            idents.add((f[2], f[3]))
    return idents


# ===========================================================================
#  Orchestration
# ===========================================================================
def read_last_covered_date(root: Path):
    fp = root / "knowledge_base" / "practice" / "LAST_COVERED_DATE"
    if fp.is_file():
        val = fp.read_text(encoding="utf-8").strip().splitlines()
        if val:
            return val[0].strip()
    return None


# Paths where the corpus-coverage date legitimately appears (it is corpus
# metadata, not a case identifier — see docs/PII_GATE_NOTES.md §4 collision note).
CORPUS_METADATA_PATHS = ("knowledge_base/practice/", "dnv-chat-mining/SKILL.md")


def scan(root: Path, entries, corpus_paths, tree_only: bool):
    """Return a de-duplicated, sorted list of findings across all surfaces.

    Each finding: (surface, ref, category). No raw values, ever.
    """
    findings = set()

    def scan_unit(surface, ref, path, text):
        for cat, ln in structural_findings(path, text):
            findings.add((surface, f"{ref}:{ln}", cat))
        if entries:
            for cat, ln in denylist_findings(path, text, entries, corpus_paths):
                findings.add((surface, f"{ref}:{ln}", cat))

    for rel, text in iter_tree_files(root):
        scan_unit("tree", rel, rel, text)

    if not tree_only:
        for sha, pth, text in iter_history_blobs(root):
            scan_unit("history", f"{sha[:12]}:{pth}", pth, text)

    return sorted(findings)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Fail-closed PII release gate (3 surfaces).")
    ap.add_argument("--denylist", default=None,
                    help="path to _pii_denylist.txt (default: <repo-root>/_pii_denylist.txt)")
    ap.add_argument("--require-denylist", action="store_true",
                    help="fail if the denylist is absent (maintainer strictness)")
    ap.add_argument("--tree-only", action="store_true",
                    help="scan only the tracked working tree (skip history)")
    ap.add_argument("--allow-any-identity", action="store_true",
                    help="do not require commit identities to be the template identity "
                         "(forkers commit under their own name)")
    ap.add_argument("--root", default=".", help="a path inside the repo to scan")
    args = ap.parse_args(argv)

    try:
        root = repo_root(Path(args.root))
    except GitError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    dl_path = Path(args.denylist) if args.denylist else (root / "_pii_denylist.txt")
    corpus_date = read_last_covered_date(root)
    entries = None
    if dl_path.is_file():
        entries = load_denylist(dl_path, corpus_date)
        print(f"denylist: loaded {len(entries)} entries from {dl_path.name}")
    else:
        if args.require_denylist:
            print(f"error: denylist required but not found at {dl_path}", file=sys.stderr)
            return 2
        print("denylist: not present — running STRUCTURAL checks only "
              "(this is expected in CI / on a fork).")

    try:
        findings = scan(root, entries, CORPUS_METADATA_PATHS, args.tree_only)
    except GitError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    meta_findings = []
    if not args.tree_only:
        try:
            for name, email in sorted(metadata_identities(root)):
                if (name, email) != (TEMPLATE_NAME, TEMPLATE_EMAIL):
                    meta_findings.append((name, email))
        except GitError as e:
            print(f"error: {e}", file=sys.stderr)
            return 2

    surfaces = "tree" if args.tree_only else "tree + history + metadata"
    if not findings and not (meta_findings and not args.allow_any_identity):
        extra = ""
        if meta_findings and args.allow_any_identity:
            extra = f" ({len(meta_findings)} non-template identity value(s) present but allowed)"
        print(f"PASS: no PII findings across {surfaces}.{extra}")
        return 0

    print(f"\nFAIL: PII gate found issues across {surfaces}.", file=sys.stderr)
    if findings:
        print(f"\n  content findings ({len(findings)}):", file=sys.stderr)
        for surface, ref, cat in findings:
            print(f"    [{surface}] {ref} — {cat}", file=sys.stderr)
    if meta_findings and not args.allow_any_identity:
        print(f"\n  commit-metadata findings ({len(meta_findings)}):", file=sys.stderr)
        print("    one or more commits carry a non-template identity "
              "(expected only 'DNV Template <noreply@example.com>').", file=sys.stderr)
        print("    Squash/rewrite history or run with --allow-any-identity on a fork.",
              file=sys.stderr)
    print("\n  (values are intentionally not printed — inspect the referenced "
          "locations locally.)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
