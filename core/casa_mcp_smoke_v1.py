#!/usr/bin/env python3
"""CASA: smoke real, local e sem alterações para o catálogo canônico de 97 IDs.

Um HTTP 403 indica resposta + recusa, não credencial aceita. HTTP 200 sem
operação autenticada também NÃO autoriza ativação automática. Roda on-demand,
sem shell arbitrário, instalação, watcher ou transferência de credenciais.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import urlsplit

SCHEMA = "CASA_MCP_CONNECTOR_SMOKE_V1"
CATALOG_SCHEMA = "CASA_OPEN_SOURCE_INTEGRATIONS_V2"
PROBES_SCHEMA = "CASA_MCP_PINNED_SMOKE_PROBES_V1"
ID = re.compile(r"^[a-z0-9][a-z0-9._-]{1,99}$")
SHA = re.compile(r"^[a-f0-9]{64}$")
MAX_BYTES = 4_000_000
MAX_HTTP_BYTES = 600_000
TIMEOUT = 4
LOCAL_HOSTS = {"127.0.0.1", "localhost"}
VALID_PORTS = {11434, 3900, 3002}
MCP_FILENAME = "casa_global_mcp_bridge.py"
MCP_ROOT = Path(r"C:\CASA_HUB\01_CORE_SYSTEM\tools\casa-global-tool-routing-v1")
MCP_TRUSTED_STATE_KEY = "r16_mcp_utf8_host_fix"


def load(path: Path) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_BYTES:
        raise ValueError("INVALID_SOURCE_FILE")
    item = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(item, dict):
        raise ValueError("OBJECT_REQUIRED")
    return item


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_url(url: str) -> tuple[str, int, str]:
    if not isinstance(url, str):
        raise ValueError("URL_STRING_REQUIRED")
    parsed = urlsplit(url)
    if (parsed.scheme != "http" or parsed.hostname not in LOCAL_HOSTS
            or parsed.username or parsed.password or parsed.fragment or parsed.query
            or parsed.port not in VALID_PORTS):
        raise ValueError("UNTRUSTED_ENDPOINT")
    if parsed.path not in ("/api/version", "/api/v1/version", "/health", "/openapi.json"):
        raise ValueError("UNAPPROVED_HEALTH_PATH")
    return parsed.hostname, parsed.port, parsed.path


def http_check(spec: dict, requester=None, env=None) -> dict:
    """Nunca redireciona; tokens apenas de ambiente local, nunca no recibo."""
    env = os.environ if env is None else env
    host, port, path = check_url(spec.get("url"))
    auth_env = spec.get("auth_env")
    headers = {"Accept": "application/json", "Connection": "close"}
    has_token = False
    if auth_env is not None:
        if not isinstance(auth_env, str) or not re.fullmatch(r"CASA_MCP_[A-Z0-9_]{3,70}", auth_env):
            raise ValueError("UNSAFE_AUTH_ENV")
        token = env.get(auth_env, "")
        if token:
            has_token = True
            headers["Authorization"] = "Bearer " + token
    def request():
        conn = http.client.HTTPConnection(host, port, timeout=TIMEOUT)
        try:
            conn.request("GET", path, headers=headers)
            rsp = conn.getresponse()
            code = rsp.status
            data = rsp.read(MAX_HTTP_BYTES + 1)
            return code, data
        finally:
            conn.close()
    try:
        code, raw = requester() if requester is not None else request()
    except (OSError, TimeoutError, http.client.HTTPException):
        return {"status": "UNREACHABLE", "connected": False, "eligible": False}
    result = {"status": "HTTP_UNEXPECTED", "http_status": code,
              "connected": code in (200, 401, 403), "eligible": False,
              "credential_supplied": has_token}
    if code in (401, 403):
        result["status"] = "REACHABLE_AUTH_DENIED"
        return result
    if code != 200 or len(raw) > MAX_HTTP_BYTES:
        return result
    try:
        body = json.loads(raw)
    except (ValueError, UnicodeError):
        return {**result, "status": "HTTP_200_INVALID_JSON"}
    if not isinstance(body, dict) or spec.get("required_field") not in body:
        return {**result, "status": "HTTP_200_HEALTH_SCHEMA_MISMATCH"}
    result["status"] = "HTTP_200_LOCAL_HEALTH"
    # An externally supplied Bearer is NOT enough to prove authentication.
    ident_field = spec.get("identity_field")
    expected = spec.get("identity_expected")
    operation_key = spec.get("operation_field")
    if (has_token and isinstance(ident_field, str)
            and isinstance(expected, str) and expected
            and body.get(ident_field) == expected
            and isinstance(operation_key, str) and body.get(operation_key) is True):
        result["status"] = "AUTHENTICATED_OPERATION_SMOKE_PASS"
        result["eligible"] = True
        result["identity_verified"] = True
    return result


def mcp_stdio_check(spec: dict, state: dict, catalog_path: Path,
                    state_path: Path, python_exe: str | None = None) -> dict:
    """Executa somente script CASA fixo, com SHA conhecido, sem shell."""
    entry = state.get("global_tools_mcp_capability", {}).get(MCP_TRUSTED_STATE_KEY, {})
    expected = entry.get("installed_bridge_sha256")
    if not isinstance(expected, str) or not SHA.fullmatch(expected):
        return {"status": "MCP_UNPINNED", "eligible": False}
    binary = MCP_ROOT / MCP_FILENAME
    if binary.is_symlink() or not binary.is_file() or binary.stat().st_size > 180000:
        return {"status": "MCP_NOT_INSTALLED", "eligible": False}
    actual = digest(binary)
    if actual != expected:
        return {"status": "MCP_INSTALLED_HASH_DRIFT", "eligible": False,
                "installed_sha256": actual}
    exe = python_exe or sys.executable
    reqs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "casa_list_global_tools", "arguments": {"limit": 1}}},
    ]
    payload = "\n".join(json.dumps(req) for req in reqs) + "\n"
    try:
        cp = subprocess.run([exe, "-B", str(binary), "--catalog", str(catalog_path),
                             "--state", str(state_path)], input=payload, text=True,
                            capture_output=True, timeout=12, check=False,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        if cp.returncode or len(cp.stdout) > 20000:
            return {"status": "MCP_STDIO_FAILED", "eligible": False}
        replies = [json.loads(x) for x in cp.stdout.splitlines() if x.strip()]
        if len(replies) != 3 or any("error" in x for x in replies):
            return {"status": "MCP_PROTOCOL_FAILED", "eligible": False}
        names = [t["name"] for t in replies[1]["result"]["tools"]]
        tools_call = json.loads(replies[2]["result"]["content"][0]["text"])
        if ("casa_list_global_tools" not in names
                or tools_call.get("schema") != "CASA_MCP_GLOBAL_DISCOVERY_V1"):
            return {"status": "MCP_TOOL_CALL_FAILED", "eligible": False}
        return {"status": "MCP_READONLY_STDIO_PASS", "connected": True,
                "eligible": False, "tool_count": len(names),
                "installed_sha256": actual,
                "canonical_operation_verified": False}
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
        return {"status": "MCP_PROTOCOL_FAILED", "eligible": False}


def verify_catalog(catalog: dict, probes: dict) -> list[dict]:
    if catalog.get("schema") != CATALOG_SCHEMA or probes.get("schema") != PROBES_SCHEMA:
        raise ValueError("SCHEMA_MISMATCH")
    items = catalog.get("entries")
    if not isinstance(items, list) or len(items) != 97:
        raise ValueError("EXPECTED_97_CATALOG_ENTRIES")
    ids = [x.get("id") if isinstance(x, dict) else None for x in items]
    if any(not isinstance(x, str) or not ID.fullmatch(x) for x in ids) or len(set(ids)) != 97:
        raise ValueError("CATALOG_IDS_NOT_UNIQUE")
    defined = probes.get("probes")
    if not isinstance(defined, dict) or set(defined) - (set(ids) | {"gitea-ci"}):
        raise ValueError("PROBE_OUTSIDE_CANONICAL_CATALOG")
    for name, spec in defined.items():
        if not isinstance(spec, dict) or set(spec) - {"transport", "url", "required_field",
                 "auth_env", "identity_field", "identity_expected", "operation_field"}:
            raise ValueError("PROBE_SCHEMA_NOT_ALLOWED:" + name)
        if spec.get("transport") == "http":
            check_url(spec.get("url"))
            if spec.get("required_field") not in {"version", "status", "paths"}:
                raise ValueError("INVALID_HTTP_HEALTH_SCHEMA")
        elif spec != {"transport": "casa-global-stdio"} or name != "casa-global-tools-mcp":
            raise ValueError("UNKNOWN_TRANSPORT")
    return items


def run(catalog: dict, probes: dict, state: dict, catalog_path: Path,
        state_path: Path, machine: str | None = None, dry_run: bool = False,
        http_requester=None) -> dict:
    items = verify_catalog(catalog, probes)
    machine = (machine if machine is not None else os.environ.get("COMPUTERNAME", "")).upper()
    rows = []
    for item in items:
        key = item["id"]
        spec = probes["probes"].get(key)
        if item.get("host") in ("UNRESOLVED", "REVIEW_ONLY", "SOURCE_ONLY", "REMOTE_UNRESOLVED"):
            status = {"status": "QUARANTINED_NO_VERIFIED_LOCAL_HOST", "eligible": False}
        elif key == "forgejo-ci":
            status = {"status": "RETIRED_ROUTE_DISABLED", "eligible": False}
        elif not spec:
            status = {"status": "NO_PINNED_LOCAL_PROBE", "eligible": False}
        elif machine != "FAMILIA" or dry_run:
            status = {"status": "HOST_GATE_NOT_EXECUTED", "eligible": False}
        elif spec["transport"] == "http":
            status = http_check(spec, requester=http_requester)
        else:
            status = mcp_stdio_check(spec, state, catalog_path, state_path)
        rows.append({"id": key, "host": item.get("host"),
                     "transport": spec["transport"] if spec else None, **status})
    # Gitea is infrastructure, never a renamed Forgejo catalog entry.
    infra = {}
    spec = probes["probes"].get("gitea-ci")
    if spec:
        infra = (http_check(spec, requester=http_requester)
                 if machine == "FAMILIA" and not dry_run
                 else {"status": "HOST_GATE_NOT_EXECUTED", "eligible": False})
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    eligible = [r["id"] for r in rows if r.get("eligible") is True]
    return {"schema": SCHEMA, "host": machine, "catalog_count": len(rows),
            "source_only": False, "transport_probes_performed": not dry_run and machine == "FAMILIA",
            "counts": dict(sorted(counts.items())), "rows": rows,
            "infrastructure_gitea": infra, "eligible_candidates": eligible,
            "canonical_activations": 0, "state_mutated": False,
            "signature_independently_verified": False,
            "promotion_gate": "SIGNED_RECEIPT_AND_INDEPENDENT_SSHSIG_AND_CORE_PROJECT_POLICY",
            "evaluated_at_utc": datetime.now(timezone.utc).isoformat()}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--catalog", type=Path, required=True)
    p.add_argument("--state", type=Path, required=True)
    p.add_argument("--probes", type=Path, required=True)
    p.add_argument("--output", type=Path)
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()
    try:
        report = run(load(a.catalog), load(a.probes), load(a.state),
                     a.catalog, a.state, dry_run=a.dry_run)
        report["catalog_sha256"] = digest(a.catalog)
        report["probe_manifest_sha256"] = digest(a.probes)
        raw = (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        if a.output:
            if a.output.is_symlink() or not a.output.parent.is_dir():
                raise ValueError("OUTPUT_DIRECTORY_UNAVAILABLE")
            payload = raw.encode("utf-8")
            # Binary mode avoids Windows CRLF rewriting that invalidated R1 SHA.
            with a.output.open("xb") as out:
                out.write(payload)
            with a.output.open("rb") as inp:
                on_disk = hashlib.sha256(inp.read()).hexdigest()
            if on_disk != hashlib.sha256(payload).hexdigest():
                raise ValueError("REPORT_READBACK_SHA256_MISMATCH")
            print(json.dumps({"status": "REPORT_CREATED", "path": str(a.output),
                              "sha256": on_disk,
                              "counts": report["counts"], "gitea": report["infrastructure_gitea"],
                              "activations": 0}, sort_keys=True))
        else:
            print(raw)
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(json.dumps({"status": "FAILED_CLOSED", "reason": str(e)[:150]}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
