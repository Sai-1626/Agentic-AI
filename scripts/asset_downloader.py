"""
Visual Prompt Agent and Asset Downloader.
Implements Module 3 Part D of the Agentic AI Video Creation System.
"""

import os
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import requests
from PIL import Image, ImageDraw, ImageFont

from .config import Config
from .script_generator import LLMClient

logger = logging.getLogger(__name__)

class VisualAgent:
    """Refines scene visual descriptions into optimized vertical 9:16 visual prompts."""

    SYSTEM_PROMPT = "You are an AI Visual Director."

    @classmethod
    def generate_visual_prompt(cls, scene: Dict[str, Any]) -> str:
        """Generates an enhanced visual prompt for the scene."""
        narration = scene.get("narration", "")
        visual_desc = scene.get("visual_description", "")

        llm_prompt = f"""You are an AI Visual Director.

Create a high-quality visual description for this scene.

Scene Narration:
{narration}

Current Visual Description:
{visual_desc}

Create a detailed visual search prompt.

The visual should be suitable for:
- Instagram Reel
- Vertical Format
- 9:16 Aspect Ratio
- Professional Quality

Return only the visual prompt. No preamble."""

        raw = LLMClient.generate(llm_prompt, cls.SYSTEM_PROMPT)
        if raw and len(raw.strip()) > 20:
            return raw.strip().strip('"')

        # Heuristic enhancement
        return (
            f"Professional cinematic vertical shot of {visual_desc}, "
            "vibrant studio lighting, sharp focus, modern aesthetic, 9:16 vertical social media composition."
        )


