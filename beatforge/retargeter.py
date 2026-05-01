# beatforge/retargeter.py

import subprocess
from pathlib import Path
from typing import Optional, Tuple

from beatforge.sampler import Sampler


class Retargeter:
    """Re-encodes an MP3 to a global target BPM via ffmpeg atempo.

    Distinct from Converter (WAV→MP3 at bucket BPM):
    this service operates on *already-encoded* MP3s,
    producing a tempo-shifted copy at a single global BPM.
    """

    def __init__(self, base_dir: Path, global_target_bpm: int, sampler: Sampler) -> None:
        self.base_dir = base_dir
        self.global_target_bpm = global_target_bpm
        self.sampler = sampler

    def retarget(self, mp3_path: Path, source_bpm: int, genre: str = "Unknown") -> Optional[Path]:
        """Produce a tempo-shifted MP3 + sample at the global target BPM.

        Args:
            mp3_path: Absolute path to the source MP3.
            source_bpm: The BPM the source was encoded at (bucket target).
            genre: The genre for folder organization.

        Returns:
            Path to the retargeted MP3, or None if already at target.
        """
        if source_bpm == self.global_target_bpm:
            return None

        # Output folder: base_dir / _160 / genre
        out_dir = self.base_dir / f"_{self.global_target_bpm}" / genre
        out_dir.mkdir(parents=True, exist_ok=True)

        out_name = self._build_output_name(mp3_path.stem, source_bpm)
        out_mp3 = out_dir / f"{out_name}.mp3"

        # Idempotent: skip if already retargeted
        if out_mp3.exists():
            return out_mp3

        multiplier = round(self.global_target_bpm / source_bpm, 4)
        self._run_ffmpeg(mp3_path, out_mp3, multiplier)

        # Sample inherits normalized loudness from source MP3 (atempo preserves amplitude)
        # No re-normalization needed
        self.sampler.create_sample(out_mp3)

        return out_mp3

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_output_name(self, stem: str, source_bpm: int) -> str:
        """Replace the source BPM suffix with the compound BPM format.

        'Queen - Champions_100bpm' → 'Queen - Champions100_160 bpm'
        """
        suffix = f"_{source_bpm}bpm"
        if stem.endswith(suffix):
            base = stem[: -len(suffix)]
        else:
            base = stem
        return f"{base}{source_bpm}_{self.global_target_bpm} bpm"

    @staticmethod
    def _run_ffmpeg(input_path: Path, output_path: Path, multiplier: float) -> None:
        """Execute ffmpeg atempo filter for tempo shifting."""
        cmd = [
            "ffmpeg", "-y",
            "-i", str(input_path),
            "-filter:a", f"atempo={multiplier}",
            "-vn",
            "-q:a", "2",
            str(output_path),
        ]
        subprocess.run(
            cmd, check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
