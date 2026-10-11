"""
Quality Control Agent and File Checker.
Implements Module 4 (Nodes 20, 21, 22) of the Agentic AI Video Creation System.
Evaluates completeness, file validity, and returns structured PASS / FAIL analysis.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

from .config import Config
from .script_generator import LLMClient, clean_json_string

logger = logging.getLogger(__name__)

class QualityControlAgent:
    """Evaluates project outputs against strict completeness criteria."""

    SYSTEM_PROMPT = "You are a Quality Control AI Agent."

    @classmethod
    def check_files(cls, project_state: Dict[str, Any]) -> Dict[str, bool]:
        """
        Implements Node 20: Check whether all required files exist on disk.
        """
        script_exists = bool(project_state.get("script") and len(project_state["script"].strip()) > 20)
        
        scenes = project_state.get("scenes", [])
        scenes_exist = bool(scenes and isinstance(scenes, list) and len(scenes) >= 1)
        
        # Check visuals
        visuals_exist = False
        if scenes_exist:
            v_files = [s.get("visual_file") for s in scenes if s.get("visual_file")]
            if len(v_files) == len(scenes) and all(os.path.exists(f) and os.path.getsize(f) > 500 for f in v_files):
                visuals_exist = True

        # Check voiceover
        audio_path = project_state.get("audio_path")
        audio_exists = bool(audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 1000)

        # Check captions
        captions_path = project_state.get("subtitles_path")
        captions_exist = bool(captions_path and os.path.exists(captions_path) and os.path.getsize(captions_path) > 20)

        # Check video
        video_path = project_state.get("video_path")
        video_exists = bool(video_path and os.path.exists(video_path) and os.path.getsize(video_path) > 10000)

        return {
            "script_exists": script_exists,
            "scenes_exist": scenes_exist,
            "visuals_exist": visuals_exist,
            "voiceover_exists": audio_exists,
            "captions_exist": captions_exist,
            "final_video_exists": video_exists
        }

    @classmethod
    def evaluate(cls, project_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Implements Node 21: Quality Agent evaluation.
        Returns { "status": "PASS" | "FAIL", "quality_score": 95, "issues": [...] }
        """
        file_checks = cls.check_files(project_state)
        issues: List[str] = []

        if not file_checks["script_exists"]:
            issues.append("Script is missing or too short.")
        if not file_checks["scenes_exist"]:
            issues.append("Scene breakdown is missing.")
        if not file_checks["visuals_exist"]:
            issues.append("One or more scene visual files are missing or unreadable.")
        if not file_checks["voiceover_exists"]:
            issues.append("Voiceover audio file is missing or corrupted.")
        if not file_checks["captions_exist"]:
            issues.append("Subtitles SRT file is missing or empty.")
        if not file_checks["final_video_exists"]:
            issues.append("Final MP4 video was not created.")

        # If files exist, run LLM Quality Evaluation if available
        if not issues:
            llm_prompt = f"""You are a Quality Control AI Agent.
Check the following project output.

Evaluate:
1. Is the script complete? Yes
2. Are all scenes available? Yes ({len(project_state.get('scenes', []))} scenes)
3. Are visuals available? Yes
4. Is voiceover available? Yes ({project_state.get('audio_path')})
5. Are captions available? Yes ({project_state.get('subtitles_path')})
6. Was the final video created? Yes ({project_state.get('video_path')})

Return JSON:
{{
  "status": "PASS or FAIL",
  "quality_score": 0,
  "issues": []
}}"""
            raw = LLMClient.generate(llm_prompt, cls.SYSTEM_PROMPT)
            if raw:
                try:
                    cleaned = clean_json_string(raw)
                    parsed = json.loads(cleaned)
                    if "status" in parsed:
                        return parsed
                except Exception:
                    pass

            return {
                "status": "PASS",
                "quality_score": 96,
                "issues": [],
                "details": file_checks
            }

        # If issues found, score drops according to issues
        penalty = len(issues) * 20
        quality_score = max(0, 100 - penalty)
        return {
            "status": "FAIL",
            "quality_score": quality_score,
            "issues": issues,
            "details": file_checks
        }


if __name__ == "__main__":
    dummy_state = {
        "script": "Artificial intelligence is changing the world.",
        "scenes": [{"scene_number": 1}],
        "audio_path": "/fake/path.mp3",
        "video_path": None
    }
    result = QualityControlAgent.evaluate(dummy_state)
    print("Quality result:", json.dumps(result, indent=2))
