"""
Tests for the consolidated/hardened pipeline scripts: merge, filter, slice, and
extract_claims. Stdlib unittest, synthetic fixtures only.

    python -m unittest test_pipeline -v
"""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))

import _common  # noqa: E402
import anonymize_chat as ac  # noqa: E402
import merge_chat_dumps as mg  # noqa: E402
import filter_chat as fl  # noqa: E402
import slice_by_topic as sl  # noqa: E402
import extract_claims as ec  # noqa: E402

SALT = b"\x01" * 32


def _export(msgs):
    return {"name": "c", "type": "public_supergroup", "id": 1, "messages": msgs}


class TestMerge(unittest.TestCase):
    def test_dedup_and_idempotent(self):
        a = _export([{"id": 1, "type": "message", "date_unixtime": "100", "from_id": "u1", "text": "a"},
                     {"id": 2, "type": "message", "date_unixtime": "200", "from_id": "u2", "text": "b"}])
        b = _export([{"id": 2, "type": "message", "date_unixtime": "200", "from_id": "u2", "text": "b"},
                     {"id": 3, "type": "message", "date_unixtime": "300", "from_id": "u3", "text": "c"}])
        with tempfile.TemporaryDirectory() as d:
            pa, pb = Path(d) / "a.json", Path(d) / "b.json"
            pa.write_text(json.dumps(a), encoding="utf-8")
            pb.write_text(json.dumps(b), encoding="utf-8")
            merged, total_in = mg.merge([str(pa), str(pb)], _common.DEFAULT_MAX_BYTES, _common.DEFAULT_MAX_DEPTH)
            ids = [m["id"] for m in merged["messages"]]
            self.assertEqual(ids, [1, 2, 3])          # deduped, sorted by time
            self.assertEqual(total_in, 4)
            # idempotent: re-merging the same overlap adds nothing new
            again, _ = mg.merge([str(pa), str(pb), str(pb)], _common.DEFAULT_MAX_BYTES, _common.DEFAULT_MAX_DEPTH)
            self.assertEqual([m["id"] for m in again["messages"]], [1, 2, 3])

    def test_rejects_non_export_shape(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.json"
            p.write_text(json.dumps([{"id": 1}]), encoding="utf-8")  # list, not export object
            o = Path(d) / "out.json"
            with self.assertRaises(_common.SafeIOError):
                mg.merge([str(p)], _common.DEFAULT_MAX_BYTES, _common.DEFAULT_MAX_DEPTH)


class TestFilter(unittest.TestCase):
    def _anon(self):
        raw = [
            {"id": 1, "type": "message", "date": "2026-01-01T00:00:00", "from_id": "u1",
             "text": "вопрос про продление внж и renovación документов в UGE"},
            {"id": 2, "type": "message", "date": "2026-01-02T00:00:00", "from_id": "u2",
             "reply_to_message_id": 1, "text": "да, я подавал на продление, requerimiento пришёл быстро"},
            {"id": 3, "type": "message", "date": "2026-01-03T00:00:00", "from_id": "u3", "text": "ок"},
        ]
        anon, *_ = ac.anonymize(raw, SALT, 4)
        return anon

    def test_refuses_raw_input(self):
        compiled, _ = fl.load_config(str(fl.DEFAULT_CONFIG))
        raw_like = [{"id": 1, "from": "Ivan", "text": "x" * 60}]
        with self.assertRaises(_common.SafeIOError):
            fl.filter_messages(raw_like, compiled, 40)

    def test_shipped_config_compiles(self):
        compiled, min_len = fl.load_config(str(fl.DEFAULT_CONFIG))
        self.assertIn("продление", compiled)
        self.assertIsInstance(min_len, int)

    def test_tags_topics_and_threads(self):
        compiled, _ = fl.load_config(str(fl.DEFAULT_CONFIG))
        out, matched = fl.filter_messages(self._anon(), compiled, 40)
        ids = {m["id"] for m in out}
        self.assertIn(1, ids)              # matched on продление/UGE
        self.assertIn(2, ids)              # reply thread context
        topics = {t for m in out for t in m["topics"]}
        self.assertTrue({"продление", "UGE_подача"} & topics)
        # output preserves anonymization (author present, no 'from')
        for m in out:
            self.assertIn("author", m)
            self.assertNotIn("from", m)


class TestSlice(unittest.TestCase):
    def test_slice_by_topic(self):
        msgs = [
            {"id": 1, "text": "a", "reply_to": None, "author": "u_1", "topics": ["документы"]},
            {"id": 2, "text": "b", "reply_to": 1, "author": "u_2", "topics": ["thread_context"]},
            {"id": 3, "text": "c", "reply_to": None, "author": "u_3", "topics": ["налоги"]},
        ]
        docs = sl.slice_topic(msgs, "документы")
        ids = {m["id"] for m in docs}
        self.assertEqual(ids, {1, 2})      # topic msg + its reply
        self.assertNotIn(3, ids)


class TestExtractClaims(unittest.TestCase):
    def test_parses_tagged_claims(self):
        spec = "\n".join([
            "# Spec",
            "## 2. Правовая основа",
            "| Ley 14/2013, art. 76 | silencio positivo | [норма] |",
            "- Доход считается gross [практика — Telegram]",
            "## 4. Риски",
            "Этот документ обязательно нужен для подачи",  # implicit risk claim
        ])
        claims = ec.parse_spec(spec.splitlines())
        tags = [c["confidence_tag"] for c in claims]
        self.assertIn("норма", tags)
        self.assertTrue(any("Telegram" in t for t in tags))
        impl = ec.add_implicit_claims(spec.splitlines(), claims)
        self.assertTrue(any("implicit" in c["confidence_tag"] for c in impl))


class TestHardeningEndToEnd(unittest.TestCase):
    def test_broken_json_managed_failure(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "broken.json"
            p.write_text("{not valid json", encoding="utf-8")
            with self.assertRaises(_common.SafeIOError):
                _common.load_json_safe(str(p))

    def test_output_outside_root_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(_common.SafeIOError):
                _common.resolve_output("../../evil.json", d)


if __name__ == "__main__":
    unittest.main(verbosity=2)
