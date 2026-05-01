# scripts/backfill_normalize.py
"""One-shot legacy patch: normalizes all existing MP3s to EBU R128 (-14 LUFS).

Usage:
    python scripts/backfill_normalize.py          # defaults to music/
    python scripts/backfill_normalize.py --dry-run # preview without processing
"""

import argparse
import sys
import time
from pathlib import Path

# Ensure project root is importable
sys.path.append(str(Path(__file__).parent.parent))

from beatforge import config
from beatforge.normalizer import Normalizer
from beatforge.sampler import Sampler

def backfill(music_dir: Path, *, dry_run: bool = False) -> None:
    normalizer = Normalizer(
        target_lufs=config.LOUDNORM_TARGET_LUFS,
        true_peak=config.LOUDNORM_TRUE_PEAK,
        lra=config.LOUDNORM_LRA
    )
    sampler = Sampler()

    # Collect all non-sample MP3s
    candidates = [
        mp3
        for mp3 in music_dir.rglob("*.mp3")
        if not mp3.name.endswith("_sample.mp3")
    ]

    processed = 0
    errors = 0
    start = time.time()

    print(f"Backfill Normalization → {config.LOUDNORM_TARGET_LUFS} LUFS")
    print(f"Source directory : {music_dir}")
    print(f"Candidates found: {len(candidates)}")
    if dry_run:
        print("DRY-RUN mode — no files will be written\n")

    for mp3 in sorted(candidates):
        if dry_run:
            print(f"  [DRY] Normalize {mp3.name}")
            processed += 1
            continue

        try:
            normalizer.normalize(mp3)
            # Recreate sample so it's also normalized
            sample_path = mp3.with_name(f"{mp3.stem}_sample.mp3")
            if sample_path.exists():
                sample_path.unlink() # Remove old unnormalized sample
            
            sampler.create_sample(mp3)
            
            processed += 1
            elapsed = time.time() - start
            print(f"  ✓ Normalized  {mp3.name}  ({elapsed:.1f}s)")
        except Exception as e:
            errors += 1
            print(f"  ✗ Error on {mp3.name}: {e}")

    elapsed = time.time() - start
    print(f"\nDone in {elapsed:.1f}s — processed={processed} errors={errors}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalize legacy MP3s to EBU R128")
    parser.add_argument(
        "--music-dir",
        type=Path,
        default=Path(config.OUTPUT_DIR),
        help=f"Root music directory (default: {config.OUTPUT_DIR})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview operations without writing files",
    )
    args = parser.parse_args()
    backfill(args.music_dir, dry_run=args.dry_run)
