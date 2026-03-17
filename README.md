# Vocab to Notion Bot

A Telegram bot that generates comprehensive vocabulary information using LLMs (Gemini, OpenAI, OpenRouter) and pushes it to a Notion database.

## Features
- Modular architecture with centrally managed config.
- Multiple LLM providers supported.
- Comprehensive vocabulary data generation including Vietnamese meanings, examples, synonyms, antonyms, etc.
- Dockerized for easy deployment.

## Configuration
Create a `.env` file in the root directory with the following variables:
```env
BOT_TOKEN=your_telegram_bot_token
NOTION_TOKEN=your_notion_api_token
NOTION_DATABASE_ID=your_notion_database_id
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

## Running the Bot

### Locally
1. Install dependencies: `pip install -r requirements.txt`
2. Run the bot: `python bot.py`

### Using Docker
1. Build the image: `docker build -t vocab-bot .`
2. Run the container: `docker run --env-file .env vocab-bot`

### Using Docker Compose
1. Run: `docker-compose up -d`

## Commands
- `/add <word>`: Generate and add a word to Notion.
- `/setmodel`: Switch between LLM models.
- `/info`: Show current configuration.
- `/help`: Display help message.
