# scripts/backfill_retarget.py
"""One-shot legacy patch: retargets all existing MP3s to the global target BPM.

Usage:
    python scripts/backfill_retarget.py          # defaults to music/ and 160 BPM
    python scripts/backfill_retarget.py --dry-run # preview without processing

This script is idempotent — safe to re-run.
Delete after all legacy files have been processed.
"""

import argparse
import re
import sys
import time
from pathlib import Path

# Ensure project root is importable
sys.path.append(str(Path(__file__).parent.parent))

from beatforge import config
from beatforge.retargeter import Retargeter
from beatforge.sampler import Sampler


BPM_PATTERN = re.compile(r"_(\d+)bpm\.mp3$")


def _parse_source_bpm(filename: str) -> int | None:
    """Extract the numeric BPM from a filename like 'Track_120bpm.mp3'."""
    match = BPM_PATTERN.search(filename)
    return int(match.group(1)) if match else None


def backfill(music_dir: Path, global_target: int, *, dry_run: bool = False) -> None:
    sampler = Sampler()
    retargeter = Retargeter(global_target, sampler)

    # Collect all non-sample MP3s, excluding _to* subfolders
    candidates = [
        mp3
        for mp3 in music_dir.rglob("*.mp3")
        if not mp3.name.endswith("_sample.mp3")
        and f"_to{global_target}" not in str(mp3)
    ]

    skipped = 0
    processed = 0
    errors = 0
    start = time.time()

    print(f"Backfill retarget → {global_target} BPM")
    print(f"Source directory : {music_dir}")
    print(f"Candidates found: {len(candidates)}")
    if dry_run:
        print("DRY-RUN mode — no files will be written\n")

    for mp3 in sorted(candidates):
        source_bpm = _parse_source_bpm(mp3.name)
        if source_bpm is None:
            print(f"  ⚠ Cannot parse BPM from: {mp3.name}")
            errors += 1
            continue

        if source_bpm == global_target:
            skipped += 1
            continue

        if dry_run:
            mult = round(global_target / source_bpm, 4)
            print(f"  [DRY] {source_bpm}→{global_target} (x{mult}) {mp3.name}")
            processed += 1
            continue

        try:
            result = retargeter.retarget(mp3, source_bpm)
            if result:
                processed += 1
                elapsed = time.time() - start
                print(f"  ✓ {source_bpm}→{global_target} bpm  {mp3.name}  ({elapsed:.1f}s)")
            else:
                skipped += 1
        except Exception as e:
            errors += 1
            print(f"  ✗ Error on {mp3.name}: {e}")

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s — processed={processed} skipped={skipped} errors={errors}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Retarget legacy MP3s to a global BPM")
    parser.add_argument(
        "--music-dir",
        type=Path,
        default=Path(config.OUTPUT_DIR),
        help=f"Root music directory (default: {config.OUTPUT_DIR})",
    )
    parser.add_argument(
        "--target-bpm",
        type=int,
        default=config.GLOBAL_TARGET_BPM,
        help=f"Global target BPM (default: {config.GLOBAL_TARGET_BPM})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview operations without writing files",
    )
    args = parser.parse_args()
    backfill(args.music_dir, args.target_bpm, dry_run=args.dry_run)
