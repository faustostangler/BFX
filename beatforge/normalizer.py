# beatforge/normalizer.py

import subprocess
import json
import re
from pathlib import Path

class Normalizer:
    """EBU R128 two-pass loudness normalization via ffmpeg loudnorm."""

    def __init__(self, target_lufs: float, true_peak: float, lra: float) -> None:
        self.target_lufs = target_lufs
        self.true_peak = true_peak
        self.lra = lra

    def normalize(self, mp3_path: Path) -> None:
        """Normalize an MP3 file in-place using two-pass loudnorm."""
        if not mp3_path.exists():
            return
            
        # Pass 1: Measure
        cmd1 = [
            "ffmpeg", "-y", "-hide_banner", "-i", str(mp3_path),
            "-af", f"loudnorm=I={self.target_lufs}:TP={self.true_peak}:LRA={self.lra}:print_format=json",
            "-f", "null", "/dev/null"
        ]
        
        result = subprocess.run(cmd1, capture_output=True, text=True)
        
        match = re.search(r'\{.*\}', result.stderr, re.DOTALL)
        if not match:
            print(f"Warning: loudnorm pass 1 failed for {mp3_path}")
            return
            
        stats = json.loads(match.group(0))
        
        temp_path = mp3_path.with_suffix('.tmp.mp3')
        
        # Pass 2: Apply correction
        cmd2 = [
            "ffmpeg", "-y", "-hide_banner", "-i", str(mp3_path),
            "-af", f"loudnorm=I={self.target_lufs}:TP={self.true_peak}:LRA={self.lra}:measured_I={stats['input_i']}:measured_LRA={stats['input_lra']}:measured_TP={stats['input_tp']}:measured_thresh={stats['input_thresh']}:offset={stats['target_offset']}:linear=true",
            "-q:a", "2",
            str(temp_path)
        ]
        
        subprocess.run(cmd2, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Replace original with normalized in-place
        temp_path.replace(mp3_path)
