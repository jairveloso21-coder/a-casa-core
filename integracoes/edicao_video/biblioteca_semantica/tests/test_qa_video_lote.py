import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qa_video_lote import audit, check_manifest, overlaps, local_file, SCHEMA


def manifest():
    h = hashlib.sha256(b'original').hexdigest()
    return {'schema_version': SCHEMA, 'annotations_private': True,
            'render_semantic_text': False,
            'sources': [{'id': 'src1', 'file': 'original.webm', 'sha256': h,
                         'origin': 'raw_capture', 'duration_seconds': 16}],
            'exports': [{'source_id': 'src1', 'file': 'one.mp4',
                         'sha256': hashlib.sha256(b'export1').hexdigest(),
                         'in_seconds': 0, 'out_seconds': 6,
                         'format': 'short'},
                        {'source_id': 'src1', 'file': 'two.mp4',
                         'sha256': hashlib.sha256(b'export2').hexdigest(),
                         'in_seconds': 6, 'out_seconds': 15,
                         'format': 'short'}]}


class BatchAuditTests(unittest.TestCase):
    def test_valid_manifest_and_no_overlap(self):
        m = manifest()
        check_manifest(m)
        self.assertEqual(overlaps(m), [])

    def test_overlapping_short_clips(self):
        m = manifest()
        m['exports'][1]['in_seconds'] = 4
        self.assertAlmostEqual(overlaps(m)[0]['overlap_seconds'], 2)

    def test_source_must_be_original(self):
        m = manifest()
        m['sources'][0]['origin'] = 'V5_export'
        with self.assertRaises(ValueError):
            check_manifest(m)

    def test_semantics_are_private(self):
        m = manifest()
        m['render_semantic_text'] = True
        with self.assertRaises(ValueError):
            check_manifest(m)

    def test_out_of_bounds_rejected(self):
        m = manifest()
        m['exports'][1]['out_seconds'] = 18
        with self.assertRaises(ValueError):
            check_manifest(m)

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                local_file(Path(temp), '../private.mp4')

    def test_hash_audit_without_external_media(self):
        m = manifest()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'original.webm').write_bytes(b'original')
            (root / 'one.mp4').write_bytes(b'export1')
            (root / 'two.mp4').write_bytes(b'export2')
            report = audit(m, root, root, media_tools=False)
            self.assertTrue(report['ok'])
            (root / 'two.mp4').write_bytes(b'modified')
            report = audit(m, root, root, media_tools=False)
            self.assertFalse(report['ok'])

    def test_audio_format_must_be_supported(self):
        m = manifest()
        m['exports'][0]['format'] = 'podcast'
        with self.assertRaises(ValueError):
            check_manifest(m)


if __name__ == '__main__':
    unittest.main()