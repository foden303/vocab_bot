import os
import json
import re
import requests
import warnings
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from openai import OpenAI
from google import genai
from dotenv import load_dotenv

# --- SUPPRESS WARNINGS ---
warnings.filterwarnings("ignore", category=FutureWarning,
                        module="google.api_core")

# --- LOAD ENV ---
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- GLOBAL STATE ---
# Default model settings
USER_MODELS = {}  # chat_id -> model_info

MODELS_CONFIG = {
    "gemini": {"name": "Gemini 2.5 Flash", "provider": "gemini", "model": "gemini-2.5-flash"},
    "openai": {"name": "GPT-3.5 Turbo", "provider": "openai", "model": "gpt-3.5-turbo"},
    "openrouter": {"name": "OpenRouter (Claude 3 Haiku)", "provider": "openrouter", "model": "anthropic/claude-3-haiku"}
}

DEFAULT_MODEL = "gemini"

# --- INIT ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Pre-init clients
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
gemini_client = genai.Client(
    api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
) if OPENROUTER_API_KEY else None


def get_vocab_prompt(word: str) -> str:
    return f"""
Generate vocabulary information for the word:

Word: {word}

Return ONLY a JSON object in this format (no preamble, no markdown blocks):

{{
 "word":"",
 "category":"",
 "pronunciation":"",
 "meaning":"",
 "example":"",
 "level":"",
 "topic":[],
 "patterns":[],
 "synonyms":[],
 "antonyms":[],
 "related_words":[],
 "paraphrase":"",
 "collocation":[]
}}
"""


def call_llm(word: str, chat_id: int) -> dict:
    model_key = USER_MODELS.get(chat_id, DEFAULT_MODEL)
    config = MODELS_CONFIG.get(model_key, MODELS_CONFIG[DEFAULT_MODEL])
    prompt = get_vocab_prompt(word)

    text = ""
    if config["provider"] == "openai":
        if not openai_client:
            raise Exception("OpenAI API Key not configured")
        response = openai_client.chat.completions.create(
            model=config["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        text = response.choices[0].message.content

    elif config["provider"] == "gemini":
        if not gemini_client:
            raise Exception("Gemini API Key not configured")
        response = gemini_client.models.generate_content(
            model=config["model"],
            contents=prompt
        )
        text = response.text

    elif config["provider"] == "openrouter":
        if not OPENROUTER_API_KEY:
            raise Exception("OpenRouter API Key not configured")
        response = openrouter_client.chat.completions.create(
            model=config["model"],
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.choices[0].message.content

    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"```json\n|```", "", text).strip()

    return json.loads(text)


def push_to_notion(vocab: dict):
    """
    Push JSON vocab vào Notion database
    """
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    # Helper to clean strings and lists
    def to_str(val):
        if isinstance(val, list):
            return ", ".join([str(v) for v in val])
        return str(val) if val else ""

    data = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Word": {"title": [{"text": {"content": vocab.get("word", "")}}]},
            "Category": {"select": {"name": vocab.get("category") or "Uncategorized"}},
            "Pronunciation": {"rich_text": [{"text": {"content": to_str(vocab.get("pronunciation", ""))}}]},
            "Meaning": {"rich_text": [{"text": {"content": to_str(vocab.get("meaning", ""))}}]},
            "Example": {"rich_text": [{"text": {"content": to_str(vocab.get("example", ""))}}]},
            "Level": {"select": {"name": vocab.get("level") or "Unknown"}},
            "Topic": {"multi_select": [{"name": str(t)} for t in vocab.get("topic", []) if t]},
            "Word Patterns": {"rich_text": [{"text": {"content": to_str(vocab.get("patterns", []))}}]},
            "Synonyms": {"rich_text": [{"text": {"content": to_str(vocab.get("synonyms", []))}}]},
            "Antonyms": {"rich_text": [{"text": {"content": to_str(vocab.get("antonyms", []))}}]},
            "Related Words": {"rich_text": [{"text": {"content": to_str(vocab.get("related_words", []))}}]},
            "Paraphrase": {"rich_text": [{"text": {"content": to_str(vocab.get("paraphrase", ""))}}]},
            "Collocation": {"rich_text": [{"text": {"content": to_str(vocab.get("collocation", []))}}]},
        }
    }

    r = requests.post(url, headers=headers, json=data)
    if r.status_code != 200:
        print(f"Error payload: {json.dumps(data, indent=2)}")
        print(f"Response: {r.text}")
    r.raise_for_status()


@dp.message_handler(commands=['start', 'help'])
async def help_handler(message: types.Message):
    help_text = """
🚀 **Vocab to Notion Bot**

**Commands:**
/add_vocab <word> - Generate and add word to Notion
/setmodel - Switch between LLM models
/info - Show current settings
/help - Show this message

**Examples:**
`/add_vocab serendipity`
    """
    await message.reply(help_text, parse_mode="Markdown")


@dp.message_handler(commands=['info'])
async def info_handler(message: types.Message):
    model_key = USER_MODELS.get(message.chat.id, DEFAULT_MODEL)
    config = MODELS_CONFIG.get(model_key)

    info_text = f"""
🛠 **Current Configuration**
- **Model:** {config['name']}
- **Provider:** {config['provider']}
- **Database ID:** `{DATABASE_ID[:6]}...{DATABASE_ID[-4:]}`
    """
    await message.reply(info_text, parse_mode="Markdown")


@dp.message_handler(commands=['setmodel'])
async def set_model_handler(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for key, cfg in MODELS_CONFIG.items():
        button = types.InlineKeyboardButton(
            text=cfg['name'], callback_data=f"model_{key}")
        keyboard.add(button)

    await message.reply("Select the LLM model you want to use:", reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data.startswith('model_'))
async def process_model_callback(callback_query: types.CallbackQuery):
    model_key = callback_query.data.split('_')[1]
    USER_MODELS[callback_query.message.chat.id] = model_key

    await bot.answer_callback_query(callback_query.id)
    await bot.edit_message_text(
        text=f"✅ Model switched to: **{MODELS_CONFIG[model_key]['name']}**",
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        parse_mode="Markdown"
    )


@dp.message_handler(commands=['add'])
async def add_vocab_handler(message: types.Message):
    args = message.get_args()
    if not args:
        await message.reply("Usage: /add <word>")
        return

    word = args.strip()
    processing_msg = await message.reply(f"⏳ Generating vocab for: **{word}**...")

    try:
        vocab = call_llm(word, message.chat.id)
        print("vocab", vocab)
        push_to_notion(vocab)
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            text=f"✅ Added **{word}** to Notion vocab database.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            text=f"❌ Error: {str(e)}"
        )


if __name__ == "__main__":
    print("Bot is starting...")
    executor.start_polling(dp, skip_updates=True)
