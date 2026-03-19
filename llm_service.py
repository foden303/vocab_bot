import json
import re
from openai import AsyncOpenAI
from google import genai
from config import config


class LLMService:
    def __init__(self):
        self.openai_client = AsyncOpenAI(
            api_key=config.OPENAI_API_KEY
        ) if config.OPENAI_API_KEY else None

        self.gemini_client = genai.Client(
            api_key=config.GEMINI_API_KEY
        ) if config.GEMINI_API_KEY else None

        self.openrouter_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY,
        ) if config.OPENROUTER_API_KEY else None

        self.ollama_client = AsyncOpenAI(
            base_url=config.OLLAMA_API_BASE,
            api_key="none"
        )
        self.lmstudio_client = AsyncOpenAI(
            base_url=config.LMSTUDIO_API_BASE,
            api_key="none"
        )

    def get_vocab_prompt(self, word: str) -> str:
        return f"""Generate comprehensive vocabulary information for the word: {word} based on Oxford Learner's Dictionary standards.

CRITICAL RULE FOR SPELLING:
If the input word "{word}" is misspelled, identify the most likely intended English word and provide information for that corrected word.

Follow these specific rules:
1. PRONUNCIATION: Use only US Phonetic Alphabet. Format must be exactly /.../ (e.g., /əˈbiliti/). Do not include "US:" prefix.
2. DEFINITIONS: "meaning" must align with Oxford Learner's Dictionary definitions. "meaning_vn" is the concise Vietnamese equivalent.
3. EXAMPLES: Provide one high-quality sentence followed by its Vietnamese translation in parentheses.
4. FORMATTING: For "patterns", "synonyms", "antonyms", "related_words", "paraphrase", and "collocation", ALWAYS include the Vietnamese meaning in parentheses: "word (nghĩa)".
5. OUTPUT: Return ONLY a valid JSON object. No preamble, no markdown code blocks.

{{
 "word": "Corrected word if misspelled",
 "category": ["noun/verb/adj..."],
 "pronunciation": "/.../",
 "meaning_vn": "Nghĩa tiếng Việt ngắn gọn",
 "meaning": "English definition based on Oxford",
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

    def get_vocab_prompt_v2(self, word: str) -> str:
        return f"""Generate comprehensive vocabulary information for the word: {word}

CRITICAL RULE FOR SPELLING:
If the input word "{word}" is misspelled or has a typo, identify the most likely intended English word and provide the vocabulary information for that corrected word instead.

Follow these specific rules:
1. Pronunciation: Use only US Phonetic Alphabet. Format must be exactly /.../ (e.g., /əˈbiliti/). Do not include "US:" prefix.
2. Provide the main "meaning_vn" as the primary Vietnamese definition.
3. For "example", provide a high-quality English sentence followed by its Vietnamese translation in parentheses.
4. For "patterns", "synonyms", "antonyms", "related_words", "paraphrase", and "collocation", ALWAYS include the Vietnamese meaning in parentheses next to every English term (e.g., "disaster (thảm họa)").
5. Ensure the JSON is valid and contains no preamble or markdown code blocks.

Return ONLY this JSON structure:

{{
 "word": "Corrected word if misspelled",
 "category": ["noun/verb/adj..."],
 "pronunciation": "/.../",
 "meaning_vn": "Nghĩa tiếng việt ngắn gọn, dễ hiểu",
 "meaning": "English definition based on Oxford",
 "example": "English sentence. (Dịch tiếng Việt)",
 "level": "A1-C2",
 "topic": [],
 "patterns": "pattern 1 (nghĩa)\\npattern 2 (nghĩa)",
 "synonyms": "synonym 1 (nghĩa)\\nsynonym 2 (nghĩa)",
 "antonyms": "antonym 1 (nghĩa)\\nantonym 2 (nghĩa)",
 "related_words": "word 1 (nghĩa)\\nword 2 (nghĩa)",
 "paraphrase": "phrase 1 (nghĩa)\\nphrase 2 (nghĩa)",
 "collocation": "collo 1 (nghĩa)\\ncollo 2 (nghĩa)"
}}
"""

    async def call_llm(self, word: str, model_key: str = None) -> dict:
        model_key = model_key or config.DEFAULT_MODEL
        cfg = config.MODELS_CONFIG.get(
            model_key, config.MODELS_CONFIG[config.DEFAULT_MODEL])
        prompt = self.get_vocab_prompt_v2(word)

        text = ""
        if cfg["provider"] == "openai":
            if not self.openai_client:
                raise Exception("OpenAI API Key not configured")
            response = await self.openai_client.chat.completions.create(
                model=cfg["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            text = response.choices[0].message.content

        elif cfg["provider"] == "gemini":
            if not self.gemini_client:
                raise Exception("Gemini API Key not configured")
            response = await self.gemini_client.aio.models.generate_content(
                model=cfg["model"],
                contents=prompt
            )
            text = response.text

        elif cfg["provider"] == "openrouter":
            if not config.OPENROUTER_API_KEY:
                raise Exception("OpenRouter API Key not configured")
            response = await self.openrouter_client.chat.completions.create(
                model=cfg["model"],
                messages=[{"role": "user", "content": prompt}],
            )
            text = response.choices[0].message.content

        elif cfg["provider"] == "ollama":
            response = await self.ollama_client.chat.completions.create(
                model=cfg["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            text = response.choices[0].message.content

        elif cfg["provider"] == "lmstudio":
            response = await self.lmstudio_client.chat.completions.create(
                model=cfg["model"],
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            text = response.choices[0].message.content

        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"```json\n|```", "", text).strip()

        return json.loads(text)


llm_service = LLMService()
