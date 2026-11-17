#!/usr/bin/env python3
"""CASA Video Lab: reusable audit of social-video exports (stdlib + ffprobe/ffmpeg).

No editing, downloads, file deletion, background process, watermark or text overlays.
Semantics remain private. Provenance is verified against a caller-supplied manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

SCHEMA = 'casa.video.export-qa/1.0'


def checksum(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def local_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ValueError('file paths must be relative to the supplied root')
    resolved_root = root.resolve()
    dest = (resolved_root / relative).resolve()
    if not dest.is_relative_to(resolved_root):
        raise ValueError('file path escapes supplied root')
    return dest


def run_checked(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess:
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout, check=False)


def probe_video(path: Path) -> dict:
    result = run_checked(['ffprobe', '-v', 'error', '-show_streams', '-show_format',
                          '-of', 'json', str(path)])
    if result.returncode:
        raise ValueError(f'ffprobe failed for {path.name}: {result.stderr[-300:]}')
    return json.loads(result.stdout)


def integrated_loudness(path: Path) -> dict:
    """Measure INPUT loudness, without modifying audio. Returns integrated LUFS and dBTP."""
    r = run_checked(['ffmpeg', '-hide_banner', '-nostdin', '-v', 'info', '-i', str(path),
                     '-vn', '-af', 'loudnorm=I=-18:TP=-1.5:LRA=11:print_format=json',
                     '-f', 'null', '-'], timeout=180)
    if r.returncode:
        raise ValueError(f'loudness measurement failed: {r.stderr[-300:]}')
    matches = re.findall(r'\{\s*"input_i"\s*:.*?\}', r.stderr, flags=re.DOTALL)
    if not matches:
        raise ValueError('ffmpeg did not return EBU loudness JSON')
    data = json.loads(matches[-1])
    return {'lufs': float(data['input_i']), 'true_peak_dbtp': float(data['input_tp'])}


def decode_whole_video(path: Path) -> None:
    r = run_checked(['ffmpeg', '-hide_banner', '-nostdin', '-v', 'error', '-xerror',
                     '-i', str(path), '-f', 'null', '-'], timeout=240)
    if r.returncode:
        raise ValueError(f'full decode failed: {r.stderr[-300:]}')


def check_manifest(data: dict) -> None:
    if not isinstance(data, dict) or data.get('schema_version') != SCHEMA:
        raise ValueError('unsupported manifest schema')
    if data.get('annotations_private') is not True or data.get('render_semantic_text') is not False:
        raise ValueError('semantic descriptions must be private and never rendered')
    if not isinstance(data.get('sources'), list) or not data['sources']:
        raise ValueError('sources must be a non-empty list')
    if not isinstance(data.get('exports'), list) or not data['exports']:
        raise ValueError('exports must be a non-empty list')
    source_ids = set()
    for src in data['sources']:
        if not isinstance(src, dict) or src.get('origin') != 'raw_capture':
            raise ValueError('source must be labeled raw_capture')
        if not src.get('id') or src['id'] in source_ids:
            raise ValueError('source IDs must be unique and nonempty')
        if not re.fullmatch(r'[0-9a-f]{64}', src.get('sha256', '')):
            raise ValueError('source hash must be sha256')
        if not isinstance(src.get('duration_seconds'), (int, float)) or src['duration_seconds'] <= 0:
            raise ValueError('source duration must be positive')
        source_ids.add(src['id'])
    for export in data['exports']:
        if not isinstance(export, dict) or export.get('source_id') not in source_ids:
            raise ValueError('export source_id unknown')
        if export.get('format') not in ('short', 'youtube_horizontal'):
            raise ValueError('export format must be short or youtube_horizontal')
        if not re.fullmatch(r'[0-9a-f]{64}', export.get('sha256', '')):
            raise ValueError('export hash must be sha256')
        start, end = export.get('in_seconds'), export.get('out_seconds')
        if (not isinstance(start, (int, float)) or not isinstance(end, (int, float))
                or isinstance(start, bool) or isinstance(end, bool)
                or not 0 <= start < end):
            raise ValueError('export must have 0 <= in_seconds < out_seconds')
        source = next(s for s in data['sources'] if s['id'] == export['source_id'])
        if end > source['duration_seconds'] + .1:
            raise ValueError('export exceeds duration of original')


def overlaps(data: dict) -> list[dict]:
    """Detect temporal overlap among short-form exports of a single original."""
    shorts = [e for e in data['exports'] if e['format'] == 'short']
    collisions = []
    for i, left in enumerate(shorts):
        for right in shorts[i+1:]:
            if left['source_id'] != right['source_id']:
                continue
            overlap = max(0., min(left['out_seconds'], right['out_seconds']) -
                          max(left['in_seconds'], right['in_seconds']))
            if overlap > .05:
                collisions.append({'a': left['file'], 'b': right['file'],
                                   'overlap_seconds': round(overlap, 3)})
    return collisions


def audit(data: dict, export_root: Path, source_root: Path,
          media_tools: bool = True) -> dict:
    check_manifest(data)
    result = {'schema_version': SCHEMA, 'ok': True, 'files': [], 'batch_issues': [],
              'media_tools_executed': media_tools}
    src_by_id = {s['id']: s for s in data['sources']}
    for src in data['sources']:
        try:
            path = local_file(source_root, src['file'])
            if not path.is_file() or checksum(path) != src['sha256']:
                result['batch_issues'].append('original missing or SHA-256 mismatch: ' + src['id'])
        except (KeyError, OSError, ValueError) as e:
            result['batch_issues'].append('source error: ' + str(e))
    for export in data['exports']:
        row = {'file': export['file'], 'issues': []}
        try:
            path = local_file(export_root, export['file'])
            if not path.is_file() or checksum(path) != export['sha256']:
                raise ValueError('missing file or export SHA-256 mismatch')
            row['sha256_ok'] = True
            if media_tools:
                info = probe_video(path)
                video = next((s for s in info['streams'] if s['codec_type'] == 'video'), None)
                audio = next((s for s in info['streams'] if s['codec_type'] == 'audio'), None)
                if not video or video.get('codec_name') != 'h264':
                    row['issues'].append('expected H.264 video stream')
                if not audio or audio.get('codec_name') != 'aac':
                    row['issues'].append('expected AAC audio stream')
                if video:
                    width, height = video.get('width', 0), video.get('height', 0)
                    if export['format'] == 'short' and not height > width:
                        row['issues'].append('short must be portrait')
                    if export['format'] == 'youtube_horizontal' and not width > height:
                        row['issues'].append('YouTube must be landscape')
                    row['resolution'] = [width, height]
                    for attr in ('color_primaries', 'color_transfer', 'color_space'):
                        if video.get(attr) != 'bt709':
                            row['issues'].append(f'{attr} not BT.709')
                duration = float(info['format']['duration'])
                expected = export['out_seconds'] - export['in_seconds']
                row['duration_seconds'] = duration
                if abs(duration - expected) > .15:
                    row['issues'].append(f'duration {duration:.2f}s != expected {expected:.2f}s')
                loud = integrated_loudness(path)
                row.update(loud)
                if not -21.0 <= loud['lufs'] <= -15.0:
                    row['issues'].append(f'loudness outside pilot target ±3 LU: {loud["lufs"]}')
                if loud['true_peak_dbtp'] > -1.5:
                    row['issues'].append(f'true peak exceeds -1.5 dBTP: {loud["true_peak_dbtp"]}')
                decode_whole_video(path)
                row['full_decode'] = 'pass'
        except (KeyError, OSError, ValueError, subprocess.TimeoutExpired) as e:
            row['issues'].append(str(e))
        result['files'].append(row)
    for item in overlaps(data):
        result['batch_issues'].append('shorts overlap: ' + json.dumps(item, ensure_ascii=False))
    louds = [f['lufs'] for f in result['files'] if 'lufs' in f]
    if len(louds) > 1 and max(louds) - min(louds) > 3.0:
        result['batch_issues'].append(f'lot loudness drift >3 LU: {max(louds)-min(louds):.1f} LU')
    result['ok'] = (not result['batch_issues'] and all(not row['issues'] for row in result['files']))
    return result


def main():
    p = argparse.ArgumentParser(description='Validate a video export batch (read-only).')
    p.add_argument('manifest', type=Path)
    p.add_argument('--exports-root', type=Path, required=True)
    p.add_argument('--sources-root', type=Path, required=True)
    p.add_argument('--skip-media-tools', action='store_true', help='metadata/hash-only selftest; not full QA')
    p.add_argument('--report', type=Path)
    args = p.parse_args()
    try:
        data = json.loads(args.manifest.read_text(encoding='utf-8'))
        report = audit(data, args.exports_root, args.sources_root, not args.skip_media_tools)
    except (OSError, ValueError, json.JSONDecodeError) as e:
        print(json.dumps({'ok': False, 'error': str(e)}, ensure_ascii=False))
        return 2
    output = json.dumps(report, indent=2, ensure_ascii=False)
    if args.report:
        args.report.write_text(output + '\n', encoding='utf-8')
    print(output)
    return 0 if report['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())