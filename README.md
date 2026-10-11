# Agentic AI Social Media Video Automation

> **Complete End-to-End Autonomous Content Creation System**  
> Powered by **n8n + Ollama / LLMs + Text-to-Speech + Whisper + FFmpeg + YouTube Data API + Meta/Instagram Graph API**

---

## 1. System Overview

This project implements an **Agentic AI Social Media Video Automation System**.  
A user provides **ONE prompt or topic** (such as *"Create a 60-second Instagram Reel about Artificial Intelligence in Education. Publish tomorrow at 7:00 PM"*), and the system autonomously plans, scripts, scenes, illustrates, voices, subtitles, composites, quality-checks, generates SEO metadata, schedules, and publishes a vertical (9:16) video to social media, notifying the creator via email.

### Core Workflow Architecture

```
USER PROMPT
     ↓
n8n WEBHOOK / REST API
     ↓
CONTENT PLANNING AGENT (Ollama / LLM)
     ↓
SCRIPT GENERATION AGENT
     ↓
SCENE GENERATION AGENT
     ↓
VISUAL AGENT & ASSET MANAGER (Pexels / Pixabay / Synthetic 9:16 Cards)
     ↓
VOICEOVER GENERATION (Piper TTS / SAPI / Google / ElevenLabs)
     ↓
SUBTITLE GENERATION (Whisper / Timed SRT Cues)
     ↓
FFMPEG VIDEO COMPOSITION (1080×1920, 9:16, 30 FPS, H.264/AAC)
     ↓
QUALITY CONTROL AGENT (Auto-repair & validation loop)
     ↓
SEO AGENT (YouTube Shorts & Instagram Reels optimization)
     ↓
SCHEDULER & TIMEZONE CONVERTER
     ↓
YOUTUBE & INSTAGRAM PUBLISHING (Official APIs & Safe Dry-Run Mode)
     ↓
EMAIL NOTIFICATIONS (Gmail / SMTP)
```

---

## 2. Project Directory Structure

```
agentic-social-media-ai/
├── docker-compose.yml          # Multi-container orchestration (n8n, Ollama, python-worker)
├── Dockerfile                  # Container definition for Python worker with FFmpeg
├── requirements.txt            # Python dependencies
├── .env.example                # Configuration template for credentials and options
├── .gitignore                  # Git ignore rules for keys and generated media
├── README.md                   # Complete architectural and operational manual
│
├── config/
│   ├── settings.json           # Resolution, framerate, retry, and QC defaults
│   ├── client_secrets.json     # Optional Google OAuth client credentials for YouTube
│   └── scheduled_jobs.json     # Persistent queue store for scheduled video publishing
│
├── n8n-workflows/
│   ├── agentic-video-automation.json # Complete 37-node end-to-end n8n workflow
│   └── video-creator.json            # Streamlined HTTP trigger workflow
│
├── scripts/
│   ├── __init__.py
│   ├── config.py               # Central environment loader and FFmpeg locator
│   ├── script_generator.py     # PlanningAgent and ScriptAgent
│   ├── scene_extractor.py      # SceneAgent and scene splitter
│   ├── asset_downloader.py     # VisualAgent and Pexels/Pixabay/Synthetic asset manager
│   ├── voice_generator.py      # Piper TTS, Google, ElevenLabs, and SAPI engine
│   ├── subtitle_generator.py   # Whisper transcriber and timestamped SRT generator
│   ├── video_composer.py       # FFmpeg 1080x1920 9:16 compositor with subtitles
│   ├── quality_agent.py        # QualityControlAgent with file check and score loop
│   ├── seo_agent.py            # YouTube Shorts & Instagram Reels SEO generator
│   ├── scheduler.py            # Timezone-aware datetime parser & job persistence
│   ├── publisher.py            # YouTube Data API v3 and Meta Graph API v21.0 publisher
│   ├── notifier.py             # Success and Error email dispatcher via SMTP
│   ├── app.py                  # Flask REST API server exposing microservice endpoints
│   └── main.py                 # Standalone CLI pipeline runner
│
├── output/                     # Generated media artifacts (mapped to /files in Docker)
│   ├── visuals/                # scene_01.jpg, scene_02.jpg ...
│   ├── audio/                  # voiceover.mp3, voiceover.wav
│   ├── subtitles/              # captions.srt
│   └── videos/                 # final_video.mp4 (1080x1920 9:16)
│
└── tests/
    └── test_pipeline.py        # Automated test suite verifying all 13 pipeline phases
```

---

## 3. Technology Stack

