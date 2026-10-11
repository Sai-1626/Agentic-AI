"""
Flask API Server for Video Automation Pipeline.
Provides endpoints for n8n HTTP Request nodes and full standalone orchestration.
"""

import os
import json
import logging
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

from .config import Config
from .script_generator import PlanningAgent, ScriptAgent
from .scene_extractor import SceneAgent
from .asset_downloader import VisualAgent, AssetDownloader
from .voice_generator import VoiceGenerator
from .subtitle_generator import SubtitleGenerator
from .video_composer import VideoComposer
from .quality_agent import QualityControlAgent
from .seo_agent import SEOAgent
from .scheduler import PublishScheduler
from .publisher import YouTubePublisher, InstagramPublisher
from .notifier import EmailNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("VideoAgentApp")

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint and service status."""
    return jsonify({
        "status": "healthy",
        "service": "agentic-social-media-ai",
        "integrations": Config.get_status_summary()
    })

@app.route("/files/<path:filename>", methods=["GET"])
def serve_file(filename):
    """Serves generated media files from the output directory."""
    return send_from_directory(Config.OUTPUT_DIR, filename)

@app.route("/api/plan", methods=["POST"])
def api_plan():
    """Node 3: Planning Agent."""
    data = request.get_json(force=True) or {}
    prompt = data.get("prompt") or data.get("topic") or data.get("user_prompt", "")
    if not prompt:
        return jsonify({"error": "Prompt or topic required"}), 400
    plan = PlanningAgent.plan(prompt)
    return jsonify(plan)

@app.route("/api/script", methods=["POST"])
def api_script():
    """Node 5: Script Agent."""
    data = request.get_json(force=True) or {}
    script = ScriptAgent.generate_script(data)
    return jsonify({"script": script})

@app.route("/api/scenes", methods=["POST"])
def api_scenes():
    """Node 7: Scene Agent."""
    data = request.get_json(force=True) or {}
    script = data.get("script", "")
    dur = int(data.get("duration", 60))
    scenes = SceneAgent.extract_scenes(script, dur)
    return jsonify({"scenes": scenes})

@app.route("/api/visuals/get", methods=["POST"])
def api_get_visual():
    """Nodes 10 & 11: Visual Prompt + Asset Retrieval for a scene."""
    scene = request.get_json(force=True) or {}
    scene_num = scene.get("scene_number", 1)
    file_path = Config.VISUALS_DIR / f"scene_{scene_num:02d}.jpg"
    prompt = VisualAgent.generate_visual_prompt(scene)
    saved = AssetDownloader.get_and_save_visual(scene, file_path)
    return jsonify({"visual_file": saved, "visual_prompt": prompt})

@app.route("/api/tts", methods=["POST"])
def api_tts():
    """Nodes 13, 14, 15: Voiceover Generation."""
    data = request.get_json(force=True) or {}
    script = data.get("script", "")
    dur = int(data.get("duration", 30))
    res = VoiceGenerator.generate_voiceover(script, target_duration=dur)
    return jsonify(res)

@app.route("/api/transcribe", methods=["POST"])
def api_transcribe():
    """Nodes 16 & 17: Subtitle Caption Generation."""
    data = request.get_json(force=True) or {}
    audio_path = Path(data.get("audio_path", str(Config.AUDIO_DIR / "voiceover.mp3")))
    scenes = data.get("scenes", [])
    res = SubtitleGenerator.generate_captions(audio_path, scenes)
    return jsonify(res)

@app.route("/api/compose", methods=["POST"])
def api_compose():
    """Nodes 18 & 19: Video Composition."""
    data = request.get_json(force=True) or {}
    scenes = data.get("scenes", [])
    audio_path = Path(data.get("audio_path", str(Config.AUDIO_DIR / "voiceover.mp3")))
    srt_path = Path(data.get("subtitles_path", str(Config.SUBTITLES_DIR / "captions.srt")))
    res = VideoComposer.compose_video(scenes, audio_path, srt_path)
    return jsonify(res)

@app.route("/api/qc", methods=["POST"])
def api_qc():
    """Nodes 20, 21, 22: Quality Control."""
    state = request.get_json(force=True) or {}
    res = QualityControlAgent.evaluate(state)
    return jsonify(res)

@app.route("/api/seo", methods=["POST"])
def api_seo():
    """Node 23: SEO Agent."""
    data = request.get_json(force=True) or {}
    topic = data.get("topic", "Technology")
    script = data.get("script", "")
    res = SEOAgent.generate_seo_content(topic, script)
    return jsonify(res)

@app.route("/api/schedule", methods=["POST"])
def api_schedule():
    """Nodes 24 & 25: Scheduling."""
    data = request.get_json(force=True) or {}
    res = PublishScheduler.parse_schedule_time(
        publish_date=data.get("publish_date"),
        publish_time=data.get("publish_time"),
        raw_text=data.get("prompt"),
        timezone_str=data.get("timezone")
    )
    return jsonify(res)

@app.route("/api/publish/youtube", methods=["POST"])
def api_publish_yt():
    """Node 26: YouTube Publish."""
    data = request.get_json(force=True) or {}
    video_path = Path(data.get("video_path", str(Config.VIDEOS_DIR / "final_video.mp4")))
    title = data.get("title", "New Video")
    desc = data.get("description", "")
    tags = data.get("tags", [])
    privacy = data.get("privacy", Config.YOUTUBE_DEFAULT_PRIVACY)
    res = YouTubePublisher.upload(video_path, title, desc, tags, privacy)
    return jsonify(res)

@app.route("/api/publish/instagram", methods=["POST"])
def api_publish_ig():
    """Nodes 28, 29, 30, 31, 32: Instagram Publish."""
    data = request.get_json(force=True) or {}
    video_path = Path(data.get("video_path", str(Config.VIDEOS_DIR / "final_video.mp4")))
    caption = data.get("caption", "New Reel")
    hashtags = data.get("hashtags", [])
    res = InstagramPublisher.publish(video_path, caption, hashtags)
    return jsonify(res)

@app.route("/api/notify/email", methods=["POST"])
def api_notify_email():
    """Nodes 35 & 36: Email Notification."""
    data = request.get_json(force=True) or {}
    is_success = data.get("success", True)
    title = data.get("title", "Video Automation")
    recipient = data.get("recipient")

    if is_success:
        res = EmailNotifier.send_success_notification(
            video_title=title,
            youtube_url=data.get("youtube_url", ""),
            instagram_url=data.get("instagram_url", ""),
            recipient=recipient
        )
    else:
        res = EmailNotifier.send_error_notification(
            video_title=title,
            youtube_status=data.get("youtube_status", "failed"),
            instagram_status=data.get("instagram_status", "failed"),
            error_message=data.get("error_message", "Unknown error"),
            recipient=recipient
        )
    return jsonify(res)

@app.route("/generate", methods=["POST"])
def generate():
    """
    End-to-End Pipeline Execution.
    Executes the entire 37-node flow synchronously or triggers scheduled run.
    """
    body = request.get_json(force=True) or {}
    prompt = body.get("prompt") or body.get("topic") or body.get("user_prompt", "")

    if not prompt:
        return jsonify({"status": "error", "message": "Missing 'prompt' or 'topic' parameter"}), 400

    logger.info(f"Starting End-to-End Video Generation Pipeline for: '{prompt}'")

    # 1. Content Planning
    plan = PlanningAgent.plan(prompt)
    topic = plan.get("topic", "AI Video")
    target_dur = plan.get("duration", 60)

    # 2. Script Generation
    script = ScriptAgent.generate_script(plan)

    # 3. Scene Breakdown
    scenes = SceneAgent.extract_scenes(script, target_duration=target_dur)

    # 4. Visual Retrieval / Generation
    AssetDownloader.process_all_scenes(scenes)

    # 5. Voiceover Generation
    voice_res = VoiceGenerator.generate_voiceover(script, target_duration=target_dur)
    audio_path = Path(voice_res["audio_path"])

    # 6. Subtitles Generation
    sub_res = SubtitleGenerator.generate_captions(audio_path, scenes)
    subtitles_path = Path(sub_res["subtitles_path"])

    # 7. Video Composition
    comp_res = VideoComposer.compose_video(scenes, audio_path, subtitles_path)
    video_path = Path(comp_res["video_path"])

    # 8. Quality Control
    qc_state = {
        "script": script,
        "scenes": scenes,
        "audio_path": str(audio_path),
        "subtitles_path": str(subtitles_path),
        "video_path": str(video_path)
    }
    qc_res = QualityControlAgent.evaluate(qc_state)

    if qc_res.get("status") == "FAIL":
        logger.warning(f"QC check reported issues: {qc_res.get('issues')}. Attempting auto-repair...")
        # Auto repair: re-verify visuals and re-compose
        AssetDownloader.process_all_scenes(scenes)
        comp_res = VideoComposer.compose_video(scenes, audio_path, subtitles_path)
        video_path = Path(comp_res["video_path"])
        qc_state["video_path"] = str(video_path)
        qc_res = QualityControlAgent.evaluate(qc_state)

    # 9. SEO Metadata
    seo_res = SEOAgent.generate_seo_content(topic, script)

    # 10. Scheduling Check
    schedule_info = PublishScheduler.parse_schedule_time(
        publish_date=body.get("publish_date"),
        publish_time=body.get("publish_time"),
        raw_text=prompt
    )

    # 11. Publishing
    yt_res = YouTubePublisher.upload(
        video_path=video_path,
        title=seo_res.get("youtube_title", topic),
        description=seo_res.get("youtube_description", ""),
        tags=seo_res.get("youtube_tags", [])
    )

    ig_res = InstagramPublisher.publish(
        video_path=video_path,
        caption=seo_res.get("instagram_caption", topic),
        hashtags=seo_res.get("instagram_hashtags", [])
    )

    # 12. Email Notification
    pub_success = (yt_res.get("status") == "success") and (ig_res.get("status") == "success")
    if pub_success:
        EmailNotifier.send_success_notification(
            video_title=seo_res.get("youtube_title", topic),
            youtube_url=yt_res.get("youtube_url", ""),
            instagram_url=ig_res.get("instagram_url", ""),
            recipient=body.get("email")
        )
    else:
        EmailNotifier.send_error_notification(
            video_title=seo_res.get("youtube_title", topic),
            youtube_status=yt_res.get("status", "failed"),
            instagram_status=ig_res.get("status", "failed"),
            error_message=f"YouTube: {yt_res.get('error')}, Instagram: {ig_res.get('error')}",
            recipient=body.get("email")
        )

    # 13. Node 37 Final Webhook Response
    response_payload = {
        "status": "success" if pub_success else "partial_success",
        "message": "Your social media video has been created and published successfully.",
        "video": "final_video.mp4",
        "video_path": str(video_path),
        "youtube_url": yt_res.get("youtube_url"),
        "instagram_url": ig_res.get("instagram_url"),
        "caption": seo_res.get("instagram_caption"),
        "hashtags": " ".join(seo_res.get("instagram_hashtags", [])),
        "quality_score": qc_res.get("quality_score", 95),
        "schedule": schedule_info
    }
    return jsonify(response_payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=Config.PORT, debug=False)
