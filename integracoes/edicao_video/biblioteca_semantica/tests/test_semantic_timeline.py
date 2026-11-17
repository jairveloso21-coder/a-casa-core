"""Contract/regression tests; synthetic media metadata only."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from semantic_timeline import ValidationError, build_edl, validate_document, verify_sources

EXAMPLE = ROOT / "examples" / "example_timeline.json"


class SemanticTimelineTests(unittest.TestCase):
    def setUp(self):
        self.doc = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def assert_invalid(self, fragment):
        with self.assertRaises(ValidationError) as err:
            validate_document(self.doc)
        self.assertIn(fragment, str(err.exception))

    def test_valid_example_and_safe_edl(self):
        self.assertEqual(validate_document(self.doc), [])
        edl = build_edl(self.doc)
        self.assertFalse(edl["render_annotations"])
        self.assertTrue(edl["annotations_private"])
        self.assertEqual(len(edl["shots"]), 1)
        self.assertAlmostEqual(edl["total_seconds"], 12.0)
        self.assertNotIn("description_pt", json.dumps(edl))

    def test_annotations_cannot_be_overlaid(self):
        self.doc["events"][1]["render_as_overlay"] = True
        self.assert_invalid("render_as_overlay must be false")

    def test_derivative_source_rejected(self):
        self.doc["sources"][0]["origin"] = "edited_export"
        self.assert_invalid("origin=raw_capture")

    def test_reverse_cuts_rejected(self):
        self.doc["shots"] = [
            {"source_id": "capture_01", "in_seconds": 8, "out_seconds": 12,
             "event_ids": ["e3"], "editorial_reason": "clímax"},
            {"source_id": "capture_01", "in_seconds": 0, "out_seconds": 8,
             "event_ids": ["e1", "e2"], "editorial_reason": "preparação"}
        ]
        self.assert_invalid("reverses/overlaps the source timeline")

    def test_causal_predecessor_cannot_disappear(self):
        self.doc["shots"] = [
            {"source_id": "capture_01", "in_seconds": 4, "out_seconds": 12,
             "event_ids": ["e2", "e3"], "editorial_reason": "sem contexto"}
        ]
        self.assert_invalid("omits causal predecessor e1")

    def test_cannot_cut_inside_action(self):
        self.doc["shots"][0]["out_seconds"] = 6
        self.assert_invalid("truncates event e2")

    def test_source_hash_checked_without_mutating(self):
        payload = b"ORIGINAL CAPTURE - synthetic fixture"
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / self.doc["sources"][0]["path"]
            path.write_bytes(payload)
            self.doc["sources"][0]["sha256"] = hashlib.sha256(payload).hexdigest()
            self.assertTrue(verify_sources(self.doc, temp))
            self.assertEqual(path.read_bytes(), payload)
            path.write_bytes(payload + b"modified")
            with self.assertRaises(ValidationError):
                verify_sources(self.doc, temp)

    def test_private_only_required(self):
        self.doc["annotation_visibility"] = "subtitles"
        self.assert_invalid("private_only")

    def test_no_fabricated_result_property(self):
        self.doc["events"][2]["result_observed"] = "yes"
        self.assert_invalid("result_observed must be a boolean")


if __name__ == "__main__":
    unittest.main()
