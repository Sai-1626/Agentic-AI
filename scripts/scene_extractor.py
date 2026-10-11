"""
Scene Extractor and Scene Agent.
Implements Module 2 Part C of the Agentic AI Video Creation System.
"""

import json
import logging
import re
from typing import Dict, Any, List

from .script_generator import LLMClient, clean_json_string

logger = logging.getLogger(__name__)

class SceneAgent:
    """Divides complete script into timed visual scenes."""

    SYSTEM_PROMPT = "You are a professional video director."

    @classmethod
    def extract_scenes(cls, script: str, target_duration: int = 60) -> List[Dict[str, Any]]:
        """Splits script into scene list with narration, visual description, keywords, and durations."""
        logger.info(f"SceneAgent dividing script into scenes (target duration: {target_duration}s)...")

        llm_prompt = f"""You are a professional video director.

Divide the following video script into scenes.

For each scene provide:
1. scene_number
2. narration
3. visual_description
4. search_keywords
5. duration_seconds

The total duration should match approximately {target_duration} seconds.
Each scene should typically last between 4 and 8 seconds.

Return ONLY valid JSON in this format:
{{
  "scenes": [
    {{
      "scene_number": 1,
      "narration": "What if AI could completely change the way you learn?",
      "visual_description": "College student using futuristic AI learning technology",
      "search_keywords": "student artificial intelligence education",
      "duration_seconds": 5
    }}
  ]
}}

SCRIPT:
{script}"""

        raw_response = LLMClient.generate(llm_prompt, cls.SYSTEM_PROMPT)
        scenes = []

        if raw_response:
            try:
                cleaned = clean_json_string(raw_response)
                parsed = json.loads(cleaned)
                if isinstance(parsed, dict) and "scenes" in parsed:
                    scenes = parsed["scenes"]
                elif isinstance(parsed, list):
                    scenes = parsed
            except Exception as e:
                logger.warning(f"Failed parsing LLM scenes output ({e}). Using intelligent splitter.")

        if not scenes:
            scenes = cls._heuristic_scene_splitter(script, target_duration)

        # Validate and normalize scenes
        normalized_scenes = []
        for i, s in enumerate(scenes, 1):
            dur = s.get("duration_seconds", 5)
            try:
                dur = max(3, int(dur))
            except Exception:
                dur = 5

            narr = str(s.get("narration", "")).strip()
            v_desc = str(s.get("visual_description", "")).strip() or f"Visual concept representing: {narr[:60]}"
            keywords = str(s.get("search_keywords", "")).strip() or "technology education learning"

            normalized_scenes.append({
                "scene_number": i,
                "narration": narr,
                "visual_description": v_desc,
                "search_keywords": keywords,
                "duration_seconds": dur
            })

        # Ensure total duration roughly balances to target_duration
        current_total = sum(s["duration_seconds"] for s in normalized_scenes)
        if current_total > 0 and abs(current_total - target_duration) > 5:
            ratio = target_duration / current_total
            for s in normalized_scenes:
                s["duration_seconds"] = max(3, int(round(s["duration_seconds"] * ratio)))

        return normalized_scenes

    @classmethod
    def _heuristic_scene_splitter(cls, script: str, target_duration: int) -> List[Dict[str, Any]]:
        """Splits script into sentences/paragraphs and assigns realistic durations."""
        # Split on sentence terminals
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", script) if s.strip()]
        if not sentences:
            sentences = [script.strip()]

        total_words = sum(len(s.split()) for s in sentences) or 1
        num_scenes = len(sentences)
        
        # Merge very short sentences if too many
        if num_scenes > 8:
            merged = []
            cur = ""
            for s in sentences:
                cur = f"{cur} {s}".strip()
                if len(cur.split()) >= 12:
                    merged.append(cur)
                    cur = ""
            if cur:
                if merged:
                    merged[-1] += f" {cur}"
                else:
                    merged.append(cur)
            sentences = merged

        scenes = []
        for i, sentence in enumerate(sentences, 1):
            words = len(sentence.split())
            dur = max(4, int(round((words / total_words) * target_duration)))
            scenes.append({
                "scene_number": i,
                "narration": sentence,
                "visual_description": f"Cinematic visual demonstrating {sentence[:60]}",
                "search_keywords": " ".join([w.lower() for w in re.findall(r"\b[A-Za-z]{4,}\b", sentence)[:4]]),
                "duration_seconds": dur
            })

        return scenes


if __name__ == "__main__":
    sample_script = (
        "What if Artificial Intelligence could completely change the way you learn? "
        "Today, AI is helping students learn faster and in a more personalized way. "
        "AI-powered tools provide instant feedback and help understand difficult topics. "
        "The future of education is becoming smarter every day. "
        "Are you ready to learn with AI? Follow for more!"
    )
    scenes = SceneAgent.extract_scenes(sample_script, 30)
    print("Scenes count:", len(scenes))
    print(json.dumps(scenes, indent=2))