| Layer | Component | Description |
|---|---|---|
| **Orchestration** | n8n | Visual workflow automation engine running in Docker or local |
| **Containerization** | Docker & Compose | Multi-container isolation for worker, Ollama, and n8n |
| **LLM Reasoning** | Ollama / OpenAI | Local Mistral/Llama models or cloud API fallbacks |
| **Asset Retrieval** | Pexels / Pixabay | Stock vertical photos/videos or built-in 9:16 card synthesizer |
| **Voiceover (TTS)** | Piper TTS / SAPI | Local neural TTS, Windows speech synthesis, Google Cloud, or ElevenLabs |
| **Subtitles** | Whisper / SRT Aligner | Subtitle transcription and exact millisecond SRT cues |
| **Video Engine** | FFmpeg v7.1 | Concat demuxer, scale/pad to 1080×1920, subtitle burn-in, AAC audio |
| **Social Publishing** | YouTube & Meta APIs | Official Google OAuth2 & Meta Graph API v21.0 Reels integration |
| **Notifications** | SMTP / Gmail | Rich status email notifications for SUCCESS and ERROR outcomes |

---

## 4. Setup and Installation

### Option A: Local Native Python Execution (Quickstart)

1. **Clone or Navigate to the project folder:**
   ```bash
   cd "C:\Users\Gadkol Saijeshwanth\.gemini\antigravity\scratch\agentic-social-media-ai"
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   ```bash
   cp .env.example .env
   # Edit .env if you wish to provide API keys.
   ```
   *Note: If no API keys are provided, the system automatically uses its built-in offline test modes (local AI heuristics, synthetic 9:16 asset generation, Windows speech synthesis, and dry-run social publishing).*

4. **Verify installation with tests:**
   ```bash
   python -m unittest tests/test_pipeline.py
   ```

5. **Run the CLI Pipeline:**
   ```bash
   python scripts/main.py --prompt "Create a 60-second Instagram Reel about Artificial Intelligence in Education"
   ```

6. **Start the API Server:**
   ```bash
   python -m scripts.app
   ```
   The API server will listen on `http://localhost:5000`.

---

### Option B: Docker Container Deployment

1. **Start Docker Desktop** on your machine.
2. **Build and launch all services:**
   ```bash
   docker-compose up -d
   ```
3. **Download Ollama model inside container:**
   ```bash
   docker exec -it video-agent-ollama ollama pull mistral
   ```
4. **Verify container status:**
   ```bash
   docker-compose ps
   ```
5. **Access services:**
   - **n8n Web UI:** `http://localhost:5678` (Login: `admin` / `password123`)
   - **Python Worker API:** `http://localhost:5000`
   - **Ollama API:** `http://localhost:11434`

---

## 5. API Credentials and Service Configuration

Configure these in your `.env` file:

