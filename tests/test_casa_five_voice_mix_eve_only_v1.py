"""Regression tests for project-scoped casting on CASA's existing mixer.
Uses isolated WAV and mocked ffprobe; no FFmpeg render or FAMILIA attestation.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

SOURCE=Path(__file__).resolve().parents[1]/"integracoes"/"edicao_video"/"biblioteca_semantica"/"casa_five_voice_mix_v1.py"
SPEC=importlib.util.spec_from_file_location("casa_mix",SOURCE)
m=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)

def h(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def fake_probe(_):
    return {"streams":[
        {"codec_type":"video","codec_name":"h264","width":1920,"height":1080,
         "color_primaries":"bt709","color_transfer":"bt709","color_space":"bt709"},
        {"codec_type":"audio","codec_name":"aac"}
    ],"format":{"duration":"180.000"}}

class ExistingMixerEveOnlyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.master=self.root/"gameplay.mp4"
        self.master.write_bytes(b"LOCAL_SYNTHETIC_FIXTURE_NOT_REAL_MEDIA")
        self.output=self.root/"candidate.mp4"
        self.report=self.root/"gate.json"
        self.wavs=[]
        for i in range(5):
            p=self.root/("voice%d.wav"%i)
            with wave.open(str(p),"wb") as f:
                f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000)
                f.writeframes(b"\\x00\\x00"*24000)
            self.wavs.append(p)
        gate={"schema":"CASA_VIDEO_RELEASE_GATE_RESULT_V2",
              "phase":"pre_render","passed":True,"release_status":"PREFLIGHT_READY",
              "source_sha256":h(self.master),"editorial_scope_mode":"EVE_ONLY_PRIVATE_TEST"}
        self.report.write_text(json.dumps(gate),encoding="utf-8")

    def manifest(self,mode="EVE_ONLY"):
        starts=[10.,85.,150.] if mode=="EVE_ONLY" else [10.,45.,80.,135.,165.]
        roles=["EVE"]*3 if mode=="EVE_ONLY" else ["EVE","GUARDIAO","NINO","TROVAO","LIA"]
        shots=[]
        for n,(at,role) in enumerate(zip(starts,roles)):
            shots.append({"voice":role,"path":str(self.wavs[n]),"sha256":h(self.wavs[n]),
                 "at":at,"until":at+5.,"scene_evidence_seconds":at+1.,
                 "text":"Synthetic scene narration for the unit test.",
                 "qa":{"technical_pass":True,"ptbr_natural_review":"APPROVED",
                       "voice_identity_review":"APPROVED","reviewer":"owner",
                       "review_evidence":"SYNTHETIC_UNIT_FIXTURE_ONLY"}})
        doc={"schema":"CASA_FIVE_VOICE_MIX_V1",
             "master":{"path":str(self.master),"sha256":h(self.master),
                       "duration_seconds":180,"require_bt709":True},
             "output":{"path":str(self.output)},"clips":shots}
        if mode=="EVE_ONLY":
            doc["cast_scope"]="EVE_ONLY"
            doc["editorial_scope"]={"schema":"CASA_VIDEO_EDITORIAL_SCOPE_V1",
              "project":"CANAL_DARK","mode":"EVE_ONLY_PRIVATE_TEST",
              "gameplay_master_sha256":h(self.master),"allowed_narrators":["EVE"],
              "pre_render_report_path":str(self.report),
              "pre_render_report_sha256":h(self.report)}
        return doc

    def check(self, doc):
        with patch.object(m,"probe",side_effect=fake_probe):
            return m.validate(doc)

    def test_backward_compatible_five_voice_mode(self):
        doc=self.manifest("FIVE_VOICES")
        self.assertEqual(self.check(doc)["cast_scope"],"FIVE_VOICES")

    def test_reuses_mixer_for_single_eve_voice(self):
        doc=self.manifest()
        result=self.check(doc)
        self.assertEqual(result["cast"],["EVE"])
        self.assertEqual(result["cast_scope"],"EVE_ONLY")

    def test_reject_other_voice_in_eve_scope(self):
        doc=self.manifest()
        doc["clips"][1]["voice"]="LIA"
        with self.assertRaisesRegex(ValueError,"EVE_ONLY_REJECTS_OTHER_VOICES"):
            self.check(doc)

    def test_reject_missing_pre_render_report(self):
        doc=self.manifest()
        doc["editorial_scope"]["pre_render_report_path"]=str(self.root/"missing.json")
        with self.assertRaisesRegex(ValueError,"PRE_RENDER_REPORT_NOT_VERIFIED"):
            self.check(doc)

    def test_reject_mismatch_gate_mode(self):
        gate=json.loads(self.report.read_text())
        gate["editorial_scope_mode"]="FIVE_VOICES"
        self.report.write_text(json.dumps(gate))
        doc=self.manifest()
        doc["editorial_scope"]["pre_render_report_sha256"]=h(self.report)
        with self.assertRaisesRegex(ValueError,"PRE_RENDER_GATE_BLOCKED"):
            self.check(doc)

    def test_reject_mismatch_gate_source_sha(self):
        gate=json.loads(self.report.read_text())
        gate["source_sha256"]="f"*64
        self.report.write_text(json.dumps(gate))
        doc=self.manifest()
        doc["editorial_scope"]["pre_render_report_sha256"]=h(self.report)
        with self.assertRaisesRegex(ValueError,"PRE_RENDER_GATE_BLOCKED"):
            self.check(doc)

    def test_reject_preexisting_output_without_replay(self):
        doc=self.manifest()
        self.output.write_bytes(b"existing")
        with self.assertRaisesRegex(ValueError,"output collision or existing file"):
            self.check(doc)

if __name__=="__main__":
    unittest.main()
