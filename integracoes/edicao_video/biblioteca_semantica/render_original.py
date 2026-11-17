#!/usr/bin/env python3
"""CASA Video Lab: portable, source-verified, context-preserving FFmpeg renderer.

Uses only user-provided ORIGINAL recordings, no overlay text or external music.
Requires ffmpeg and ffprobe; deliberately refuses unhandled HDR sources.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from qa_video_lote import checksum, local_file, probe_video, check_manifest, SCHEMA


def render(config: dict, source_root: Path, output_root: Path) -> dict:
    if config.get('schema_version') != 'casa.video.render/1.0':
        raise ValueError('unsupported render configuration')
    srcs = config.get('sources')
    jobs = config.get('jobs')
    if not isinstance(srcs, list) or not srcs or not isinstance(jobs, list) or not jobs:
        raise ValueError('sources and jobs must be nonempty lists')
    if source_root.resolve() == output_root.resolve():
        raise ValueError('output root must differ from input root')
    output_root.mkdir(parents=True, exist_ok=True)
    found = {}
    for source in srcs:
        if source.get('origin') != 'raw_capture':
            raise ValueError('rejecting non-original source')
        path = local_file(source_root, source['file'])
        if not path.is_file() or checksum(path) != source['sha256']:
            raise ValueError('original file missing or SHA256 mismatch')
        if path.resolve().is_relative_to(output_root.resolve()):
            raise ValueError('original located under output root')
        metadata = probe_video(path)
        video = next((s for s in metadata['streams'] if s['codec_type'] == 'video'), None)
        audio = next((s for s in metadata['streams'] if s['codec_type'] == 'audio'), None)
        if not video or not audio:
            raise ValueError('source requires video and audio streams')
        if video.get('color_transfer') in ('smpte2084', 'arib-std-b67'):
            raise ValueError('HDR input detected: explicit validated HDR-to-SDR mapping required')
        if source['id'] in found:
            raise ValueError('repeated source ID')
        found[source['id']] = (path, metadata, video)
    manifest = {'schema_version': SCHEMA, 'annotations_private': True,
                'render_semantic_text': False, 'sources': [], 'exports': []}
    for src in srcs:
        manifest['sources'].append({'id': src['id'], 'file': src['file'],
                                    'sha256': src['sha256'], 'origin': 'raw_capture',
                                    'duration_seconds': float(found[src['id']][1]['format']['duration'])})
    planned = set()
    for job in jobs:
        sid = job['source_id']
        if sid not in found:
            raise ValueError('unknown job source')
        start, end = float(job['in_seconds']), float(job['out_seconds'])
        if not 0 <= start < end <= float(found[sid][1]['format']['duration']) + .05:
            raise ValueError('job range must be within original recording')
        file = job['file']
        if Path(file).name != file or not file.endswith('.mp4') or file in planned:
            raise ValueError('output filename must be unique simple .mp4 basename')
        planned.add(file)
        out = output_root / file
        if out.exists():
            raise FileExistsError(f'output exists; refusing to overwrite: {out}')
        srcpath, _, video = found[sid]
        fmt = job['format']
        if fmt == 'short':
            crop = job.get('crop')
            if not isinstance(crop, dict) or not all(k in crop for k in ('x', 'y', 'w', 'h')):
                raise ValueError('portrait short requires visually selected crop')
            x, y, w, h = (int(crop[k]) for k in ('x', 'y', 'w', 'h'))
            if not (x >= 0 and y >= 0 and w > 0 and h > 0
                    and x+w <= video['width'] and y+h <= video['height']):
                raise ValueError('portrait crop out of bounds')
            vf = (f'crop={w}:{h}:{x}:{y},'
                  'scale=720:1280:force_original_aspect_ratio=increase:flags=lanczos,'
                  'crop=720:1280,fps=30,format=yuv420p,'
                  'setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709')
        elif fmt == 'youtube_horizontal':
            if video['width'] <= video['height']:
                raise ValueError('YouTube horizontal requires landscape original')
            vf = ('scale=1280:720:force_original_aspect_ratio=decrease:flags=lanczos,'
                  'pad=1280:720:(ow-iw)/2:(oh-ih)/2,fps=30,format=yuv420p,'
                  'setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709')
        else:
            raise ValueError('unknown format')
        args = ['ffmpeg','-hide_banner','-nostdin','-v','error','-n',
                '-ss',str(start),'-i',str(srcpath),'-t',str(end-start),
                '-map','0:v:0','-map','0:a:0','-vf',vf,
                '-af','loudnorm=I=-18:TP=-1.5:LRA=11',
                '-c:v','libx264','-preset','veryfast','-crf','22','-threads','3',
                '-pix_fmt','yuv420p','-r','30',
                '-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709',
                '-c:a','aac','-b:a','160k','-ar','48000','-ac','2',
                '-movflags','+faststart',str(out)]
        completed = subprocess.run(args, capture_output=True, text=True, timeout=240)
        if completed.returncode:
            out.unlink(missing_ok=True)
            raise RuntimeError(f'ffmpeg failed for {file}: {completed.stderr[-700:]}')
        manifest['exports'].append({'source_id': sid, 'file': file,
                                    'sha256': checksum(out),
                                    'in_seconds': start, 'out_seconds': end,
                                    'format': fmt})
    check_manifest(manifest)
    return manifest


def main():
    p = argparse.ArgumentParser(description='CASA verified render from original recording only')
    p.add_argument('config', type=Path)
    p.add_argument('--sources-root', type=Path, required=True)
    p.add_argument('--exports-root', type=Path, required=True)
    p.add_argument('--manifest', type=Path, required=True)
    a = p.parse_args()
    try:
        config = json.loads(a.config.read_text(encoding='utf-8'))
        data = render(config, a.sources_root, a.exports_root)
        a.manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
        print(json.dumps({'ok': True, 'exports': len(data['exports'])}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.TimeoutExpired) as e:
        print(json.dumps({'ok': False, 'error': str(e)}, ensure_ascii=False))
        return 2

if __name__ == '__main__':
    raise SystemExit(main())