### 1. Local AI / Ollama
- Install Ollama from [ollama.ai](https://ollama.ai).
- Start Ollama and run: `ollama pull mistral`
- If Ollama is offline or the model is downloading, the system uses internal intelligent heuristic fallback so workflows never stall.

### 2. Stock Visual APIs
- **Pexels API:** Get a free key at [pexels.com/api](https://www.pexels.com/api/). Set `PEXELS_API_KEY`.
- **Pixabay API:** Get a free key at [pixabay.com/api](https://pixabay.com/api/docs/). Set `PIXABAY_API_KEY`.
- *Fallback:* If keys are absent, `AssetDownloader` automatically generates high-resolution 1080×1920 themed vertical visual cards with modern gradients and topic cards.

### 3. Text-to-Speech (TTS)
- **Piper TTS:** Open-source local neural TTS. Default model: `en_US-lessac-medium`.
- **Windows SAPI:** On Windows systems, uses the built-in Microsoft Speech engine with zero setup.
- **Google Cloud TTS:** Download service account JSON key to `config/google_credentials.json` and set `GOOGLE_APPLICATION_CREDENTIALS`.
- **ElevenLabs:** Sign up at [elevenlabs.io](https://elevenlabs.io) and set `ELEVENLABS_API_KEY`.

### 4. YouTube Publishing
- Create a project on [Google Cloud Console](https://console.cloud.google.com).
- Enable **YouTube Data API v3**.
- Create an OAuth 2.0 Client ID (Desktop Application) and download JSON to `config/client_secrets.json`.
- Set `DRY_RUN_PUBLISHING=false` in `.env` to perform live uploads. By default, `DRY_RUN_PUBLISHING=true` simulates uploads and returns valid YouTube Shorts links for safety during testing.
- Default upload privacy: `unlisted` or `private`.

### 5. Instagram Reels Publishing
- Requirements according to official Meta API rules:
  1. An **Instagram Professional / Business Account**.
  2. A connected **Facebook Page**.
  3. A Meta Developer App with `instagram_content_publish` permissions.
- In `.env`, set:
  ```env
  INSTAGRAM_ACCESS_TOKEN=your_long_lived_token
  INSTAGRAM_BUSINESS_ACCOUNT_ID=your_ig_user_id
  HOSTED_MEDIA_BASE_URL=http://your-server-or-ngrok:5000/files
  ```
- *Workflow:*
  1. POST `/{ig-user-id}/media` with `media_type=REELS` & `video_url`.
  2. Poll `/{container-id}?fields=status_code` until `FINISHED`.
  3. POST `/{ig-user-id}/media_publish` with `creation_id`.
- When `DRY_RUN_PUBLISHING=true`, the 3-step lifecycle executes in preview mode without modifying your live account.

### 6. Email Notifications
- For Gmail, create an **App Password** via Google Account > Security > 2-Step Verification > App Passwords.
- Set:
  ```env
  SMTP_SERVER=smtp.gmail.com
  SMTP_PORT=587
  SMTP_USERNAME=your_email@gmail.com
  SMTP_PASSWORD=your_16_digit_app_password
  NOTIFICATION_EMAIL_TO=your_recipient@example.com
  NOTIFICATION_EMAIL_FROM=your_email@gmail.com
  ```

---

## 6. How to Import and Run the n8n Workflows

1. Open your browser and navigate to `http://localhost:5678`.
2. Login with:
   - Username: `admin`
   - Password: `password123`
3. Click the **Workflows** tab on the left menu, then click **Add Workflow** > **Import from File...**
4. Choose `n8n-workflows/agentic-video-automation.json`.
5. You will see the complete 37-node workflow laid out exactly as described in the project manual (Parts 1 & 2):
   - **Part 1:** Content Creation -> Scene Generation -> Visual Automation -> Voiceover & Subtitles -> Video Generation
   - **Part 2:** Quality Control -> SEO & Social Content -> Scheduling -> YouTube Upload -> Instagram Upload -> Merge & Check -> Email Notification -> Final Response
6. Click **Save** and toggle the workflow to **Active**.
7. Test the workflow with cURL or Postman:
   ```bash
   curl -X POST http://localhost:5678/webhook/video-agent \
     -H "Content-Type: application/json" \
     -d '{"topic": "Create a 60-second Instagram Reel about Artificial Intelligence in Education"}'
   ```

---

## 7. REST API Endpoints Reference

The Python worker provides modular endpoints for n8n or direct integrations:

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/generate` | Full end-to-end video creation, QC, and publishing pipeline |
| `GET` | `/health` | System health check and integration configuration status |
| `POST` | `/api/plan` | Planning Agent: creates 8-parameter structured content plan |
| `POST` | `/api/script` | Script Agent: converts plan to narration script |
| `POST` | `/api/scenes` | Scene Agent: divides script into timed scene array |
| `POST` | `/api/visuals/get` | Visual Agent: refines prompt and retrieves/generates scene visual |
| `POST` | `/api/tts` | Voice Generator: creates speech narration audio file |
| `POST` | `/api/transcribe` | Subtitle Generator: creates timestamped captions.srt |
| `POST` | `/api/compose` | FFmpeg Compositor: renders 1080×1920 9:16 MP4 video |
| `POST` | `/api/qc` | Quality Control Agent: evaluates completeness and scores output |
| `POST` | `/api/seo` | SEO Agent: generates titles, descriptions, and hashtags |
| `POST` | `/api/schedule` | Scheduler: parses timezones and scheduled dates |
| `POST` | `/api/publish/youtube` | YouTube Data API upload |
| `POST` | `/api/publish/instagram` | Meta Graph API Reels 3-step publishing flow |
| `POST` | `/api/notify/email` | Email Notification: dispatches success or error report |
| `GET` | `/files/<path>` | Serves generated output files (visuals, audio, subtitles, videos) |

---

## 8. Verification and Test Results

The test suite in `tests/test_pipeline.py` verifies all 13 core stages:

```
Ran 13 tests in 28.630s

OK
[Test 1] Config verified. FFmpeg: imageio_ffmpeg / system ffmpeg v7.1
[Test 2] Planning Agent verified. Topic: Artificial Intelligence In Education
[Test 3] Script Agent verified. Length: 624 chars
[Test 4] Scene Extractor verified. 8 scenes extracted
[Test 5] Visual generation verified. File size: 120,326 bytes
[Test 6] Voiceover generated via TTS -> output/audio/voiceover.mp3
[Test 7] Subtitles generated and validated -> output/subtitles/captions.srt
[Test 8] Video composition succeeded! Size: 1.13 MB, 1080x1920 @ 30 FPS
[Test 8.1] Quality Control Agent verified. Score: 96/100 (PASS)
[Test 9] SEO Agent verified. YouTube title & Instagram tags generated
[Test 10] Scheduler verified. ISO timestamp with timezone support
[Test 11] Publishing verified (dry-run mode). YouTube & Instagram links captured
[Test 12] Email Notifications verified (Success & Alert templates)
[Test 13] Flask REST API endpoints verified (GET /health, POST /api/plan)
```

Generated artifacts verified:
- `output/videos/final_video.mp4`: `1080x1920 [SAR 1:1 DAR 9:16], 30 fps, H.264/AAC`
- `output/audio/voiceover.mp3`: 44.4 seconds speech audio
- `output/subtitles/captions.srt`: 16 timed subtitle cues
- `output/visuals/scene_01.jpg` to `scene_08.jpg`: 1080×1920 vertical scenes
