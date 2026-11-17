# Skill: CASA Semantic Video Decoupage v1.0

**Status: documented source skill. Not registered/installed in Qwen or the HOST FAMILIA yet.**

## When to use
Every CASA project producing short videos from raw recordings, when the user wants smooth, engaging editing without jump cuts or false narratives.

## Invariants
- Only original recording(s) backed by source manifest and SHA-256.
- No re-edit of previous exports, no deletion/alteration of the original.
- Build private text events with precise time ranges and confidence **before** choosing shots.
- Sequence event chain: setup → action → observed consequence. If the payoff is absent, state absent; never invent one.
- One story continuity first; cuts only at meaningful boundaries. Separate fights/scenes explicitly.
- Event descriptions and analysis text **MUST NOT** be burned into the video or exported as subtitles.
- Models provide suggestions, not definitive observation; uncertain descriptions require human/visual review.

## Standard workflow
1. Inventory originals: unique source IDs, path, SHA-256 and duration (actual file verification required).
2. Watch and describe **what can be seen**; create \`events\` with observed evidence timestamps.
3. Mark low-information sequences, occlusion, black frames, loading and pauses as candidates for review, not automatic removal.
4. Build \`shots\` while preserving event order and all dependencies.
5. Validate with \`semantic_timeline.py validate\` including \`--source-root\` when original bytes available.
6. Generate an EDL suggestion with \`semantic_timeline.py edl\`; editorial review before independent renderer.
7. QA actual exported MP4 for continuity, framing, synchronized original audio and no injected event descriptions.
8. Report SOURCE/CI/HOST/DEVICE evidence separately; do not claim increased retention without platform metrics.

## Data contract
Refer to [schema.json](./schema.json) and [README.md](./README.md). Text fields are **for internal planning only**. The EDL exporter deliberately omits \`description_pt\`.

## Failure handling
Reject: derivative source, SHA mismatch, missing causal predecessor, reverse chronological cut in same recording, truncated action, \`render_as_overlay=true\`, unknown event, source change without reason, out-of-range timestamps. No background continuous agent/process required.