class AssetDownloader:
    """Fetches stock images/videos from Pexels/Pixabay or generates synthetic 1080x1920 visuals."""

    @classmethod
    def search_pexels(cls, query: str) -> Optional[str]:
        """Search Pexels API for vertical photo or video."""
        if not Config.PEXELS_API_KEY:
            return None
        
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": Config.PEXELS_API_KEY}
        params = {"query": query, "orientation": "portrait", "per_page": 5}
        try:
            resp = requests.get(url, headers=headers, params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                photos = data.get("photos", [])
                if photos:
                    # Pick portrait or large image url
                    return photos[0]["src"].get("portrait") or photos[0]["src"].get("large")
        except Exception as e:
            logger.warning(f"Pexels search failed: {e}")
        return None

    @classmethod
    def search_pixabay(cls, query: str) -> Optional[str]:
        """Search Pixabay API for images."""
        if not Config.PIXABAY_API_KEY:
            return None
        url = "https://pixabay.com/api/"
        params = {
            "key": Config.PIXABAY_API_KEY,
            "q": query,
            "image_type": "photo",
            "orientation": "vertical",
            "per_page": 5
        }
        try:
            resp = requests.get(url, params=params, timeout=15)
            if resp.status_code == 200:
                hits = resp.json().get("hits", [])
                if hits:
                    return hits[0].get("largeImageURL") or hits[0].get("webformatURL")
        except Exception as e:
            logger.warning(f"Pixabay search failed: {e}")
        return None

    @classmethod
    def download_url(cls, image_url: str, output_path: Path) -> bool:
        """Downloads an image from a URL and saves it."""
        try:
            resp = requests.get(image_url, timeout=30, stream=True)
            if resp.status_code == 200:
                with open(output_path, "wb") as f:
                    for chunk in resp.iter_content(1024 * 32):
                        f.write(chunk)
                return True
        except Exception as e:
            logger.warning(f"Failed to download image from {image_url}: {e}")
        return False

    @classmethod
    def generate_synthetic_visual(cls, scene: Dict[str, Any], output_path: Path) -> str:
        """
        Creates a high-resolution vertical (1080x1920) background card.
        Ensures 100% reliability offline or without external API keys.
        """
        width = Config.VIDEO_WIDTH
        height = Config.VIDEO_HEIGHT
        scene_num = scene.get("scene_number", 1)
        narration = scene.get("narration", "")
        keywords = scene.get("search_keywords", "AI Concept")

        # Color palette cycling based on scene number
        palettes = [
            ((15, 23, 42), (59, 130, 246)),     # Deep slate to bright blue
            ((30, 27, 75), (147, 51, 234)),     # Deep purple to vibrant violet
            ((19, 78, 74), (20, 184, 166)),     # Deep teal to bright cyan
            ((88, 28, 135), (236, 72, 153)),    # Magenta gradient
            ((17, 24, 39), (99, 102, 241))      # Indigo night
        ]
        c1, c2 = palettes[(scene_num - 1) % len(palettes)]

        # Generate vertical gradient
        img = Image.new("RGB", (width, height), c1)
        draw = ImageDraw.Draw(img)

        # Draw vertical gradient lines
        for y in range(height):
            ratio = y / height
            r = int(c1[0] * (1 - ratio) + c2[0] * ratio)
            g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
            b = int(c1[2] * (1 - ratio) + c2[2] * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Add tech grid overlay aesthetic
        for gx in range(0, width, 120):
            draw.line([(gx, 0), (gx, height)], fill=(255, 255, 255, 20), width=1)
        for gy in range(0, height, 120):
            draw.line([(0, gy), (width, gy)], fill=(255, 255, 255, 20), width=1)

        # Center card container
        card_x0, card_y0 = 80, 480
        card_x1, card_y1 = width - 80, 1440
        draw.rectangle([card_x0, card_y0, card_x1, card_y1], fill=(10, 15, 30), outline=(255, 255, 255), width=3)

        # Header Badge
        badge_text = f"SCENE {scene_num:02d} • {keywords.upper()[:28]}"
        draw.text((120, card_y0 + 50), badge_text, fill=(56, 189, 248))

        # Scene Visual Description Snippet
        summary = scene.get("visual_description", narration)[:140]
        # Wrap text simply
        words = summary.split()
        lines = []
        cur_line = ""
        for w in words:
            if len(cur_line + " " + w) > 30:
                lines.append(cur_line)
                cur_line = w
            else:
                cur_line = f"{cur_line} {w}".strip()
        if cur_line:
            lines.append(cur_line)

        ty = card_y0 + 160
        for line in lines[:6]:
            draw.text((120, ty), line, fill=(241, 245, 249))
            ty += 45

        # Save image
        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "JPEG", quality=92)
        logger.info(f"Generated synthetic visual: {output_path}")
        return str(output_path)

    @classmethod
    def get_and_save_visual(cls, scene: Dict[str, Any], output_path: Path) -> str:
        """
        Attempts stock API download first, then seamlessly falls back to synthetic high-res generation.
        """
        query = scene.get("search_keywords") or scene.get("visual_description", "technology")
        # Try Pexels
        img_url = cls.search_pexels(query)
        if not img_url:
            # Try Pixabay
            img_url = cls.search_pixabay(query)

        if img_url:
            success = cls.download_url(img_url, output_path)
            if success and output_path.exists() and output_path.stat().st_size > 1000:
                logger.info(f"Downloaded online asset for Scene {scene.get('scene_number')} -> {output_path}")
                return str(output_path)

        # Fallback to synthetic high-res 9:16 vertical card
        return cls.generate_synthetic_visual(scene, output_path)

    @classmethod
    def process_all_scenes(cls, scenes: list, output_dir: Optional[Path] = None) -> list:
        """Processes and downloads visuals for all scenes."""
        target_dir = output_dir or Config.VISUALS_DIR
        target_dir.mkdir(parents=True, exist_ok=True)
        
        visual_files = []
        for scene in scenes:
            scene_num = scene.get("scene_number", 1)
            file_name = f"scene_{scene_num:02d}.jpg"
            file_path = target_dir / file_name
            # Generate visual prompt
            scene["visual_prompt"] = VisualAgent.generate_visual_prompt(scene)
            saved_path = cls.get_and_save_visual(scene, file_path)
            scene["visual_file"] = saved_path
            visual_files.append(saved_path)
            
        return visual_files


if __name__ == "__main__":
    test_scene = {
        "scene_number": 1,
        "narration": "What if AI could completely change the way you learn?",
        "visual_description": "Futuristic student studying with interactive holograms",
        "search_keywords": "ai education student",
        "duration_seconds": 5
    }
    out = Config.VISUALS_DIR / "test_scene_01.jpg"
    res = AssetDownloader.get_and_save_visual(test_scene, out)
    print("Visual generated at:", res)
