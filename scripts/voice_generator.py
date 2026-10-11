"""
Voice Generator and TTS Engine.
Implements Module 3 Part E of the Agentic AI Video Creation System.
Supports Piper TTS, Google Cloud TTS, ElevenLabs, and Windows SAPI / Local Fallback.
"""

import os
import sys
import wave
import math
import struct
import shutil
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import requests

from .config import Config

logger = logging.getLogger(__name__)

class VoiceGenerator:
    """Generates natural speech audio for the video script."""

    @classmethod
    def generate_piper_tts(cls, text: str, output_wav: Path) -> bool:
        """Invokes Piper TTS CLI binary."""
        piper_bin = shutil.which("piper")
        if not piper_bin:
            return False

        try:
            logger.info("Attempting Piper TTS generation...")
            # piper --model <model> --output_file <out>
            cmd = [
                piper_bin,
                "--model", Config.PIPER_VOICE_MODEL,
                "--output_file", str(output_wav)
            ]
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=text)
            if process.returncode == 0 and output_wav.exists() and output_wav.stat().st_size > 500:
                logger.info(f"Piper TTS successfully created {output_wav}")
                return True
            logger.warning(f"Piper failed: {stderr}")
        except Exception as e:
            logger.warning(f"Piper invocation error: {e}")
        return False

    @classmethod
    def generate_elevenlabs(cls, text: str, output_path: Path) -> bool:
        """Calls ElevenLabs Text-to-Speech API."""
        if not Config.ELEVENLABS_API_KEY:
            return False

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{Config.ELEVENLABS_VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": Config.ELEVENLABS_API_KEY
        }
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        try:
            logger.info("Calling ElevenLabs TTS API...")
            resp = requests.post(url, json=data, headers=headers, timeout=60)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(resp.content)
                logger.info(f"ElevenLabs TTS audio saved to {output_path}")
                return True
            logger.warning(f"ElevenLabs error ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.warning(f"ElevenLabs request failed: {e}")
        return False

    @classmethod
    def generate_google_tts(cls, text: str, output_path: Path) -> bool:
        """Calls Google Cloud Text-to-Speech API."""
        if not (Config.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(Config.GOOGLE_APPLICATION_CREDENTIALS)):
            return False

        try:
            logger.info("Calling Google Cloud Text-to-Speech...")
            from google.cloud import texttospeech
            client = texttospeech.TextToSpeechClient()
            s_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="en-US",
                name="en-US-Neural2-C"
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            response = client.synthesize_speech(
                input=s_input, voice=voice, audio_config=audio_config
            )
            with open(output_path, "wb") as f:
                f.write(response.audio_content)
            logger.info(f"Google TTS audio saved to {output_path}")
            return True
        except Exception as e:
            logger.warning(f"Google TTS failed: {e}")
        return False

    @classmethod
    def generate_windows_sapi(cls, text: str, output_wav: Path) -> bool:
        """Uses Windows built-in speech synthesizer via PowerShell."""
        if os.name != "nt":
            return False

        try:
            logger.info("Using Windows SAPI SpeechSynthesizer for speech generation...")
            # Escape single quotes in text for powershell
            clean_text = text.replace("'", "''").replace("\n", " ")
            ps_script = (
                f"Add-Type -AssemblyName System.Speech; "
                f"$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                f"$synth.SetOutputToWaveFile('{str(output_wav)}'); "
                f"$synth.Speak('{clean_text}'); "
                f"$synth.Dispose();"
            )
            cmd = ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0 and output_wav.exists() and output_wav.stat().st_size > 1000:
                logger.info(f"Windows SAPI voiceover generated at: {output_wav}")
                return True
            logger.warning(f"Windows SAPI returned {result.returncode}: {result.stderr}")
        except Exception as e:
            logger.warning(f"Windows SAPI generation failed: {e}")
        return False

    @classmethod
    def generate_fallback_wav(cls, text: str, output_wav: Path, target_duration: int = 15) -> str:
        """
        Pure Python fallback WAV generator: generates harmonic audio modulated with speech rhythm.
        Guarantees that audio exists even if no external TTS or SAPI is reachable.
        """
        logger.info(f"Generating fallback harmonic voiceover ({target_duration}s)...")
        sample_rate = 24000
        words = text.split()
        estimated_duration = max(5, int(len(words) * 0.4))
        duration = min(estimated_duration, target_duration if target_duration else estimated_duration)
        total_samples = int(sample_rate * duration)

        with wave.open(str(output_wav), "w") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)

            # Generate cadence modulated tones (resembling voice formants)
            frames = bytearray()
            for i in range(total_samples):
                t = i / sample_rate
                # Modulate amplitude with speech-like syllable pauses (3 Hz cadence)
                cadence = 0.5 + 0.5 * math.sin(2 * math.pi * 3.5 * t)
                # Formant frequencies: 220Hz (fundamental), 440Hz, 880Hz
                val = (
                    0.6 * math.sin(2 * math.pi * 220 * t) +
                    0.3 * math.sin(2 * math.pi * 440 * t) +
                    0.1 * math.sin(2 * math.pi * 880 * t)
                ) * cadence * 10000.0
                clamped = max(-32767, min(32767, int(val)))
                frames.extend(struct.pack("<h", clamped))

            wav_file.writeframes(frames)
            
        logger.info(f"Synthetic fallback audio written to: {output_wav}")
        return str(output_wav)

    @classmethod
    def convert_to_mp3_if_needed(cls, wav_path: Path, mp3_path: Path) -> Path:
        """Uses FFmpeg to convert WAV to MP3 if FFmpeg is available, else keeps WAV."""
        ffmpeg_exe = Config.get_ffmpeg_exe()
        try:
            cmd = [
                ffmpeg_exe, "-y",
                "-i", str(wav_path),
                "-codec:a", "libmp3lame",
                "-b:a", "192k",
                str(mp3_path)
            ]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if res.returncode == 0 and mp3_path.exists() and mp3_path.stat().st_size > 500:
                return mp3_path
        except Exception as e:
            logger.info(f"MP3 conversion bypassed, using original audio: {e}")
        return wav_path

    @classmethod
    def generate_voiceover(cls, script: str, output_path: Optional[Path] = None, target_duration: int = 30) -> Dict[str, Any]:
        """
        Main entry point for Voice Generation.
        Tries configured engines in priority order:
        1. ElevenLabs / Google (if credentials present)
        2. Piper TTS (if installed)
        3. Windows SAPI (if on Windows)
        4. High-fidelity harmonic cadence fallback
        """
        target_dir = Config.AUDIO_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        final_mp3 = output_path or (target_dir / "voiceover.mp3")
        temp_wav = target_dir / "voiceover.wav"

        # Check configured engine
        engine_used = "fallback"

        if Config.TTS_ENGINE == "elevenlabs" and cls.generate_elevenlabs(script, final_mp3):
            engine_used = "elevenlabs"
            return {"audio_path": str(final_mp3), "engine": engine_used, "format": "mp3"}

        if Config.TTS_ENGINE == "google" and cls.generate_google_tts(script, final_mp3):
            engine_used = "google"
            return {"audio_path": str(final_mp3), "engine": engine_used, "format": "mp3"}

        if cls.generate_piper_tts(script, temp_wav):
            engine_used = "piper"
            final_audio = cls.convert_to_mp3_if_needed(temp_wav, final_mp3)
            return {"audio_path": str(final_audio), "engine": engine_used, "format": final_audio.suffix[1:]}

        if cls.generate_windows_sapi(script, temp_wav):
            engine_used = "windows_sapi"
            final_audio = cls.convert_to_mp3_if_needed(temp_wav, final_mp3)
            return {"audio_path": str(final_audio), "engine": engine_used, "format": final_audio.suffix[1:]}

        # Fallback harmonic synthesis
        cls.generate_fallback_wav(script, temp_wav, target_duration)
        final_audio = cls.convert_to_mp3_if_needed(temp_wav, final_mp3)
        return {"audio_path": str(final_audio), "engine": "harmonic_synth", "format": final_audio.suffix[1:]}


if __name__ == "__main__":
    test_text = "What if Artificial Intelligence could completely change the way you learn? Discover the future today."
    res = VoiceGenerator.generate_voiceover(test_text)
    print("Voiceover output:", res)
