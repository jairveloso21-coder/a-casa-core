#!/usr/bin/env python3
"""CASA reusable five-voice audiovisual mixer for an approved video master.

Media are never uploaded, overwritten, or republished by this tool. It rejects
unverified audio and rejected voice fingerprints. All paths/data are project scoped.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import wave

REJECTED_WAV_SHA = {
    "d0081a95cb08e9c77604dedb8e050888195ffba2887316157851eec319d9da02",  # R4
    "f682fedf72da80b60e26cb67cd2f9591571efd830be0049721296523520e82eb",  # R5
}
CAST = {"EVE", "GUARDIAO", "TROVAO", "NINO", "LIA"}


def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for buf in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(buf)
    return h.hexdigest()


def run(cmd: list[str], timeout: int = 10800) -> subprocess.CompletedProcess:
    v = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", stdin=subprocess.DEVNULL, timeout=timeout,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    if v.returncode:
        raise RuntimeError(f"command exit {v.returncode}: {v.stderr[-800:]}")
    return v


def probe(p: Path) -> dict:
    return json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format",
                           "-of", "json", str(p)], 180).stdout)


def validate(manifest: dict, *, check_media=True) -> dict:
    if manifest.get("schema") != "CASA_FIVE_VOICE_MIX_V1":
        raise ValueError("schema mismatch")
    movie = Path(manifest["master"]["path"])
    dest = Path(manifest["output"]["path"])
    if dest.resolve() == movie.resolve() or dest.exists():
        raise ValueError("output collision or existing file; no replay")
    if movie.is_symlink() or not movie.is_file():
        raise ValueError("master missing or symlink")
    master_sha = digest(movie)
    if master_sha != manifest["master"]["sha256"]:
        raise ValueError("master SHA mismatch")
    p = probe(movie)
    video = next((s for s in p["streams"] if s["codec_type"] == "video"), None)
    audio = next((s for s in p["streams"] if s["codec_type"] == "audio"), None)
    if not video or not audio or video.get("codec_name") != "h264" or audio.get("codec_name") != "aac":
        raise ValueError("master must have H264/AAC")
    if int(video["width"]) <= int(video["height"]):
        raise ValueError("target video must be horizontal")
    if manifest["master"].get("require_bt709"):
        if any(video.get(k) != "bt709" for k in ("color_primaries", "color_transfer", "color_space")):
            raise ValueError("R5 color not verified SDR BT709: correct source render first")
    duration = float(p["format"]["duration"])
    if not math.isclose(duration, float(manifest["master"]["duration_seconds"]), abs_tol=0.15):
        raise ValueError("master duration drift")
    # R13 five-voice behavior is the default, preserved byte-for-byte at the
    # contract level. Project-specified single narration reuses THIS mixer.
    cast_scope = manifest.get("cast_scope", "FIVE_VOICES")
    if cast_scope not in ("FIVE_VOICES", "EVE_ONLY"):
        raise ValueError("unknown cast scope")
    shots = manifest.get("clips", [])
    min_clips = 3 if cast_scope == "EVE_ONLY" else 5
    if not isinstance(shots, list) or not min_clips <= len(shots) <= 18:
        raise ValueError("wrong individually reviewed clip count")
    if any(not isinstance(s, dict) for s in shots):
        raise ValueError("invalid clip entry")
    names = {x.get("voice") for x in shots}
    if cast_scope == "FIVE_VOICES":
        if names != CAST:
            raise ValueError(f"five voices required, found {sorted(str(x) for x in names)}")
    else:
        if names != {"EVE"}:
            raise ValueError("EVE_ONLY_REJECTS_OTHER_VOICES")
        editorial = manifest.get("editorial_scope")
        if not isinstance(editorial, dict) or editorial.get("schema") != "CASA_VIDEO_EDITORIAL_SCOPE_V1":
            raise ValueError("EDITORIAL_SCOPE_MISSING")
        if (editorial.get("project") != "CANAL_DARK"
                or editorial.get("mode") != "EVE_ONLY_PRIVATE_TEST"
                or editorial.get("gameplay_master_sha256") != master_sha
                or editorial.get("allowed_narrators") != ["EVE"]):
            raise ValueError("EDITORIAL_SOURCE_OR_CAST_MISMATCH")
        # The R8 candidate already contains four other narration tracks.
        if master_sha == "48e74edfa88f6b30fcece706ce39b89a4e4b5a65c3f88549ff22960d94709b54":
            raise ValueError("MIXED_R8_IS_NOT_CLEAN_MASTER")
        # Verify the physical bytes of the CASA release-gate's SOURCE report.
        # This is not a signature or a substitute for a HOST-signed receipt.
        report_path = Path(editorial.get("pre_render_report_path", ""))
        report_sha = editorial.get("pre_render_report_sha256")
        if (not report_path.is_file() or report_path.is_symlink()
                or not isinstance(report_sha, str) or len(report_sha) != 64
                or digest(report_path) != report_sha):
            raise ValueError("PRE_RENDER_REPORT_NOT_VERIFIED")
        try:
            gate = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ValueError("PRE_RENDER_REPORT_INVALID") from exc
        if (gate.get("schema") != "CASA_VIDEO_RELEASE_GATE_RESULT_V2"
                or gate.get("phase") != "pre_render"
                or gate.get("passed") is not True
                or gate.get("release_status") != "PREFLIGHT_READY"
                or gate.get("source_sha256") != master_sha
                or gate.get("editorial_scope_mode") != "EVE_ONLY_PRIVATE_TEST"):
            raise ValueError("PRE_RENDER_GATE_BLOCKED")
    ordered = sorted(shots, key=lambda x: x["at"])
    previous_end = 0.
    signals = []
    for i, clip in enumerate(ordered):
        start = float(clip["at"])
        end = float(clip["until"])
        if start < previous_end - .05 or end <= start or end > duration - .1:
            raise ValueError(f"overlap or out-of-bounds clip {i}")
        previous_end = end
        path = Path(clip["path"])
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"missing vocal stem {i}: {path.name}")
        signature = digest(path)
        if signature in REJECTED_WAV_SHA or signature != clip["sha256"]:
            raise ValueError(f"rejected or unverified voice stem {i}")
        if clip.get("qa", {}).get("technical_pass") is not True:
            raise ValueError(f"audio technical QA missing {i}")
        if clip.get("qa", {}).get("ptbr_natural_review") != "APPROVED":
            raise ValueError(f"natural Brazilian accent not approved {i}")
        if clip.get("qa", {}).get("voice_identity_review") != "APPROVED":
            raise ValueError(f"voice identity not approved {i}")
        if clip.get("qa", {}).get("reviewer") != "owner" or not clip.get("qa", {}).get("review_evidence"):
            raise ValueError(f"owner review evidence missing {i}")
        if not clip.get("text") or not clip.get("scene_evidence_seconds"):
            raise ValueError(f"text or real frame anchor missing {i}")
        if not start - 5 <= float(clip["scene_evidence_seconds"]) <= end + 5:
            raise ValueError(f"scene observation not near clip {i}")
        with wave.open(str(path), "rb") as f:
            if f.getnchannels() not in (1, 2) or f.getsampwidth() != 2 or f.getframerate() < 16000:
                raise ValueError(f"voice WAV format invalid {i}")
            secs = f.getnframes() / f.getframerate()
            if secs < .5 or secs > end - start - .1:
                raise ValueError(f"voice clip longer than scene window {i}")
        signals.append({"voice": clip["voice"], "sha256": signature,
                        "seconds": round(secs, 3), "at": start, "until": end})
    if cast_scope == "FIVE_VOICES":
        if not (ordered[0]["at"] < 40 and any(60 <= x["at"] <= 120 for x in ordered)
                and any(x["at"] > 130 for x in ordered)):
            raise ValueError("speech must be spread from opening through climax")
    else:
        zones = {int(min(2, float(s["at"]) * 3 / duration)) for s in ordered}
        if zones != {0, 1, 2}:
            raise ValueError("EVE_NARRATION_NOT_DISTRIBUTED")
    if len(set(round(x["at"] / 5) for x in ordered)) != len(ordered):
        raise ValueError("clustered voice placement")
    return {"status": "PREFLIGHT_PASS", "cast": sorted(names), "cast_scope": cast_scope, "master_sha256": master_sha,
            "master_duration_seconds": duration, "clips": signals,
            "editorial_release_approved": False}


def render(manifest: dict) -> dict:
    state = validate(manifest)
    movie = Path(manifest["master"]["path"])
    target = Path(manifest["output"]["path"])
    target.parent.mkdir(parents=True, exist_ok=True)
    pending = target.with_suffix(".pending.mp4")
    if pending.exists():
        raise ValueError("existing in-progress output; no replay")
    clips = sorted(manifest["clips"], key=lambda x: x["at"])
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-xerror", "-n",
           "-i", str(movie)]
    for clip in clips:
        cmd += ["-i", str(clip["path"])]
    filters = []
    for i, clip in enumerate(clips, 1):
        ms = round(float(clip["at"]) * 1000)
        filters.append(f"[{i}:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                       f"volume=0.9,adelay={ms}|{ms}[voice{i}]")
    joined = "".join(f"[voice{i}]" for i in range(1, len(clips) + 1))
    filters.append(f"{joined}amix=inputs={len(clips)}:duration=longest:normalize=0,"
                   f"apad=whole_dur={state['master_duration_seconds']},"
                   f"atrim=duration={state['master_duration_seconds']},asplit=2[sidechain][voiceout]")
    filters.append("[0:a]aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[game]")
    filters.append("[game][sidechain]sidechaincompress=threshold=0.03:ratio=3:attack=45:release=500[ducked]")
    filters.append("[ducked][voiceout]amix=inputs=2:duration=first:normalize=0,"
                   "loudnorm=I=-14:TP=-1.5:LRA=9[mixed]")
    cmd += ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[mixed]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "320k", "-ar", "48000",
            "-ac", "2", "-movflags", "+faststart", str(pending)]
    try:
        run(cmd)
        meta = probe(pending)
        v = next(x for x in meta["streams"] if x["codec_type"] == "video")
        a = next(x for x in meta["streams"] if x["codec_type"] == "audio")
        if v["codec_name"] != "h264" or a["codec_name"] != "aac":
            raise RuntimeError("output codecs wrong")
        if not math.isclose(float(meta["format"]["duration"]), state["master_duration_seconds"], abs_tol=.2):
            raise RuntimeError("output duration changed")
        run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-xerror",
             "-i", str(pending), "-f", "null", "-"])
        os.replace(pending, target)
        state.update({"status": "CANDIDATE_RENDERED_TECH_PASS_EXECUTOR_UNATTESTED", "output_sha256": digest(target),
                      "output_bytes": target.stat().st_size, "output_path": str(target),
                      "full_decode_pass": True, "editorial_release_approved": False})
    except Exception:
        # Leave pending output for forensic inspection; never silently re-run a failing effect.
        raise
    return state


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["verify", "render"])
    ap.add_argument("manifest", type=Path)
    ap.add_argument("--receipt", type=Path)
    args = ap.parse_args()
    result = None
    try:
        data = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = validate(data) if args.action == "verify" else render(data)
        code = 0
    except Exception as exc:
        result = {"status": "BLOCKED", "error": str(exc), "action": args.action}
        code = 2
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        if args.receipt.exists():
            print(json.dumps({"status": "BLOCKED", "error": "receipt already exists"}))
            return 3
        args.receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return code

if __name__ == "__main__":
    sys.exit(main())
