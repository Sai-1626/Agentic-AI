"""
Command-line Interface (CLI) for Agentic AI Social Media Video Automation.
Allows running the complete pipeline directly from terminal or automated scripts.
"""

import sys
import json
import argparse
import logging
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from scripts.config import Config
from scripts.script_generator import PlanningAgent, ScriptAgent
from scripts.scene_extractor import SceneAgent
from scripts.asset_downloader import AssetDownloader
from scripts.voice_generator import VoiceGenerator
from scripts.subtitle_generator import SubtitleGenerator
from scripts.video_composer import VideoComposer
from scripts.quality_agent import QualityControlAgent
from scripts.seo_agent import SEOAgent
from scripts.scheduler import PublishScheduler
from scripts.publisher import YouTubePublisher, InstagramPublisher
from scripts.notifier import EmailNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VideoAgentCLI")

def run_pipeline(prompt: str, dry_run: bool = True, output_dir: str = None) -> dict:
    """Executes the complete pipeline step by step."""
    print("=" * 60)
    print("[*] STARTING AGENTIC AI VIDEO CREATION SYSTEM")
    print(f"[*] Prompt: {prompt}")
    print("=" * 60)

    # Step 1: Content Planning Agent
    print("\n[Step 1/11] Running Planning Agent...")
    plan = PlanningAgent.plan(prompt)
    print(f"  * Topic: {plan.get('topic')}")
    print(f"  * Audience: {plan.get('target_audience')}")
    print(f"  * Platform: {plan.get('platform')}")
    print(f"  * Target Duration: {plan.get('duration')}s")

    # Step 2: Script Generation Agent
    print("\n[Step 2/11] Running Script Agent...")
    script = ScriptAgent.generate_script(plan)
    print(f"  * Script preview: {script[:120]}...")

    # Step 3: Scene Extraction Agent
    print("\n[Step 3/11] Running Scene Agent...")
    scenes = SceneAgent.extract_scenes(script, target_duration=plan.get("duration", 60))
    print(f"  * Generated {len(scenes)} scenes.")
    for s in scenes:
        print(f"    - Scene {s['scene_number']}: {s['duration_seconds']}s | {s['narration'][:50]}...")

    # Step 4: Visual Retrieval & Generation
    print("\n[Step 4/11] Generating / Fetching Visual Assets...")
    visuals = AssetDownloader.process_all_scenes(scenes)
    print(f"  * Visual files ready: {len(visuals)} items.")

    # Step 5: Voiceover Generation
    print("\n[Step 5/11] Generating Voiceover Narration...")
    audio_info = VoiceGenerator.generate_voiceover(script, target_duration=plan.get("duration", 60))
    audio_path = Path(audio_info["audio_path"])
    print(f"  * Voiceover saved ({audio_info['engine']}): {audio_path}")

    # Step 6: Subtitle Generation (Whisper / Timed SRT)
    print("\n[Step 6/11] Generating Subtitles (SRT)...")
    sub_info = SubtitleGenerator.generate_captions(audio_path, scenes)
    subtitles_path = Path(sub_info["subtitles_path"])
    print(f"  * Captions saved: {subtitles_path}")

    # Step 7: FFmpeg Video Composition (1080x1920 9:16)
    print("\n[Step 7/11] Composing 1080x1920 9:16 MP4 Video with FFmpeg...")
    comp_info = VideoComposer.compose_video(scenes, audio_path, subtitles_path)
    video_path = Path(comp_info["video_path"])
    print(f"  * Video rendered: {video_path}")
    print(f"  * Size: {comp_info['file_size_mb']} MB | Resolution: {comp_info['resolution']}")

    # Step 8: Quality Control Agent
    print("\n[Step 8/11] Running Quality Control Agent...")
    qc_state = {
        "script": script,
        "scenes": scenes,
        "audio_path": str(audio_path),
        "subtitles_path": str(subtitles_path),
        "video_path": str(video_path)
    }
    qc_res = QualityControlAgent.evaluate(qc_state)
    print(f"  * QC Status: {qc_res['status']} | Quality Score: {qc_res['quality_score']}/100")
    if qc_res.get("issues"):
        print(f"  * Issues detected: {qc_res['issues']}")

    # Step 9: SEO & Social Content Agent
    print("\n[Step 9/11] Running SEO Agent...")
    seo_res = SEOAgent.generate_seo_content(plan.get("topic", "AI Video"), script)
    print(f"  * YouTube Title: {seo_res.get('youtube_title')}")
    print(f"  * Instagram Caption: {seo_res.get('instagram_caption')}")
    print(f"  * Hashtags: {' '.join(seo_res.get('instagram_hashtags', []))}")

    # Step 10: Publishing to YouTube & Instagram
    print("\n[Step 10/11] Publishing to Platforms...")
    yt_res = YouTubePublisher.upload(
        video_path=video_path,
        title=seo_res.get("youtube_title", "New Video"),
        description=seo_res.get("youtube_description", ""),
        tags=seo_res.get("youtube_tags", [])
    )
    print(f"  * YouTube Status: {yt_res.get('status')} ({yt_res.get('mode')}) | Link: {yt_res.get('youtube_url')}")

    ig_res = InstagramPublisher.publish(
        video_path=video_path,
        caption=seo_res.get("instagram_caption", "New Reel"),
        hashtags=seo_res.get("instagram_hashtags", [])
    )
    print(f"  * Instagram Status: {ig_res.get('status')} ({ig_res.get('mode')}) | Link: {ig_res.get('instagram_url')}")

    # Step 11: Email Notification
    print("\n[Step 11/11] Sending Notification...")
    if yt_res.get("status") == "success" and ig_res.get("status") == "success":
        mail_res = EmailNotifier.send_success_notification(
            video_title=seo_res.get("youtube_title", plan.get("topic")),
            youtube_url=yt_res.get("youtube_url", ""),
            instagram_url=ig_res.get("instagram_url", "")
        )
    else:
        mail_res = EmailNotifier.send_error_notification(
            video_title=seo_res.get("youtube_title", plan.get("topic")),
            youtube_status=yt_res.get("status", "failed"),
            instagram_status=ig_res.get("status", "failed"),
            error_message="Publishing check incomplete"
        )
    print(f"  * Notification Status: {mail_res.get('status')} ({mail_res.get('mode')})")

    print("\n" + "=" * 60)
    print("[SUCCESS] PIPELINE COMPLETED SUCCESSFULLY!")
    print(f"[*] Final Video: {video_path}")
    print(f"[*] YouTube: {yt_res.get('youtube_url')}")
    print(f"[*] Instagram: {ig_res.get('instagram_url')}")
    print("=" * 60)

    return {
        "status": "success",
        "video": str(video_path),
        "youtube_url": yt_res.get("youtube_url"),
        "instagram_url": ig_res.get("instagram_url"),
        "quality_score": qc_res.get("quality_score")
    }

def main():
    parser = argparse.ArgumentParser(description="Agentic AI Social Media Video Automation")
    parser.add_argument("--prompt", type=str, default="Create a 60-second Instagram Reel about Artificial Intelligence in Education", help="Video creation prompt")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Run publishing in dry-run mode")
    args = parser.parse_args()

    run_pipeline(prompt=args.prompt, dry_run=args.dry_run)

if __name__ == "__main__":
    main()
