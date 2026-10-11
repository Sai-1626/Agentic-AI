"""
Configuration module for Agentic AI Social Media Video Automation.
Loads environment variables and validates system configuration.
"""

import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file if present
ENV_PATH = BASE_DIR / ".env"
if ENV_PATH.exists():
    load_dotenv(dotenv_path=ENV_PATH)
else:
    load_dotenv()  # Fallback to current working directory

class Config:
    """Central configuration class with smart fallbacks."""
    BASE_DIR = BASE_DIR
    
    # Storage Directories
    # In docker, /files is mapped to ./output. Locally, we use BASE_DIR / "output"
    if os.name != 'nt' and Path("/files").exists() and os.access("/files", os.W_OK):
        OUTPUT_DIR = Path("/files")
    else:
        OUTPUT_DIR = BASE_DIR / "output"

    VISUALS_DIR = OUTPUT_DIR / "visuals"
    AUDIO_DIR = OUTPUT_DIR / "audio"
    SUBTITLES_DIR = OUTPUT_DIR / "subtitles"
    VIDEOS_DIR = OUTPUT_DIR / "videos"
    CONFIG_DIR = BASE_DIR / "config"

    # Ensure output directories exist
    for directory in [OUTPUT_DIR, VISUALS_DIR, AUDIO_DIR, SUBTITLES_DIR, VIDEOS_DIR, CONFIG_DIR]:
        directory.mkdir(parents=True, exist_ok=True)

    # LLM Settings
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_MODEL = os.getenv("LLM_MODEL", "mistral")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # Stock Asset Providers
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY", "")
    PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY", "")
    UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "")

    # TTS Settings
    TTS_ENGINE = os.getenv("TTS_ENGINE", "piper").lower()  # piper, google, elevenlabs, local
    PIPER_VOICE_MODEL = os.getenv("PIPER_VOICE_MODEL", "en_US-lessac-medium")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

    # Subtitle / Whisper Settings
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")

    # Video Settings
    VIDEO_WIDTH = int(os.getenv("VIDEO_WIDTH", "1080"))
    VIDEO_HEIGHT = int(os.getenv("VIDEO_HEIGHT", "1920"))
    VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))
    VIDEO_ASPECT_RATIO = "9:16"

    # Social Publishing Settings
    DRY_RUN_PUBLISHING = os.getenv("DRY_RUN_PUBLISHING", "true").lower() in ("true", "1", "yes")
    YOUTUBE_CLIENT_SECRETS_FILE = os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", str(CONFIG_DIR / "client_secrets.json"))
    YOUTUBE_CREDENTIALS_FILE = os.getenv("YOUTUBE_CREDENTIALS_FILE", str(CONFIG_DIR / "youtube_token.json"))
    YOUTUBE_DEFAULT_PRIVACY = os.getenv("YOUTUBE_DEFAULT_PRIVACY", "unlisted")  # private, unlisted, public

    INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID", "")
    INSTAGRAM_GRAPH_VERSION = os.getenv("INSTAGRAM_GRAPH_VERSION", "v21.0")
    HOSTED_MEDIA_BASE_URL = os.getenv("HOSTED_MEDIA_BASE_URL", "http://localhost:5000/files")

    # Scheduling Settings
    DEFAULT_TIMEZONE = os.getenv("DEFAULT_TIMEZONE", "Asia/Kolkata")
    SCHEDULE_STORE_FILE = CONFIG_DIR / "scheduled_jobs.json"

    # Email / Notification Settings
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    NOTIFICATION_EMAIL_TO = os.getenv("NOTIFICATION_EMAIL_TO", "")
    NOTIFICATION_EMAIL_FROM = os.getenv("NOTIFICATION_EMAIL_FROM", "")

    # Web Server & n8n Settings
    PORT = int(os.getenv("PORT", "5000"))
    N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/video-agent")

    @classmethod
    def get_ffmpeg_exe(cls) -> str:
        """Find or return path to FFmpeg binary executable."""
        env_ffmpeg = os.getenv("FFMPEG_PATH")
        if env_ffmpeg and os.path.exists(env_ffmpeg):
            return env_ffmpeg
        
        sys_ffmpeg = shutil.which("ffmpeg")
        if sys_ffmpeg:
            return sys_ffmpeg
            
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            return "ffmpeg"

    @classmethod
    def get_status_summary(cls) -> dict:
        """Return configured status of all external services and credentials."""
        return {
            "llm": {
                "ollama_url": cls.OLLAMA_BASE_URL,
                "model": cls.LLM_MODEL,
                "openai_configured": bool(cls.OPENAI_API_KEY)
            },
            "visuals": {
                "pexels": bool(cls.PEXELS_API_KEY),
                "pixabay": bool(cls.PIXABAY_API_KEY),
                "unsplash": bool(cls.UNSPLASH_ACCESS_KEY),
                "local_fallback_available": True
            },
            "tts": {
                "engine": cls.TTS_ENGINE,
                "google_configured": bool(cls.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(cls.GOOGLE_APPLICATION_CREDENTIALS)),
                "elevenlabs_configured": bool(cls.ELEVENLABS_API_KEY),
                "local_synth_available": True
            },
            "ffmpeg": {
                "binary": cls.get_ffmpeg_exe(),
                "available": bool(cls.get_ffmpeg_exe())
            },
            "publishing": {
                "dry_run": cls.DRY_RUN_PUBLISHING,
                "youtube_oauth_configured": bool(os.path.exists(cls.YOUTUBE_CLIENT_SECRETS_FILE)),
                "instagram_configured": bool(cls.INSTAGRAM_ACCESS_TOKEN and cls.INSTAGRAM_BUSINESS_ACCOUNT_ID)
            },
            "notifications": {
                "smtp_configured": bool(cls.SMTP_USERNAME and cls.SMTP_PASSWORD and cls.NOTIFICATION_EMAIL_TO)
            }
        }
