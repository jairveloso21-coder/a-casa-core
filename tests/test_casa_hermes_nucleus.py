import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / "core" / "casa_hermes_nucleus.py"
spec = importlib.util.spec_from_file_location("casa_hermes_nucleus", SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
MANIFEST = Path(__file__).resolve().parents[1] / "core" / "CASA_HERMES_NUCLEUS_V1.json"


class NucleusTests(unittest.TestCase):
    def setUp(self):
        self.m = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_seven_capabilities_no_second_orchestrator(self):
        mod.validate_manifest(self.m)
        self.assertEqual(set(self.m["capabilities"]), mod.EXPECTED)
        self.assertEqual(self.m["authority"], "CASA_CORE_ONLY")
        self.assertFalse(self.m["starts_daemon"])

    def test_fails_if_new_daemon_or_shell_or_legacy_ci(self):
        for change in ({"starts_daemon": True}, {"remote_shell": "powershell"},
                       {"primary_ci": "Forgejo"}, {"authority": "HERMES_CORE"}):
            item = json.loads(json.dumps(self.m))
            item.update(change)
            with self.subTest(change=change), self.assertRaises(mod.NucleusContractError):
                mod.validate_manifest(item)

    def test_refuses_traversal(self):
        item = json.loads(json.dumps(self.m))
        item["capabilities"]["persistent_memory"]["source_refs"][0]["path"] = "../../etc/passwd"
        with self.assertRaises(mod.NucleusContractError):
            mod.validate_manifest(item)

    def test_safe_survey_never_claims_runtime(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            report = mod.survey(root, root, MANIFEST)
            self.assertEqual(report["result_scope"], "SOURCE_CHECKOUT_ONLY")
            self.assertFalse(report["installed_on_chatgpt"])
            self.assertEqual(len(report["capabilities"]), 7)
            for cap in report["capabilities"].values():
                self.assertEqual(cap["host_current"], "NOT_TESTED")

    def test_no_receipt_no_verification(self):
        task = {"schema": "CASA_SOVEREIGN_GIT_TASK_V1", "job_id": "abc", "nonce": "123", "operation": "device.status", "target": "familia"}
        self.assertEqual(mod.receipt_gate(task, None)["status"], "WAITING_FOR_RECEIPT")

    def test_matching_git_receipt_still_not_host_attestation(self):
        task = {"schema": "CASA_SOVEREIGN_GIT_TASK_V1", "job_id": "abc", "nonce": "123", "operation": "device.status", "target": "familia"}
        digest = hashlib.sha256(json.dumps(task, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        rec = {"schema": "CASA_SOVEREIGN_GIT_RESULT_V1", "job_id": "abc", "nonce": "123", "operation": "device.status", "source": "familia", "task_sha256": digest, "status": "PASS"}
        self.assertEqual(mod.receipt_gate(task, rec)["status"], "GIT_RECEIPT_MATCH_NOT_SIGNED_VERIFICATION")
        self.assertEqual(mod.receipt_gate(task, {**rec, "nonce": "bad"})["status"], "RECEIPT_MISMATCH")
        att = {"schema": "CASA_SOVEREIGN_SIGNED_V1_ATTESTATION_V2", "device": "familia",
               "job_id": "abc", "owner": None,
               "receipt_sha256": hashlib.sha256(json.dumps(rec, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}
        self.assertEqual(mod.receipt_gate(task, rec, att)["status"], "AWAITING_INDEPENDENT_SSHSIG_VERIFIER")
        self.assertEqual(mod.receipt_gate(task, rec, {**att, "device": "unknown"}, lambda _r: True)["status"], "ATTESTATION_MISMATCH")
        self.assertEqual(mod.receipt_gate(task, rec, att, lambda _r: False)["status"], "SIGNATURE_INVALID")
        self.assertEqual(mod.receipt_gate(task, rec, att, lambda _r: True)["status"], "HOST_SIGNED_VERIFIED")


if __name__ == "__main__":
    unittest.main()
