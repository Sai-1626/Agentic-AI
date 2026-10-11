"""
Planning Agent and Script Generation Agent.
Implements Module 2 of the Agentic AI Video Creation System.
"""

import json
import logging
import re
from typing import Dict, Any, Optional
import requests

from .config import Config

logger = logging.getLogger(__name__)

class LLMClient:
    """Handles communication with Ollama, OpenAI, or smart local fallback."""

    @staticmethod
    def call_ollama(prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Calls the local Ollama API."""
        url = f"{Config.OLLAMA_BASE_URL}/api/generate"
        payload = {
            "model": Config.LLM_MODEL,
            "prompt": prompt,
            "system": system_prompt or "",
            "stream": False,
            "options": {
                "temperature": 0.7
            }
        }
        try:
            response = requests.post(url, json=payload, timeout=25)
            if response.status_code == 200:
                data = response.json()
                return data.get("response", "").strip()
            logger.warning(f"Ollama returned HTTP {response.status_code}: {response.text}")
        except Exception as e:
            logger.info(f"Ollama connection unavailable ({e}), trying alternatives...")
        return None

    @staticmethod
    def call_openai(prompt: str, system_prompt: Optional[str] = None) -> Optional[str]:
        """Calls OpenAI API if key is present."""
        if not Config.OPENAI_API_KEY:
            return None
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {Config.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        payload = {
            "model": Config.OPENAI_MODEL,
            "messages": messages,
            "temperature": 0.7
        }
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.warning(f"OpenAI call failed: {e}")
        return None

    @classmethod
    def generate(cls, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Attempts Ollama -> OpenAI -> Fallback."""
        # 1. Try Ollama
        res = cls.call_ollama(prompt, system_prompt)
        if res:
            return res
        
        # 2. Try OpenAI
        res = cls.call_openai(prompt, system_prompt)
        if res:
            return res

        # 3. Fallback heuristic
        return ""


def clean_json_string(text: str) -> str:
    """Extracts JSON substring from LLM response markdown or text."""
    text = text.strip()
    # Check for markdown code fences
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence_match:
        text = fence_match.group(1).strip()
    # Find first '{' or '[' and last '}' or ']'
    start_brace = text.find("{")
    end_brace = text.rfind("}")
    if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
        return text[start_brace:end_brace+1]
    return text


class PlanningAgent:
    """Analyzes user prompt and generates structured video content plan."""

    SYSTEM_PROMPT = "You are an AI Social Media Content Planning Agent."

    @classmethod
    def plan(cls, user_prompt: str) -> Dict[str, Any]:
        """Generate structured plan for the video."""
        logger.info(f"PlanningAgent executing for prompt: '{user_prompt}'")
        
        llm_prompt = f"""You are an AI Social Media Content Planning Agent.

Analyze the user's request and create a complete video plan.

Determine:
1. Topic
2. Target Audience
3. Platform
4. Video Duration (in seconds)
5. Tone
6. Content Style
7. Main Message
8. Hook Strategy

If information is missing, make intelligent decisions automatically.

Return ONLY valid JSON.

User Request:
{user_prompt}

Example Output:
{{
  "topic": "Artificial Intelligence in Education",
  "target_audience": "College Students",
  "platform": "Instagram Reels",
  "duration": 60,
  "tone": "Educational and Engaging",
  "style": "Short-form Video",
  "main_message": "AI is transforming education",
  "hook_strategy": "Ask an interesting question"
}}"""

        raw_response = LLMClient.generate(llm_prompt, cls.SYSTEM_PROMPT)
        plan_data = None

        if raw_response:
            try:
                cleaned = clean_json_string(raw_response)
                plan_data = json.loads(cleaned)
            except Exception as e:
                logger.warning(f"Could not parse LLM output as JSON ({e}). Falling back to heuristics.")

        if not plan_data or not isinstance(plan_data, dict):
            # Deterministic intelligent fallback extractor
            duration = 60
            dur_match = re.search(r"(\d+)[ -]?(?:sec|second)", user_prompt, re.I)
            if dur_match:
                duration = int(dur_match.group(1))

            platform = "Instagram Reels"
            if re.search(r"youtube|shorts", user_prompt, re.I):
                platform = "YouTube Shorts"
            elif re.search(r"tiktok", user_prompt, re.I):
                platform = "TikTok"

            # Clean topic
            topic = user_prompt
            for prefix in ["create a", "make a", "generate a", "video about", "reel about", "short about"]:
                topic = re.sub(rf"^.*?{prefix}\s*", "", topic, flags=re.I)
            topic = re.sub(r"\b(?:and publish.*|publish tomorrow.*)$", "", topic, flags=re.I).strip(" .")
            if not topic:
                topic = "Artificial Intelligence in Education"

            plan_data = {
                "topic": topic.title(),
                "target_audience": "Students and Tech Enthusiasts",
                "platform": platform,
                "duration": duration,
                "tone": "Educational and Engaging",
                "style": "Short-form Video",
                "main_message": f"How {topic} is shaping tomorrow's landscape",
                "hook_strategy": "Compelling question with immediate curiosity hook"
            }

        # Normalize duration
        if "duration" in plan_data:
            try:
                plan_data["duration"] = int(plan_data["duration"])
            except Exception:
                plan_data["duration"] = 60

        return plan_data


class ScriptAgent:
    """Converts content plan into a compelling short-form video narration script."""

    SYSTEM_PROMPT = "You are a professional short-form social media video script writer."

    @classmethod
    def generate_script(cls, content_plan: Dict[str, Any]) -> str:
        """Generates narration script based on the content plan."""
        logger.info(f"ScriptAgent generating script for topic: {content_plan.get('topic')}")

        plan_json = json.dumps(content_plan, indent=2)
        llm_prompt = f"""You are a professional short-form social media video script writer.

Create a complete script based on the following content plan.

Requirements:
- Start with a powerful hook.
- Use simple language.
- Make the content engaging.
- Keep the script suitable for the requested duration ({content_plan.get('duration', 60)} seconds, approximately {int(content_plan.get('duration', 60) * 2.3)} words).
- Include useful information.
- End with a strong conclusion.
- Include a call to action if appropriate.

Content Plan:
{plan_json}

Return ONLY the narration script. No intro, no scene headings, no stage directions, no quotes."""

        raw_script = LLMClient.generate(llm_prompt, cls.SYSTEM_PROMPT)
        if raw_script and len(raw_script.strip()) > 40:
            # Strip markdown quotes or headers
            cleaned = re.sub(r"^#.*$", "", raw_script, flags=re.M).strip()
            cleaned = cleaned.strip('"\'')
            return cleaned

        # Reliable high quality script fallback matching the topic
        topic = content_plan.get("topic", "Artificial Intelligence in Education")
        target = content_plan.get("target_audience", "College Students")
        main_msg = content_plan.get("main_message", "AI is transforming education")

        return (
            f"What if {topic} could completely change the way you learn?\n\n"
            f"Today, intelligent tools are helping {target.lower()} understand complex concepts faster than ever before. "
            f"With personalized tutors, automated study summaries, and instant problem-solving, education is entering an incredible new era. "
            f"{main_msg}. It empowers you to study smarter, retain knowledge longer, and master any skill on your own schedule.\n\n"
            f"The future of learning has officially arrived. Are you ready to upgrade your journey? Follow for more insights!"
        )


if __name__ == "__main__":
    test_prompt = "Create a 60-second Instagram Reel about Artificial Intelligence in Education"
    plan = PlanningAgent.plan(test_prompt)
    print("Plan:", json.dumps(plan, indent=2))
    script = ScriptAgent.generate_script(plan)
    print("\nScript:\n", script)
