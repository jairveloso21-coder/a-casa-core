import copy
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from render_original import render

class RenderTests(unittest.TestCase):
    def test_reject_derivative(self):
        doc = {'schema_version':'casa.video.render/1.0','sources':[{'origin':'edited_export', 'file':'fake.mp4'}],'jobs':[{'name':'fake'}]}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(ValueError):
                render(doc,root,root/'out')

    def test_source_and_output_roots_must_differ(self):
        doc = {'schema_version':'casa.video.render/1.0','sources':[{'origin':'raw_capture'}],'jobs':[{'name':'fake'}]}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(ValueError):
                render(doc,root,root)

    def test_empty_jobs_rejected(self):
        doc = {'schema_version':'casa.video.render/1.0','sources':[{'origin':'raw_capture'}],'jobs':[]}
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with self.assertRaises(ValueError):
                render(doc,root,root/'out')

if __name__ == '__main__':
    unittest.main()