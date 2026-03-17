import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    NOTION_TOKEN = os.getenv("NOTION_TOKEN")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    MODELS_CONFIG = {
        "gemini": {"name": "Gemini 2.5 Flash", "provider": "gemini", "model": "gemini-2.5-flash"},
        "openai": {"name": "GPT-3.5 Turbo", "provider": "openai", "model": "gpt-3.5-turbo"},
        "openrouter": {"name": "OpenRouter (Claude 3 Haiku)", "provider": "openrouter", "model": "anthropic/claude-3-haiku"}
    }
    DEFAULT_MODEL = "gemini"

config = Config()
