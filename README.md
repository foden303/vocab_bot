# Vocab to Notion Bot

A Telegram bot that generates comprehensive vocabulary information using LLMs (Gemini, OpenAI, OpenRouter) and pushes it to a Notion database, with advanced synchronization to Anki.

## 🚀 Key Features
- **Smart Generation**: Generates comprehensive vocabulary data including meanings, examples, synonyms, antonyms, collocations, etc.
- **Multiple LLM Providers**: Support for Gemini, OpenAI, and OpenRouter.
- **Notion Integration**: Automatically saves entries to a structured database.
- **Anki Synchronization**: Push your unsynced words to Anki with beautiful custom templates.
- **Oxford Audio Downloader**: Automatically fetches US English pronunciation audio files directly from Oxford Learner's Dictionary.
- **Audio Fallback**: Intelligently uses local `.mp3` files or falls back to Anki's native TTS.
- **Dockerized**: Easy deployment with Docker and Docker Compose.

---

## Setup Guide

### 1. Obtain Credentials

#### Telegram Bot Token
- Open Telegram and search for `@BotFather`.
- Send the `/newbot` command and provide a name.
- Copy the **API Token** provided.

#### Notion Token & Database ID
- Create an internal integration at [Notion My Integrations](https://www.notion.so/my-integrations).
- Share your database with the integration.
- Database ID is the alphanumeric string in the URL: `https://www.notion.so/.../DATABASE_ID?v=...`
- **Important**: Your Notion database **must** have a checkbox property named exactly `Synced to Anki`.

#### Anki Setup
- Install the **AnkiConnect** add-on (ID: `2055492159`).
- Ensure Anki is running whenever you use the `/sync` command.

### 2. Configuration
Create a `.env` file in the root directory:
```env
# Bot Keys
BOT_TOKEN=your_telegram_bot_token
NOTION_TOKEN=your_notion_api_token
NOTION_DB_WORD_ID=your_NOTION_DB_WORD_ID
NOTION_DB_COLLOCATION_ID=your_NOTION_DB_COLLOCATION_ID

# LLM Keys
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# Anki Config (Optional)
ANKI_CONNECT_URL=http://localhost:8765
ANKI_DECK_NAME=VocabBot
ANKI_MODEL_NAME=Basic

# Audio Config
SOUNDS_DIR=./sounds
```

---

## Running the Bot

### Using Docker Compose (Recommended)
1. Run: `docker-compose up -d --build`
2. **Volumes**: The `sounds/` directory is mapped as a volume, allowing you to manage audio files from your host machine.

### Running Locally
1. Install dependencies: `pip install -r requirements.txt`
2. Run the bot: `python bot.py`

---

## Commands
- `/add <word>`: Generate and add a word to Notion.
- `/getaudio`: Download US pronunciation mp3s from Oxford for unsynced words.
- `/sync`: Push unsynced words and audio from Notion to Anki.
- `/setmodel`: Switch between LLM models.
- `/info`: Show current configuration.
- `/help`: Display help message.

---

## 🎨 Personalization
You can customize the Anki card design by editing the HTML/CSS files in the `templates/` directory:
- `front.html`: Front side logic (Word, Pronunciation, Audio button).
- `back.html`: Back side details (Meanings, Examples, Metadata).
