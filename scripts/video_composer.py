"""
FFmpeg and MoviePy Video Composer.
Implements Module 3 Part G (Nodes 18 & 19) of the Agentic AI Video Creation System.
Composes 1080x1920 9:16 30 FPS MP4 video combining visuals, voiceover, and captions.
"""

import os
import sys
import time
import shutil
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import Config

logger = logging.getLogger(__name__)

class VideoComposer:
    """Orchestrates FFmpeg composition into compliant vertical MP4 video."""

    @classmethod
    def compose_video(
        cls,
        scenes: List[Dict[str, Any]],
        audio_path: Path,
        subtitles_path: Optional[Path] = None,
        output_mp4: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Combines scene visual images, voiceover audio, and SRT subtitles into a 1080x1920 MP4.
        """
        target_mp4 = output_mp4 or (Config.VIDEOS_DIR / f"final_video_{int(time.time())}.mp4")
        # Also maintain standard final_video.mp4 as referenced in manual
        standard_mp4 = Config.VIDEOS_DIR / "final_video.mp4"
        target_mp4.parent.mkdir(parents=True, exist_ok=True)

        ffmpeg_exe = Config.get_ffmpeg_exe()
        logger.info(f"Using FFmpeg binary: {ffmpeg_exe}")

        # Verify visuals
        valid_scenes = []
        for s in scenes:
            v_file = s.get("visual_file")
            if v_file and os.path.exists(v_file):
                valid_scenes.append(s)

        if not valid_scenes:
            raise FileNotFoundError("No valid visual files provided for video composition.")

        # Create FFmpeg concat demuxer file
        concat_txt = Config.OUTPUT_DIR / "concat_scenes.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for s in valid_scenes:
                dur = s.get("duration_seconds", 5)
                # Escaped file path with forward slashes
                vf_clean = Path(s["visual_file"]).resolve().as_posix()
                f.write(f"file '{vf_clean}'\n")
                f.write(f"duration {dur}\n")
            # FFmpeg concat requires repeating the last file
            last_file = Path(valid_scenes[-1]["visual_file"]).resolve().as_posix()
            f.write(f"file '{last_file}'\n")

        # Prepare subtitle filter if available
        sub_filter = None
        if subtitles_path and subtitles_path.exists():
            # FFmpeg subtitle filter needs escaped path:
            # colon and backslash must be escaped
            srt_escaped = subtitles_path.resolve().as_posix()
            # Windows drive letter colon escape: e.g. C:/ -> C\:/
            if len(srt_escaped) > 1 and srt_escaped[1] == ":":
                srt_escaped = srt_escaped[0] + "\\:" + srt_escaped[2:]
            sub_filter = f"subtitles='{srt_escaped}':force_style='FontSize=20,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,BorderStyle=4,Alignment=2,MarginV=140'"

        # Base video filter chain:
        # Scale to fit 1080x1920 keeping aspect ratio, pad with black bars or blurred background, set 30fps
        vf_chain = (
            f"scale={Config.VIDEO_WIDTH}:{Config.VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,"
            f"pad={Config.VIDEO_WIDTH}:{Config.VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2:black,"
            f"setsar=1,fps={Config.VIDEO_FPS}"
        )

        # Attempt 1: Full composition with subtitles burned in
        cmd_with_subs = None
        if sub_filter:
            full_vf = f"{vf_chain},{sub_filter}"
            cmd_with_subs = [
                ffmpeg_exe, "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_txt),
                "-i", str(audio_path),
                "-vf", full_vf,
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-shortest",
                str(target_mp4)
            ]

        # Attempt 2: Composition without burning subtitles (if libass filter unavailable)
        cmd_fallback = [
            ffmpeg_exe, "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_txt),
            "-i", str(audio_path),
            "-vf", vf_chain,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(target_mp4)
        ]

        success = False
        last_error = ""

        if cmd_with_subs:
            logger.info("Executing FFmpeg command with subtitles...")
            proc = subprocess.run(cmd_with_subs, capture_output=True, text=True, timeout=120)
            if proc.returncode == 0 and target_mp4.exists() and target_mp4.stat().st_size > 10000:
                success = True
                logger.info("FFmpeg composition with subtitles succeeded!")
            else:
                last_error = proc.stderr
                logger.warning(f"Subtitles burning failed: {proc.stderr[:200]}... falling back to video without burn-in.")

        if not success:
            logger.info("Executing FFmpeg composition...")
            proc = subprocess.run(cmd_fallback, capture_output=True, text=True, timeout=120)
            if proc.returncode == 0 and target_mp4.exists() and target_mp4.stat().st_size > 10000:
                success = True
                logger.info("FFmpeg video composition succeeded!")
            else:
                last_error = proc.stderr
                logger.error(f"FFmpeg failed with returncode {proc.returncode}: {proc.stderr}")
                raise RuntimeError(f"FFmpeg video encoding failed: {proc.stderr}")

        # Copy to canonical final_video.mp4 for convenience
        try:
            shutil.copyfile(target_mp4, standard_mp4)
        except Exception:
            pass

        # Cleanup concat file
        try:
            concat_txt.unlink(missing_ok=True)
        except Exception:
            pass

        file_size_mb = round(target_mp4.stat().st_size / (1024 * 1024), 2)
        return {
            "status": "success",
            "video_path": str(target_mp4),
            "canonical_video_path": str(standard_mp4),
            "file_size_mb": file_size_mb,
            "resolution": f"{Config.VIDEO_WIDTH}x{Config.VIDEO_HEIGHT}",
            "fps": Config.VIDEO_FPS,
            "aspect_ratio": Config.VIDEO_ASPECT_RATIO
        }


if __name__ == "__main__":
    from .voice_generator import VoiceGenerator
    from .asset_downloader import AssetDownloader
    from .subtitle_generator import SubtitleGenerator

    test_scenes = [
        {
            "scene_number": 1,
            "narration": "Artificial Intelligence is transforming how we learn every day.",
            "visual_description": "Modern university campus with digital student holographic screens",
            "search_keywords": "students technology",
            "duration_seconds": 4
        },
        {
            "scene_number": 2,
            "narration": "Get ready to elevate your skills and study smarter with AI tools.",
            "visual_description": "Excited student achieving breakthrough success",
            "search_keywords": "education success",
            "duration_seconds": 4
        }
    ]
    AssetDownloader.process_all_scenes(test_scenes)
    aud_res = VoiceGenerator.generate_voiceover("Artificial Intelligence is transforming how we learn every day. Get ready to elevate your skills.")
    srt_res = SubtitleGenerator.generate_captions(Path(aud_res["audio_path"]), test_scenes)
    comp_res = VideoComposer.compose_video(test_scenes, Path(aud_res["audio_path"]), Path(srt_res["subtitles_path"]))
    print("Composition result:", comp_res)
