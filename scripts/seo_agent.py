"""
SEO Agent for Social Media Content Marketing.
Implements Module 5 (Node 23) of the Agentic AI Video Creation System.
Generates tailored YouTube Shorts and Instagram Reels metadata.
"""

import json
import logging
import re
from typing import Dict, Any

from .script_generator import LLMClient, clean_json_string

logger = logging.getLogger(__name__)

class SEOAgent:
    """Generates platform-specific SEO metadata for YouTube Shorts and Instagram Reels."""

    SYSTEM_PROMPT = "You are an expert Social Media SEO and Content Marketing Agent."

    @classmethod
    def generate_seo_content(cls, topic: str, script: str) -> Dict[str, Any]:
        """Generates titles, descriptions, tags, and hashtags for YouTube and Instagram."""
        logger.info(f"SEOAgent generating content for topic: '{topic}'")

        llm_prompt = f"""You are an expert Social Media SEO and Content Marketing Agent.

Analyze the following video topic and script.

Generate optimized content for YouTube Shorts and Instagram Reels.

Create:
1. SEO-friendly YouTube Title
2. YouTube Description
3. YouTube Keywords
4. YouTube Tags
5. Instagram Caption
6. Instagram Hashtags
7. Call to Action

Requirements:
- Make the title attractive and searchable.
- Use relevant keywords naturally.
- Do not use keyword stuffing.
- Make the caption engaging.
- Create relevant hashtags.
- Optimize the content separately for YouTube and Instagram.

TOPIC:
{topic}

VIDEO SCRIPT:
{script}

Return ONLY valid JSON in this exact structure:
{{
  "youtube_title": "How Artificial Intelligence is Transforming Education | AI in Education",
  "youtube_description": "Discover how Artificial Intelligence is transforming education and helping students learn in smarter and more personalized ways.",
  "youtube_keywords": [
    "Artificial Intelligence",
    "AI in Education",
    "Future of Education",
    "Technology"
  ],
  "youtube_tags": [
    "AI",
    "Artificial Intelligence",
    "Education",
    "Technology"
  ],
  "instagram_caption": "Artificial Intelligence is changing the future of education! 🚀📚",
  "instagram_hashtags": [
    "#AI",
    "#ArtificialIntelligence",
    "#Education",
    "#Technology",
    "#FutureOfEducation"
  ],
  "call_to_action": "Follow for more AI and technology content!"
}}"""

        raw = LLMClient.generate(llm_prompt, cls.SYSTEM_PROMPT)
        seo_data = None

        if raw:
            try:
                cleaned = clean_json_string(raw)
                seo_data = json.loads(cleaned)
            except Exception as e:
                logger.warning(f"Failed parsing LLM SEO output ({e}). Falling back to algorithmic generator.")

        if not seo_data or not isinstance(seo_data, dict):
            # Deterministic, high-yield SEO generator
            words = [w for w in re.findall(r"\b[A-Za-z0-9]{3,}\b", topic) if w.lower() not in ("the", "and", "for", "with")]
            clean_title = f"{topic.strip()} | Revealed in 60s"[:90]
            
            keywords = [topic, "Education", "Technology", "Future Tech", "AI Revolution", "Tutorial"]
            tags = list({w.capitalize() for w in words} | {"AI", "TechTrends", "Innovation"})[:10]
            hashtags = [f"#{re.sub(r'[^A-Za-z0-9]', '', t)}" for t in tags[:6]]

            seo_data = {
                "youtube_title": clean_title,
                "youtube_description": (
                    f"Explore the truth about {topic}! In this video, we break down everything you need to know "
                    "about modern advancements and what it means for you. Watch till the end for essential takeaways!"
                ),
                "youtube_keywords": keywords,
                "youtube_tags": tags,
                "instagram_caption": f"Here is how {topic} is redefining everything! 🚀💡 Double tap if you learned something new today.",
                "instagram_hashtags": hashtags,
                "call_to_action": "Follow and subscribe for more daily AI insights!"
            }

        return seo_data


if __name__ == "__main__":
    test_topic = "Artificial Intelligence in Education"
    test_script = "What if AI could completely change the way you learn? Discover the future today."
    res = SEOAgent.generate_seo_content(test_topic, test_script)
    print("SEO output:\n", json.dumps(res, indent=2))
