import json
import re
from openai import OpenAI
from google import genai
from config import config

class LLMService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY) if config.OPENAI_API_KEY else None
        self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY) if config.GEMINI_API_KEY else None
        self.openrouter_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY,
        ) if config.OPENROUTER_API_KEY else None

    def get_vocab_prompt(self, word: str) -> str:
        return f"""Generate comprehensive vocabulary information for the word: {word}

Follow these specific rules:
1. Provide the main "meaning_vn" as the primary Vietnamese definition.
2. For "example", provide a high-quality English sentence followed by its Vietnamese translation in parentheses.
3. For "patterns", "synonyms", "antonyms", "related_words", and "collocation", ALWAYS include the Vietnamese meaning in parentheses next to every English term (e.g., "disaster (thảm họa)").
4. Ensure the JSON is valid and contains no preamble or markdown code blocks.

Return ONLY this JSON structure:

{{
 "word": "",
 "category": [],
 "pronunciation": "US: /.../ | UK: /.../",
 "meaning_vn": "Meaning in Vietnamese",
 "meaning": "Meaning in English",
 "example": "English sentence. (Dịch tiếng Việt)",
 "level": "A1-C2",
 "topic": [],
 "patterns": ["pattern (nghĩa)", "pattern 2 (nghĩa)"],
 "synonyms": ["synonym (nghĩa)", "synonym 2 (nghĩa)"],
 "antonyms": ["antonym (nghĩa)", "antonym 2 (nghĩa)"],
 "related_words": ["related word (nghĩa)", "related word 2 (nghĩa)"],
 "paraphrase": ["paraphrase 1 (nghĩa)", "paraphrase 2 (nghĩa)"],
 "collocation": ["collocation (nghĩa)", "collocation 2 (nghĩa)"]
}}
"""

    def call_llm(self, word: str, model_key: str = None) -> dict:
        model_key = model_key or config.DEFAULT_MODEL
        cfg = config.MODELS_CONFIG.get(model_key, config.MODELS_CONFIG[config.DEFAULT_MODEL])
        prompt = self.get_vocab_prompt(word)

        text = ""
        if cfg["provider"] == "openai":
            if not self.openai_client:
                raise Exception("OpenAI API Key not configured")
            response = self.openai_client.chat.completions.create(
                model=cfg["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            text = response.choices[0].message.content

        elif cfg["provider"] == "gemini":
            if not self.gemini_client:
                raise Exception("Gemini API Key not configured")
            response = self.gemini_client.models.generate_content(
                model=cfg["model"],
                contents=prompt
            )
            text = response.text

        elif cfg["provider"] == "openrouter":
            if not config.OPENROUTER_API_KEY:
                raise Exception("OpenRouter API Key not configured")
            response = self.openrouter_client.chat.completions.create(
                model=cfg["model"],
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.choices[0].message.content

        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"```json\n|```", "", text).strip()

        return json.loads(text)

llm_service = LLMService()
