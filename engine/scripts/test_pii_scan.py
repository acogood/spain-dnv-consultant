"""
Tests for the fail-closed PII release gate (pii_scan.py). Stdlib unittest.

    C:/Python313/python.exe -m unittest test_pii_scan -v
    python -m unittest test_pii_scan            # from engine/scripts/

IMPORTANT: this file is itself scanned by the gate, so it must not contain any
real denylisted value OR any gate-tripping token. Every fixture is either
INVENTED (never a real case value) or a format-valid PII-shaped token ASSEMBLED
at runtime from fragments via `J(...)`, so the source fragments stay below every
detector threshold while the assembled string still exercises the detector.
Reserved/synthetic values that the gate allows (x@example.com, X9999999R,
+34 600 111 222) may appear as plain literals.

Layers:
  * unit tests of the pure detectors/matchers on synthetic strings (fast, no git);
  * integration tests that build a THROWAWAY git repo (with a subdirectory, so
    the cat-file batch reader must stay aligned across a tree object — regression
    guard for the body-draining bug);
  * a check that the REAL repo this file lives in scans clean (exit-0 contract).
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pii_scan as p  # noqa: E402


def J(*parts):
    """Assemble a token at runtime so no gate-tripping literal appears in source."""
    return "".join(parts)


def scats(path, text):
    return sorted({c for c, _ in p.structural_findings(path, text)})


class TestFoldAndStem(unittest.TestCase):
    def test_fold_diacritics_and_case(self):
        self.assertEqual(p.fold("café"), p.fold("cafe"))
        self.assertEqual(p.fold("CAFE"), "cafe")

    def test_stem_strips_one_cyrillic_vowel(self):
        self.assertEqual(p._stem("зорина"), "зорин")
        self.assertEqual(p._stem("петрова"), "петров")

    def test_stem_leaves_consonant_ending(self):
        self.assertEqual(p._stem("зорин"), "зорин")
        self.assertEqual(p._stem("петров"), "петров")


class TestStructuralDetectors(unittest.TestCase):
    def test_email_reserved_vs_real(self):
        self.assertEqual(scats("a.md", "x@example.com"), [])
        self.assertEqual(scats("a.md", "x@example.org"), [])
        self.assertIn("non-reserved email", scats("a.md", J("x@", "gmail.com")))
        self.assertIn("non-reserved email", scats("a.md", J("third.party@", "realco.io")))

    def test_phone_dummy_vs_real(self):
        self.assertEqual(scats("a.md", "call +34 600 111 222"), [])
        self.assertIn("non-reserved phone", scats("a.md", J("call +34 ", "655 123 456")))

    def test_handle_prose_only(self):
        self.assertIn("social @handle", scats("a.md", "ping @realperson"))
        self.assertEqual(scats("a.py", "ping @realperson"), [])       # code: decorators
        self.assertEqual(scats("a.md", "ping @user or @example"), [])  # placeholders

    def test_nie_synthetic_and_example_allowed(self):
        self.assertIn("NIE-format identifier", scats("docs/x.md", J("Z", "0000001R")))
        self.assertEqual(scats("docs/x.md", "X9999999R"), [])            # known-synthetic
        self.assertEqual(scats("example/mvp-case/x.md", J("Z", "1234567L")), [])  # example/

    def test_regage_requires_full_shape(self):
        self.assertEqual(scats("a.md", "never invent a REGAGE number"), [])
        self.assertIn("REGAGE registro number",
                      scats("a.md", J("REGAGE", "26e000000000009")))

    def test_long_number_and_secrets(self):
        self.assertIn("15-digit expediente", scats("a.md", J("12345", "6789099999")))
        self.assertEqual(scats("a.md", "### Risk-Priority Order"), [])   # not a sk- key
        self.assertIn("secret: openai key", scats("a.md", J("sk-", "A" * 30)))
        self.assertIn("secret: aws access key", scats("a.md", J("AKIA", "IOSFODNN7EXAMPLE")))
        self.assertTrue(any("private key" in c
                            for c in scats("a.md", J("-----BEGIN ", "RSA PRIVATE KEY-----"))))


class TestDenylistMatching(unittest.TestCase):
    def _entries(self, text, corpus_iso=None):
        d = Path(tempfile.mkdtemp())
        dl = d / "dl.txt"
        dl.write_text(text, encoding="utf-8")
        return p.load_denylist(dl, corpus_iso)

    def _dcats(self, entries, text):
        return sorted({c for c, _ in p.denylist_findings("a.md", text, entries, ())})

    def test_cyrillic_declension_via_stem(self):
        ents = self._entries("# --- applicant ---\nФейкин\n")   # invented surname
        self.assertTrue(self._dcats(ents, "это Фейкин"))        # nominative
        self.assertTrue(self._dcats(ents, "дело Фейкина"))      # genitive
        self.assertTrue(self._dcats(ents, "передали Фейкину"))  # dative
        self.assertFalse(self._dcats(ents, "совсем другой текст"))

    def test_latin_name_separator_variants(self):
        ents = self._entries("# --- applicant ---\nIvan Petrov\n")  # invented name
        self.assertTrue(self._dcats(ents, "user ivan petrov"))
        self.assertTrue(self._dcats(ents, "user ivan.petrov"))
        self.assertTrue(self._dcats(ents, "user ivan_petrov"))
        self.assertFalse(self._dcats(ents, "ivano the sailor"))     # boundary: not 'ivan'

    def test_digit_entry_literal_bounded(self):
        val = J("Z", "0000001N")                                    # assembled fake NIE
        ents = self._entries("# --- id ---\n" + val + "\n")
        self.assertTrue(self._dcats(ents, "nie is " + val + " here"))
        self.assertFalse(self._dcats(ents, "XX" + val + "XX"))       # inside a longer run

    def test_category_label_reported_not_value(self):
        ents = self._entries("# --- spouse (familiar) ---\nZzztestname\n")  # invented
        found = list(p.denylist_findings("a.md", "hi Zzztestname bye", ents, ()))
        self.assertTrue(found)
        cat = found[0][0]
        self.assertIn("spouse (familiar)", cat)
        self.assertNotIn("Zzztestname", cat)                        # value never in label


class TestIdentityPolicy(unittest.TestCase):
    def test_template_and_github_noreply_allowed(self):
        self.assertTrue(p.identity_allowed(p.TEMPLATE_NAME, p.TEMPLATE_EMAIL))
        self.assertTrue(p.identity_allowed("GitHub", "noreply@github.com"))
        self.assertTrue(p.identity_allowed(
            "somedev", J("12345+somedev@", "users.noreply.github.com")))

    def test_real_personal_email_rejected(self):
        # a GitHub-side merge with email privacy OFF stamps a routable address
        self.assertFalse(p.identity_allowed("Some Dev", J("some.dev@", "gmail.com")))
        self.assertFalse(p.identity_allowed("Some Dev", J("some.dev@", "company.io")))


class TestCorpusDateAllowlist(unittest.TestCase):
    def _entries(self):
        # An invented ISO date standing in for LAST_COVERED_DATE.
        d = Path(tempfile.mkdtemp())
        dl = d / "dl.txt"
        dl.write_text("# --- real case dates ---\n2020-02-20\n", encoding="utf-8")
        return p.load_denylist(dl, "2020-02-20")

    def test_allowed_in_corpus_paths_flagged_elsewhere(self):
        ents = self._entries()
        corpus = ("knowledge_base/practice/",)
        inside = list(p.denylist_findings(
            "knowledge_base/practice/digest.md", "covered 2020-02-20", ents, corpus))
        outside = list(p.denylist_findings(
            "engine/x.md", "case 2020-02-20", ents, corpus))
        self.assertFalse(inside)     # corpus-coverage metadata: allowed
        self.assertTrue(outside)     # same date as a case reference: flagged


class TestGitSurfacesIntegration(unittest.TestCase):
    """Build a throwaway repo and exercise history-blob + metadata surfaces."""

    def _run(self, root, *args):
        subprocess.run(["git", *args], cwd=str(root), check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def _make_repo(self, tmp, name, email):
        root = Path(tmp)
        self._run(root, "init", "-q")
        self._run(root, "config", "user.name", name)
        self._run(root, "config", "user.email", email)
        self._run(root, "config", "commit.gpgsign", "false")
        # a subdirectory -> a tree object between blobs (batch-reader alignment).
        (root / "sub").mkdir()
        (root / "sub" / "keep.txt").write_text("hello\n", encoding="utf-8")
        (root / "leak.md").write_text(
            J("contact third.party@", "realmail.com") + " here\n", encoding="utf-8")
        self._run(root, "add", "-A")
        self._run(root, "commit", "-q", "-m", "seed")
        return root

    def test_personal_identity_is_a_finding(self):
        email = J("real.person@", "personal.com")   # assembled: real-looking at runtime
        with tempfile.TemporaryDirectory() as tmp:
            root = self._make_repo(tmp, "Real Person", email)
            idents = p.metadata_identities(root)
            self.assertIn(("Real Person", email), idents)
            self.assertNotIn((p.TEMPLATE_NAME, p.TEMPLATE_EMAIL), idents)

    def test_history_blob_scan_stays_aligned_past_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = self._make_repo(tmp, "Real Person", J("real.person@", "personal.com"))
            blobs = {pth: text for _, pth, text in p.iter_history_blobs(root)}
            # both the pre-tree and post-tree blobs are present and intact
            self.assertIn("leak.md", blobs)
            self.assertIn("sub/keep.txt", blobs)
            self.assertIn("realmail.com", blobs["leak.md"])
            self.assertEqual(blobs["sub/keep.txt"].strip(), "hello")
            # structural sweep catches the third-party email in history
            self.assertIn("non-reserved email", scats("leak.md", blobs["leak.md"]))


class TestRealRepoIsClean(unittest.TestCase):
    """The exit-0 contract: this repo must scan clean across all surfaces."""

    def setUp(self):
        try:
            self.root = p.repo_root(HERE)
        except p.GitError as e:
            self.skipTest(f"not in a git repo: {e}")

    def test_content_surfaces_clean(self):
        dl = self.root / "_pii_denylist.txt"
        entries = p.load_denylist(dl, p.read_last_covered_date(self.root)) \
            if dl.is_file() else None
        findings = p.scan(self.root, entries, p.CORPUS_METADATA_PATHS, tree_only=False)
        self.assertEqual(findings, [], f"unexpected PII findings: {findings}")

    def test_commit_metadata_all_identities_allowed(self):
        idents = p.metadata_identities(self.root)
        bad = sorted((n, e) for n, e in idents if not p.identity_allowed(n, e))
        self.assertEqual(bad, [], f"disallowed commit identities present: {bad}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
