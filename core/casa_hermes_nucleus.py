#!/usr/bin/env python3
"""CASA Core: reaproveitar 7 capacidades Hermes sem segundo orquestrador.

Leitura local de fontes e gate correlacionado. Não instala, despacha, abre
shell nem promove SOURCE a HOST/CI/DEVICE.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

EXPECTED = frozenset({
    "persistent_memory", "skills_learning", "mcp_gateway", "typed_execution",
    "subagents", "scheduled_automation", "multi_platform",
})
ROOT_TAGS = frozenset({"core", "state"})


class NucleusContractError(ValueError):
    """Falha de governança, pin, rota ou formato canônico."""


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise NucleusContractError("JSON_OBJECT_REQUIRED:" + path.name)
    return value


def _child(root: Path, relative: str) -> Path:
    """Resolve fonte dentro do repositório, rejeitando escape e links externos."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise NucleusContractError("INVALID_SOURCE_PATH")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise NucleusContractError("SOURCE_ESCAPE_ATTEMPT")
    resolved_root = root.resolve()
    resolved_path = (resolved_root / path).resolve()
    if not resolved_path.is_relative_to(resolved_root):
        raise NucleusContractError("SYMLINK_ESCAPE_ATTEMPT")
    return resolved_path


def validate_manifest(m: dict[str, Any]) -> None:
    if m.get("schema") != "CASA_HERMES_NUCLEUS_V1":
        raise NucleusContractError("UNKNOWN_SCHEMA")
    if m.get("authority") != "CASA_CORE_ONLY" or m.get("host_executor") != "EXISTING_STRICT_EXECUTOR":
        raise NucleusContractError("DUAL_ORCHESTRATOR_PROHIBITED")
    if m.get("native_chatgpt_installation") is not False or m.get("starts_daemon") is not False:
        raise NucleusContractError("FALSE_NATIVE_INSTALL_OR_DAEMON")
    caps = m.get("capabilities")
    if not isinstance(caps, dict) or set(caps) != EXPECTED:
        raise NucleusContractError("SEVEN_CAPABILITIES_REQUIRED")
    for cap_id, item in caps.items():
        if not isinstance(item, dict) or not isinstance(item.get("source_refs"), list) or not item["source_refs"]:
            raise NucleusContractError("MISSING_SOURCE_REFS:" + cap_id)
        if item.get("owner") not in {"CASA_CORE", "MOTOR_FORGE_LYA", "QWEN_CODE"}:
            raise NucleusContractError("INVALID_COMPONENT_OWNER:" + cap_id)
        if item.get("runtime") != "REUSE_EXISTING_CAPABILITY":
            raise NucleusContractError("UNAUTHORIZED_NEW_RUNTIME:" + cap_id)
        for s in item["source_refs"]:
            if not isinstance(s, dict) or s.get("root") not in ROOT_TAGS:
                raise NucleusContractError("INVALID_SOURCE_REF:" + cap_id)
            _child(Path("/"), s.get("path"))
    routes = m.get("read_only_routes", {})
    if set(routes) != {"familia_status"}:
        raise NucleusContractError("ALLOWLIST_TOO_BROAD")
    route = routes["familia_status"]
    if route != {"transport": "sovereign-git-v1", "target": "familia", "operation": "device.status", "params": {}}:
        raise NucleusContractError("INVALID_READ_ONLY_ROUTE")
    if m.get("primary_ci") != "Gitea:3002" or m.get("remote_shell") != "DISALLOWED":
        raise NucleusContractError("CI_OR_SHELL_POLICY_MISMATCH")


def survey(core_root: Path, state_root: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    """Inventaria apenas arquivos-fonte. Nunca alega processos ou QA físico."""
    src = manifest_path or _child(core_root, "core/CASA_HERMES_NUCLEUS_V1.json")
    manifest = _read_json(src)
    validate_manifest(manifest)
    roots = {"core": core_root, "state": state_root}
    items: dict[str, Any] = {}
    for cap_id, cap in manifest["capabilities"].items():
        refs = []
        for entry in cap["source_refs"]:
            path = _child(roots[entry["root"]], entry["path"])
            refs.append({
                "root": entry["root"], "path": entry["path"],
                "present_in_checkout": path.is_file(),
            })
        items[cap_id] = {
            "owner": cap["owner"], "runtime": cap["runtime"],
            "source_probe": "SOME_REFERENCES_PRESENT" if any(r["present_in_checkout"] for r in refs)
                            else "SOURCES_NOT_FOUND_IN_CHECKOUT",
            "source_refs": refs, "host_current": "NOT_TESTED",
            "device_current": "NOT_TESTED", "ci_current": "NOT_TESTED",
        }
    return {
        "schema": "CASA_HERMES_NUCLEUS_SURVEY_V1",
        "authority": "CASA_CORE_ONLY",
        "manifest_sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
        "result_scope": "SOURCE_CHECKOUT_ONLY", "installed_on_chatgpt": False,
        "creates_jobs": False, "creates_daemons": False,
        "capabilities": items, "next_gate": "EXISTING_AUTHORIZED_HOST_RECEIPT",
        "existing_familia_status_route": manifest["read_only_routes"]["familia_status"],
    }


def receipt_gate(task: dict[str, Any], receipt: dict[str, Any] | None,
                 signature_verifier: Any = None) -> dict[str, Any]:
    """Exige verificador SSHSIG confiável externo: campo JSON não é assinatura."""
    if not isinstance(task, dict) or task.get("schema") != "CASA_SOVEREIGN_GIT_TASK_V1":
        return {"status": "INVALID_TASK", "host_verified": False}
    if not isinstance(receipt, dict):
        return {"status": "WAITING_FOR_RECEIPT", "host_verified": False}
    canonical = json.dumps(task, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    expected = hashlib.sha256(canonical).hexdigest()
    if any((receipt.get("job_id") != task.get("job_id"),
            receipt.get("nonce") != task.get("nonce"),
            receipt.get("task_sha256") != expected,
            receipt.get("operation") != task.get("operation"),
            receipt.get("source") != task.get("target"),
            receipt.get("schema") != "CASA_SOVEREIGN_GIT_RESULT_V1")):
        return {"status": "RECEIPT_MISMATCH", "host_verified": False}
    if receipt.get("status") != "PASS":
        return {"status": "HOST_FAILED_OR_UNCONFIRMED", "host_verified": False}
    if not callable(signature_verifier):
        return {"status": "GIT_RECEIPT_MATCH_NOT_SIGNED_VERIFICATION", "host_verified": False}
    try:
        verified = signature_verifier(receipt)
    except (OSError, ValueError):
        verified = False
    return {"status": "HOST_SIGNED_VERIFIED" if verified is True else "SIGNATURE_INVALID",
            "host_verified": verified is True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--core-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(survey(args.core_root, args.state_root), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "reason": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
