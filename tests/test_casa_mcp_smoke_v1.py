import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

P = Path(__file__).resolve().parents[1] / "core" / "casa_mcp_smoke_v1.py"
spec = importlib.util.spec_from_file_location("casa_mcp_smoke_v1", P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

CAT = {"schema": m.CATALOG_SCHEMA, "entries": [
    {"id": "tool-" + str(i), "host": "FAMILIA", "domain": "qa"} for i in range(96)
] + [{"id": "forgejo-ci", "host": "FAMILIA"}]}
PROBES = {"schema": m.PROBES_SCHEMA, "probes": {
    "tool-0": {"transport": "http",
               "url": "http://127.0.0.1:11434/api/version", "required_field": "version"},
    "gitea-ci": {"transport": "http",
                 "url": "http://127.0.0.1:3002/api/v1/version", "required_field": "version"}
}}

class SmokeTests(unittest.TestCase):
    def test_97_entries_exact(self):
        self.assertEqual(len(m.verify_catalog(CAT, PROBES)), 97)
        bad = dict(CAT)
        bad["entries"] = CAT["entries"][:-1]
        with self.assertRaisesRegex(ValueError, "97"):
            m.verify_catalog(bad, PROBES)

    def test_loopback_only(self):
        for url in ["http://evil.invalid/health", "http://127.0.0.1:5555/health",
                    "https://127.0.0.1:3002/api/v1/version",
                    "http://127.0.0.1:3002/api/v1/version?token=x",
                    "http://localhost:3002/../../secret"]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                m.check_url(url)

    def test_200_unauthed_cannot_promote(self):
        r = m.http_check(PROBES["probes"]["tool-0"],
                         requester=lambda: (200, b'{"version":"1.2"}'))
        self.assertEqual(r["status"], "HTTP_200_LOCAL_HEALTH")
        self.assertFalse(r["eligible"])

    def test_403_even_with_credentials_not_homologation(self):
        spec = {**PROBES["probes"]["tool-0"], "auth_env": "CASA_MCP_TEST_TOKEN"}
        r = m.http_check(spec, requester=lambda: (403, b'{"detail":"forbidden"}'),
                         env={"CASA_MCP_TEST_TOKEN": "secret"})
        self.assertEqual(r["status"], "REACHABLE_AUTH_DENIED")
        self.assertFalse(r["eligible"])
        self.assertNotIn("secret", json.dumps(r))

    def test_authenticated_operation_proof_only(self):
        spec = {**PROBES["probes"]["tool-0"], "auth_env": "CASA_MCP_TEST_TOKEN",
                "identity_field": "user", "identity_expected": "owner",
                "operation_field": "allowed"}
        r = m.http_check(spec,
                         requester=lambda: (200, b'{"version":"1.0","user":"owner","allowed":true}'),
                         env={"CASA_MCP_TEST_TOKEN": "secret"})
        self.assertEqual(r["status"], "AUTHENTICATED_OPERATION_SMOKE_PASS")
        self.assertTrue(r["eligible"])

    def test_no_remote_or_legacy_auto_activation(self):
        r = m.run(CAT, PROBES, {}, Path("catalog"), Path("state"),
                  machine="FAMILIA", http_requester=lambda: (200, b'{"version":"0.0"}'))
        self.assertEqual(len(r["rows"]), 97)
        self.assertEqual(r["canonical_activations"], 0)
        self.assertFalse(r["state_mutated"])
        self.assertEqual(next(x for x in r["rows"] if x["id"]=="forgejo-ci")["status"],
                         "RETIRED_ROUTE_DISABLED")
        self.assertEqual(r["rows"][0]["status"], "HTTP_200_LOCAL_HEALTH")

    def test_unknown_auth_env_rejected(self):
        with self.assertRaises(ValueError):
            m.http_check({**PROBES["probes"]["tool-0"], "auth_env": "HOME"},
                         requester=lambda: (200, b'{}'))

    def test_report_bytes_are_binary_sha_stable(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / "report.json"
            payload = ('{"rows":[1,2]}\n').encode("utf-8")
            with p.open("xb") as out:
                out.write(payload)
            self.assertEqual(p.read_bytes(), payload)
            self.assertEqual(m.digest(p), m.hashlib.sha256(payload).hexdigest())

    def test_no_execution_on_other_machine(self):
        r = m.run(CAT, PROBES, {}, Path("catalog"), Path("state"), machine="OTHER")
        self.assertEqual(r["rows"][0]["status"], "HOST_GATE_NOT_EXECUTED")
        self.assertFalse(r["transport_probes_performed"])

if __name__ == "__main__":
    unittest.main()
