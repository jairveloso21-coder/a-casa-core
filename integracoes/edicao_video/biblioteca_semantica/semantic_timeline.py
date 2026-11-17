#!/usr/bin/env python3
"""CASA Semantic Video Library v1.0: private annotations and continuity-safe EDL.
Pure Python stdlib; NO rendering, transcription, model inference or source mutation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

VERSION = "casa.semantic-video/1.0"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
EVENT_TYPES = {"setup", "action", "consequence", "payoff", "low_information"}


class ValidationError(ValueError):
    def __init__(self, errors):
        self.errors = errors
        super().__init__("\n".join(errors))


def _number(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x == x and abs(x) != float("inf")


def _positive(x):
    return _number(x) and x > 0


def _nonempty(x):
    return isinstance(x, str) and bool(x.strip())


def validate_document(doc):
    """Validate a planned editorial timeline; return non-blocking warnings.

    This checks declared provenance and timeline consistency only.
    Proof of original-file provenance requires verify_sources() on real files.
    """
    problems, warnings = [], []
    if not isinstance(doc, dict):
        raise ValidationError(["document must be a JSON object"])
    if doc.get("schema_version") != VERSION:
        problems.append(f"schema_version must be {VERSION}")
    if not _nonempty(doc.get("project_id")):
        problems.append("project_id must be a nonempty string")
    if doc.get("annotation_visibility") != "private_only":
        problems.append("annotation_visibility must be private_only")
    sources = doc.get("sources")
    events = doc.get("events")
    shots = doc.get("shots")
    if not isinstance(sources, list) or not sources:
        problems.append("sources must be a nonempty list")
        sources = []
    if not isinstance(events, list) or not events:
        problems.append("events must be a nonempty list")
        events = []
    if not isinstance(shots, list) or not shots:
        problems.append("shots must be a nonempty list")
        shots = []

    by_source, by_event = {}, {}
    for i, src in enumerate(sources):
        ctx = f"sources[{i}]"
        if not isinstance(src, dict):
            problems.append(f"{ctx} must be an object")
            continue
        sid = src.get("id")
        if not _nonempty(sid) or sid in by_source:
            problems.append(f"{ctx}.id is blank or repeated")
            continue
        by_source[sid] = src
        if not _nonempty(src.get("path")):
            problems.append(f"{ctx}.path must refer to an original recording")
        if src.get("origin") != "raw_capture" or src.get("immutable") is not True:
            problems.append(f"{ctx} must declare origin=raw_capture and immutable=true")
        if not isinstance(src.get("sha256"), str) or not SHA256.fullmatch(src["sha256"]):
            problems.append(f"{ctx}.sha256 must be 64 lowercase hex digits")
        if not _positive(src.get("duration_seconds")):
            problems.append(f"{ctx}.duration_seconds must be positive")

    for i, event in enumerate(events):
        ctx = f"events[{i}]"
        if not isinstance(event, dict):
            problems.append(f"{ctx} must be an object")
            continue
        eid = event.get("id")
        if not _nonempty(eid) or eid in by_event:
            problems.append(f"{ctx}.id is blank or repeated")
            continue
        by_event[eid] = event
        sid = event.get("source_id")
        if sid not in by_source:
            problems.append(f"{ctx}.source_id must refer to a source")
        start, end = event.get("start_seconds"), event.get("end_seconds")
        if not _number(start) or not _number(end) or start < 0 or end <= start:
            problems.append(f"{ctx} must have 0 <= start_seconds < end_seconds")
        elif sid in by_source and _positive(by_source[sid].get("duration_seconds")):
            if end > by_source[sid]["duration_seconds"] + 0.001:
                problems.append(f"{ctx} exceeds source duration")
        if not _nonempty(event.get("description_pt")):
            problems.append(f"{ctx}.description_pt must describe OBSERVED action")
        if event.get("event_type") not in EVENT_TYPES:
            problems.append(f"{ctx}.event_type unknown")
        if not _number(event.get("confidence")) or not 0 <= event["confidence"] <= 1:
            problems.append(f"{ctx}.confidence must be in [0,1]")
        elif event["confidence"] < 0.6:
            warnings.append(f"{ctx} has low confidence; requires review")
        if event.get("render_as_overlay") is not False:
            problems.append(f"{ctx}.render_as_overlay must be false")
        if not isinstance(event.get("depends_on"), list):
            problems.append(f"{ctx}.depends_on must be a list")
        ev = event.get("evidence_seconds")
        if not isinstance(ev, list) or not ev or any(not _number(t) for t in ev):
            problems.append(f"{ctx}.evidence_seconds must contain numeric timestamps")
        elif _number(start) and _number(end):
            if any(t < start - 0.001 or t > end + 0.001 for t in ev):
                problems.append(f"{ctx}.evidence_seconds must be inside event bounds")
        if event.get("result_observed") is not True and event.get("result_observed") is not False:
            problems.append(f"{ctx}.result_observed must be a boolean")

    for eid, event in by_event.items():
        deps = event.get("depends_on", [])
        if not isinstance(deps, list):
            continue
        for dep in deps:
            if dep == eid or dep not in by_event:
                problems.append(f"{eid} depends on missing/self event {dep}")
            elif by_event[dep].get("source_id") != event.get("source_id"):
                problems.append(f"{eid} depends on different source {dep}")
            elif _number(by_event[dep].get("start_seconds")) and _number(event.get("start_seconds")):
                if by_event[dep]["start_seconds"] > event["start_seconds"]:
                    problems.append(f"{eid} dependency {dep} begins later")

    seen_sources, last_end, selected_events = set(), {}, set()
    last_source = None
    for i, shot in enumerate(shots):
        ctx = f"shots[{i}]"
        if not isinstance(shot, dict):
            problems.append(f"{ctx} must be an object")
            continue
        sid = shot.get("source_id")
        if sid not in by_source:
            problems.append(f"{ctx}.source_id unknown")
            continue
        start, end = shot.get("in_seconds"), shot.get("out_seconds")
        if not _number(start) or not _number(end) or start < 0 or end <= start:
            problems.append(f"{ctx} must have 0 <= in_seconds < out_seconds")
            continue
        duration = by_source[sid].get("duration_seconds")
        if _positive(duration) and end > duration + 0.001:
            problems.append(f"{ctx} exceeds source duration")
        if sid in last_end and start < last_end[sid] - 0.001:
            problems.append(f"{ctx} reverses/overlaps the source timeline")
        if last_source is not None and sid != last_source:
            if not _nonempty(shot.get("transition_reason")):
                problems.append(f"{ctx} changes source without transition_reason")
            if sid in seen_sources:
                problems.append(f"{ctx} revisits a prior source; manual restructuring needed")
        if not _nonempty(shot.get("editorial_reason")):
            problems.append(f"{ctx}.editorial_reason required")
        linked = shot.get("event_ids")
        if not isinstance(linked, list) or not linked:
            problems.append(f"{ctx}.event_ids must contain at least one event")
            linked = []
        for eid in linked:
            event = by_event.get(eid)
            if event is None:
                problems.append(f"{ctx} references missing event {eid}")
                continue
            if event.get("source_id") != sid:
                problems.append(f"{ctx} event {eid} belongs to another source")
            elif _number(event.get("start_seconds")) and _number(event.get("end_seconds")):
                if event["start_seconds"] < start - 0.001 or event["end_seconds"] > end + 0.001:
                    problems.append(f"{ctx} truncates event {eid}; preserve full action")
            selected_events.add(eid)
        last_end[sid] = end
        seen_sources.add(sid)
        last_source = sid

    for eid in selected_events:
        event = by_event[eid]
        for dep in event.get("depends_on", []) if isinstance(event.get("depends_on"), list) else []:
            if dep in by_event and dep not in selected_events:
                problems.append(f"selected event {eid} omits causal predecessor {dep}")
    if problems:
        raise ValidationError(problems)
    return warnings


def verify_sources(doc, root):
    """Physically rehash local source recordings; never modifies them."""
    errors = []
    root = Path(root).resolve()
    for src in doc["sources"]:
        relative = Path(src["path"])
        if relative.is_absolute() or ".." in relative.parts:
            errors.append(f"{src['id']}: path must be relative and within source root")
            continue
        p = (root / relative).resolve()
        if not p.is_relative_to(root) or not p.is_file():
            errors.append(f"{src['id']}: source missing or escapes source root")
            continue
        digest = hashlib.sha256()
        with p.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != src["sha256"]:
            errors.append(f"{src['id']}: physical SHA-256 mismatch")
    if errors:
        raise ValidationError(errors)
    return True


def build_edl(doc):
    """Safe *proposed* edit decisions; no renderer is called and no captions generated."""
    warnings = validate_document(doc)
    sources = {src["id"]: src for src in doc["sources"]}
    return {
        "format": "casa.safe-edl/1.0",
        "project_id": doc["project_id"],
        "annotations_private": True,
        "render_annotations": False,
        "source_hashes": {sid: src["sha256"] for sid, src in sources.items()},
        "total_seconds": round(sum(s["out_seconds"] - s["in_seconds"] for s in doc["shots"]), 3),
        "shots": [
            {"source_id": s["source_id"], "in_seconds": s["in_seconds"],
             "out_seconds": s["out_seconds"], "event_ids": s["event_ids"],
             "editorial_reason": s["editorial_reason"],
             "transition_reason": s.get("transition_reason", "")}
            for s in doc["shots"]
        ],
        "warnings": warnings,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="CASA Semantic Video: validation and safe EDL")
    parser.add_argument("command", choices=("validate", "edl"))
    parser.add_argument("timeline", type=Path)
    parser.add_argument("--source-root", type=Path, help="Verify raw recording SHA-256 on disk")
    args = parser.parse_args(argv)
    try:
        doc = json.loads(args.timeline.read_text(encoding="utf-8"))
        warnings = validate_document(doc)
        if args.source_root:
            verify_sources(doc, args.source_root)
        result = {"valid": True, "warnings": warnings} if args.command == "validate" else build_edl(doc)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValidationError, OSError, ValueError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
