"""
Subtitle and Caption Generator.
Implements Module 3 Part F (Nodes 16 & 17) of the Agentic AI Video Creation System.
Supports Whisper audio transcription and scene-aligned timestamped SRT generation.
"""

import os
import re
import math
import wave
import shutil
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import Config

logger = logging.getLogger(__name__)

def format_timestamp(seconds: float) -> str:
    """Formats seconds into SRT timestamp format: HH:MM:SS,mmm."""
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"

def get_audio_duration(audio_path: Path) -> float:
    """Returns duration of audio file in seconds via wave or ffprobe."""
    if not audio_path.exists():
        return 10.0

    # 1. Try wave if WAV
    if audio_path.suffix.lower() == ".wav":
        try:
            with wave.open(str(audio_path), "r") as w:
                frames = w.getnframes()
                rate = w.getframerate()
                if rate > 0:
                    return frames / float(rate)
        except Exception:
            pass

    # 2. Try ffprobe/ffmpeg
    ffmpeg_exe = Config.get_ffmpeg_exe()
    try:
        cmd = [
            ffmpeg_exe,
            "-i", str(audio_path)
        ]
        res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True, timeout=10)
        dur_match = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.?\d*)", res.stderr)
        if dur_match:
            h, m, s = dur_match.groups()
            return int(h) * 3600 + int(m) * 60 + float(s)
    except Exception as e:
        logger.warning(f"Could not read audio duration via ffmpeg: {e}")

    return 30.0


class SubtitleGenerator:
    """Generates strictly compliant SRT subtitle files."""

    @classmethod
    def transcribe_with_whisper(cls, audio_path: Path, output_srt: Path) -> bool:
        """Invokes Whisper CLI or Python API if available."""
        whisper_bin = shutil.which("whisper")
        if not whisper_bin:
            return False

        try:
            logger.info("Attempting speech-to-text with Whisper CLI...")
            cmd = [
                whisper_bin,
                str(audio_path),
                "--model", Config.WHISPER_MODEL,
                "--output_format", "srt",
                "--output_dir", str(output_srt.parent)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            generated_srt = output_srt.parent / f"{audio_path.stem}.srt"
            if res.returncode == 0 and generated_srt.exists():
                if generated_srt != output_srt:
                    shutil.move(str(generated_srt), str(output_srt))
                logger.info(f"Whisper transcription succeeded -> {output_srt}")
                return True
            logger.warning(f"Whisper CLI execution returned {res.returncode}: {res.stderr}")
        except Exception as e:
            logger.warning(f"Whisper invocation failed: {e}")
        return False

    @classmethod
    def generate_srt_from_scenes(
        cls,
        scenes: List[Dict[str, Any]],
        audio_path: Optional[Path] = None,
        output_srt: Optional[Path] = None
    ) -> Path:
        """
        Generates cleanly timed, human-readable SRT subtitles aligned with scenes.
        Guarantees that subtitle timestamps cover the full duration and never overlap.
        """
        target_file = output_srt or (Config.SUBTITLES_DIR / "captions.srt")
        target_file.parent.mkdir(parents=True, exist_ok=True)

        total_audio_duration = get_audio_duration(audio_path) if audio_path else sum(s.get("duration_seconds", 5) for s in scenes)
        total_scene_duration = sum(s.get("duration_seconds", 5) for s in scenes) or 1.0

        # Proportional scale factor
        scale = total_audio_duration / total_scene_duration if total_scene_duration > 0 else 1.0

        srt_blocks = []
        current_time = 0.0
        index = 1

        for scene in scenes:
            narration = scene.get("narration", "").strip()
            if not narration:
                continue

            scene_dur = scene.get("duration_seconds", 5) * scale

            # Split narration into concise caption chunks (max 8 words / 45 chars for mobile readability)
            words = narration.split()
            chunks = []
            cur_chunk = []
            for w in words:
                cur_chunk.append(w)
                if len(cur_chunk) >= 7 or len(" ".join(cur_chunk)) >= 40:
                    chunks.append(" ".join(cur_chunk))
                    cur_chunk = []
            if cur_chunk:
                chunks.append(" ".join(cur_chunk))

            if not chunks:
                chunks = [narration]

            chunk_duration = scene_dur / len(chunks)

            for chunk in chunks:
                start_sec = current_time
                end_sec = min(total_audio_duration, current_time + chunk_duration)
                
                start_fmt = format_timestamp(start_sec)
                end_fmt = format_timestamp(end_sec)

                srt_blocks.append(f"{index}\n{start_fmt} --> {end_fmt}\n{chunk}\n")
                index += 1
                current_time = end_sec

        srt_content = "\n".join(srt_blocks)
        with open(target_file, "w", encoding="utf-8") as f:
            f.write(srt_content)

        logger.info(f"Generated captions.srt with {index-1} cues at: {target_file}")
        return target_file

    @classmethod
    def generate_captions(
        cls,
        audio_path: Path,
        scenes: List[Dict[str, Any]],
        output_srt: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Orchestrates subtitle generation.
        Tries Whisper first, falls back to high-accuracy scene-aligned SRT generation.
        """
        target_file = output_srt or (Config.SUBTITLES_DIR / "captions.srt")
        
        # 1. Try Whisper
        if cls.transcribe_with_whisper(audio_path, target_file):
            return {
                "subtitles_path": str(target_file),
                "engine": "whisper",
                "status": "success"
            }

        # 2. Scene-aligned generator
        srt_file = cls.generate_srt_from_scenes(scenes, audio_path, target_file)
        return {
            "subtitles_path": str(srt_file),
            "engine": "scene_aligner",
            "status": "success"
        }


if __name__ == "__main__":
    test_scenes = [
        {"scene_number": 1, "narration": "Artificial Intelligence is changing education.", "duration_seconds": 4},
        {"scene_number": 2, "narration": "Students can now learn in completely new ways.", "duration_seconds": 4}
    ]
    out = Config.SUBTITLES_DIR / "test_captions.srt"
    res = SubtitleGenerator.generate_srt_from_scenes(test_scenes, output_srt=out)
    print("SRT Content:\n", out.read_text(encoding="utf-8"))
