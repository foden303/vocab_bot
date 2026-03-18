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
    OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://localhost:11434/v1")
    LMSTUDIO_API_BASE = os.getenv(
        "LMSTUDIO_API_BASE", "http://localhost:1234/v1")

    MODELS_CONFIG = {
        "gemini": {
            "name": "Gemini 2.5 Flash",
            "provider": "gemini",
            "model": "gemini-2.5-flash"
        },

        "openrouter_fast": {
            "name": "OpenRouter Fast (Step 3.5)",
            "provider": "openrouter",
            "model": "stepfun/step-3.5-flash:free"
        },

        "openrouter_smart": {
            "name": "OpenRouter Smart (Nemotron)",
            "provider": "openrouter",
            "model": "nvidia/nemotron-3-super-120b-a12b:free"
        },

        "openrouter_creative": {
            "name": "OpenRouter Creative (Trinity)",
            "provider": "openrouter",
            "model": "arcee-ai/trinity-large-preview:free"
        },

        "openrouter_auto": {
            "name": "OpenRouter Auto Free",
            "provider": "openrouter",
            "model": "openrouter/free"
        },

        "ollama": {
            "name": "Ollama (Llama 3)",
            "provider": "ollama",
            "model": "llama3"
        },

        "lmstudio": {
            "name": "LM Studio (Local)",
            "provider": "lmstudio",
            "model": "local-model"
        }
    }
    DEFAULT_MODEL = "openrouter_fast"

    # Anki Configuration
    ANKI_CONNECT_URL = os.getenv("ANKI_CONNECT_URL", "http://localhost:8765")
    ANKI_DECK_NAME = os.getenv("ANKI_DECK_NAME", "VocabBot")
    ANKI_MODEL_NAME = os.getenv("ANKI_MODEL_NAME", "Basic")
    SOUNDS_DIR = os.getenv("SOUNDS_DIR", os.path.join(
        os.path.dirname(__file__), "sounds"))

    # Ensure directories exist
    os.makedirs(SOUNDS_DIR, exist_ok=True)


config = Config()
