import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(r"C:\CASA_HUB\02_REPOSITORIES")
STATE_REPO = BASE_DIR / "Projetos-Arquivo"
OUTBOX_ROOT = STATE_REPO / "missions" / "outbox"
CANONICAL_STATE_FILE = STATE_REPO / "CANONICAL_SYSTEM_STATE.json"

def reconcile_outbox_receipts() -> dict:
    if CANONICAL_STATE_FILE.exists():
        state = json.loads(CANONICAL_STATE_FILE.read_text(encoding="utf-8"))
    else:
        state = {
            "schema": "CASA_CANONICAL_STATE_V16",
            "governance_baseline": "CORE_GOVERNANCE_BASELINE_ONLY",
            "scopes": {}
        }

    state["governance_baseline"] = "CORE_GOVERNANCE_BASELINE_ONLY"
    state.setdefault("scopes", {})

    processed_count = 0
    if not OUTBOX_ROOT.exists():
        return {"status": "NO_OUTBOX_DIR", "processed": 0}

    for receipt_file in sorted(OUTBOX_ROOT.rglob("*.json")):
        try:
            raw_bytes = receipt_file.read_bytes()
            receipt_hash = hashlib.sha256(raw_bytes).hexdigest()
            receipt = json.loads(raw_bytes.decode("utf-8"))

            project = receipt.get("project")
            gate = receipt.get("gate", "HOST")
            exit_code = receipt.get("exit_code", 1)
            mission_id = receipt.get("mission_id", receipt_file.stem)

            if not project:
                continue

            proj_entry = state["scopes"].setdefault(project, {
                "highest_verified_gate": "SOURCE",
                "last_receipt": None,
                "open_blockers": []
            })

            if exit_code == 0 and receipt.get("artifact_sha256"):
                proj_entry["highest_verified_gate"] = gate
                proj_entry["last_receipt"] = {
                    "mission_id": mission_id,
                    "gate": gate,
                    "receipt_sha256": receipt_hash,
                    "artifact_sha256": receipt.get("artifact_sha256"),
                    "ssh_sig_verified": bool(receipt.get("ssh_sig")),
                    "verified_at": datetime.now(timezone.utc).isoformat()
                }
                proj_entry["open_blockers"] = [
                    b for b in proj_entry.get("open_blockers", []) if b.get("gate") != gate
                ]
            else:
                proj_entry["open_blockers"] = [
                    {
                        "gate": gate,
                        "mission_id": mission_id,
                        "reason": receipt.get("error_reason", f"exit_code={exit_code}"),
                        "recorded_at": datetime.now(timezone.utc).isoformat()
                    }
                ]
            processed_count += 1
        except Exception as exc:
            print(f"[WARN] Falha ao processar recibo {receipt_file}: {exc}")

    state["last_reconciled_at"] = datetime.now(timezone.utc).isoformat()
    CANONICAL_STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"status": "RECONCILED_OK", "processed_receipts": processed_count}

if __name__ == "__main__":
    result = reconcile_outbox_receipts()
    print(json.dumps(result, indent=2, ensure_ascii=False))
