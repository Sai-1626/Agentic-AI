"""
End-to-End and Unit Test Suite for Agentic AI Social Media Video Automation.
"""

import os
import sys
import json
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

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
from scripts.app import app

class TestVideoAutomationPipeline(unittest.TestCase):
    """Verifies each module and full pipeline integrity."""

    def setUp(self):
        self.test_prompt = "Create a 60-second Instagram Reel about Artificial Intelligence in Education"
        self.output_dir = Config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def test_01_config(self):
        """Test configuration paths and FFmpeg resolution."""
        self.assertTrue(Config.OUTPUT_DIR.exists())
        self.assertTrue(Config.VISUALS_DIR.exists())
        ffmpeg_bin = Config.get_ffmpeg_exe()
        self.assertTrue(len(ffmpeg_bin) > 0)
        print(f"\n[Test 1] Config verified. FFmpeg: {ffmpeg_bin}")

    def test_02_planning_agent(self):
        """Test Planning Agent produces required JSON keys."""
        plan = PlanningAgent.plan(self.test_prompt)
        required_keys = ["topic", "target_audience", "platform", "duration", "tone", "style", "main_message", "hook_strategy"]
        for key in required_keys:
            self.assertIn(key, plan)
        self.assertIsInstance(plan["duration"], int)
        print(f"[Test 2] Planning Agent verified. Topic: {plan['topic']}")

    def test_03_script_agent(self):
        """Test Script Agent generates narration."""
        plan = PlanningAgent.plan(self.test_prompt)
        script = ScriptAgent.generate_script(plan)
        self.assertIsInstance(script, str)
        self.assertTrue(len(script) > 50)
        print(f"[Test 3] Script Agent verified. Length: {len(script)} chars")

    def test_04_scene_extractor(self):
        """Test Scene Extractor breaks script into scenes."""
        plan = PlanningAgent.plan(self.test_prompt)
        script = ScriptAgent.generate_script(plan)
        scenes = SceneAgent.extract_scenes(script, target_duration=plan["duration"])
        self.assertTrue(len(scenes) >= 1)
        for s in scenes:
            self.assertIn("scene_number", s)
            self.assertIn("narration", s)
            self.assertIn("visual_description", s)
            self.assertIn("duration_seconds", s)
        print(f"[Test 4] Scene Extractor verified. {len(scenes)} scenes extracted")

    def test_05_visual_generation(self):
        """Test visual asset creation/download."""
        test_scene = {
            "scene_number": 99,
            "narration": "Test Narration",
            "visual_description": "AI Futuristic Robot in Classroom",
            "search_keywords": "robot student education",
            "duration_seconds": 4
        }
        test_file = Config.VISUALS_DIR / "test_scene_99.jpg"
        saved = AssetDownloader.get_and_save_visual(test_scene, test_file)
        self.assertTrue(os.path.exists(saved))
        self.assertTrue(os.path.getsize(saved) > 1000)
        print(f"[Test 5] Visual generation verified. File size: {os.path.getsize(saved)} bytes")

    def test_06_voice_generator(self):
        """Test voiceover generation produces valid audio file."""
        test_script = "Artificial intelligence is changing the way students learn around the globe."
        res = VoiceGenerator.generate_voiceover(test_script, target_duration=5)
        audio_path = res["audio_path"]
        self.assertTrue(os.path.exists(audio_path))
        self.assertTrue(os.path.getsize(audio_path) > 1000)
        print(f"[Test 6] Voiceover generated via {res['engine']} -> {audio_path}")

    def test_07_subtitle_generator(self):
        """Test subtitle generation produces valid SRT."""
        test_scenes = [
            {"scene_number": 1, "narration": "Artificial intelligence is changing education.", "duration_seconds": 4},
            {"scene_number": 2, "narration": "Students learn in completely new ways.", "duration_seconds": 4}
        ]
        test_srt = Config.SUBTITLES_DIR / "test_captions_unit.srt"
        srt_file = SubtitleGenerator.generate_srt_from_scenes(test_scenes, output_srt=test_srt)
        self.assertTrue(srt_file.exists())
        content = srt_file.read_text(encoding="utf-8")
        self.assertIn("-->", content)
        self.assertIn("Artificial intelligence", content)
        print(f"[Test 7] Subtitles generated and validated.")

    def test_08_end_to_end_video_composition(self):
        """Test full FFmpeg composition of visuals + audio + subtitles into 1080x1920 MP4."""
        test_scenes = [
            {
                "scene_number": 1,
                "narration": "AI tools help college students study faster and retain more.",
                "visual_description": "Modern student digital screen workspace",
                "search_keywords": "study student tech",
                "duration_seconds": 4
            },
            {
                "scene_number": 2,
                "narration": "Discover the incredible power of artificial intelligence today.",
                "visual_description": "Glowing digital knowledge network",
                "search_keywords": "ai future technology",
                "duration_seconds": 4
            }
        ]
        # 1. Visuals
        AssetDownloader.process_all_scenes(test_scenes)
        # 2. Audio
        aud_res = VoiceGenerator.generate_voiceover(
            "AI tools help college students study faster and retain more. Discover the incredible power of artificial intelligence today.",
            target_duration=8
        )
        audio_path = Path(aud_res["audio_path"])
        # 3. Subtitles
        sub_res = SubtitleGenerator.generate_captions(audio_path, test_scenes)
        sub_path = Path(sub_res["subtitles_path"])
        # 4. Composition
        comp_res = VideoComposer.compose_video(test_scenes, audio_path, sub_path)
        video_path = Path(comp_res["video_path"])

        self.assertTrue(video_path.exists())
        self.assertTrue(video_path.stat().st_size > 10000)
        self.assertEqual(comp_res["resolution"], "1080x1920")
        print(f"[Test 8] Video composition succeeded! Size: {comp_res['file_size_mb']} MB -> {video_path}")

        # 5. Quality Control evaluation
        qc_state = {
            "script": "AI tools help college students study faster.",
            "scenes": test_scenes,
            "audio_path": str(audio_path),
            "subtitles_path": str(sub_path),
            "video_path": str(video_path)
        }
        qc_eval = QualityControlAgent.evaluate(qc_state)
        self.assertEqual(qc_eval["status"], "PASS")
        self.assertTrue(qc_eval["quality_score"] >= 80)
        print(f"[Test 8.1] Quality Control Agent verified. Score: {qc_eval['quality_score']}")

    def test_09_seo_agent(self):
        """Test SEO content generator."""
        res = SEOAgent.generate_seo_content("AI in Education", "Sample script text here")
        self.assertIn("youtube_title", res)
        self.assertIn("youtube_description", res)
        self.assertIn("instagram_caption", res)
        self.assertIn("instagram_hashtags", res)
        self.assertTrue(len(res["instagram_hashtags"]) >= 1)
        print(f"[Test 9] SEO Agent verified. Title: {res['youtube_title']}")

    def test_10_scheduler(self):
        """Test date and time parsing with timezone."""
        sched = PublishScheduler.parse_schedule_time(publish_date="2026-10-15", publish_time="19:00", timezone_str="Asia/Kolkata")
        self.assertIn("scheduled_iso", sched)
        self.assertIn("wait_seconds", sched)
        self.assertEqual(sched["publish_date"], "2026-10-15")
        print(f"[Test 10] Scheduler verified. Scheduled ISO: {sched['scheduled_iso']}")

    def test_11_publishing_dry_run(self):
        """Test YouTube and Instagram publishing interfaces."""
        video_path = Config.VIDEOS_DIR / "final_video.mp4"
        if not video_path.exists():
            # Create a tiny placeholder if needed for publish test
            with open(video_path, "wb") as f:
                f.write(b"0" * 20000)

        yt = YouTubePublisher.upload(video_path, "Test YouTube Video", "Description", ["tag1"])
        self.assertEqual(yt["status"], "success")
        self.assertIn("youtube_url", yt)

        ig = InstagramPublisher.publish(video_path, "Test Instagram Reel", ["#ai", "#education"])
        self.assertEqual(ig["status"], "success")
        self.assertIn("instagram_url", ig)
        print(f"[Test 11] Publishing verified. YT: {yt['youtube_url']}, IG: {ig['instagram_url']}")

    def test_12_email_notifications(self):
        """Test Success and Error email notification dispatchers."""
        succ = EmailNotifier.send_success_notification("Test Video", "https://youtube.com/test", "https://instagram.com/test")
        self.assertEqual(succ["status"], "success")

        err = EmailNotifier.send_error_notification("Test Video", "success", "failed", "Instagram token expired")
        self.assertEqual(err["status"], "success")
        print("[Test 12] Email Notifications verified.")

    def test_13_flask_api(self):
        """Test Flask API endpoints."""
        client = app.test_client()
        # Health check
        res = client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "healthy")

        # Plan endpoint
        plan_res = client.post("/api/plan", json={"topic": "Artificial Intelligence in Education"})
        self.assertEqual(plan_res.status_code, 200)
        self.assertIn("topic", plan_res.get_json())
        print("[Test 13] Flask REST API endpoints verified.")

if __name__ == "__main__":
    unittest.main()
