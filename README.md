# Vocab to Notion Bot

A Telegram bot that generates comprehensive vocabulary information using LLMs (Gemini, OpenAI, OpenRouter) and pushes it to a Notion database.

## Features
- Modular architecture with centrally managed config.
- Multiple LLM providers supported (Gemini, OpenAI, OpenRouter).
- Comprehensive vocabulary data generation including meanings, examples, synonyms, antonyms, etc.
- Dockerized for easy deployment.

---

## Setup Guide

### 1. Obtain Credentials

#### Telegram Bot Token
- Open Telegram and search for `@BotFather`.
- Send the `/newbot` command and follow the instructions to name your bot.
- Once created, `@BotFather` will provide an **API Token**. This is your `BOT_TOKEN`.

#### Notion Token (Internal Integration Token)
- Go to [Notion My Integrations](https://www.notion.so/my-integrations).
- Click **+ New integration**.
- Name your integration, select your workspace, and click **Submit**.
- In the **Secrets** tab, click **Show** and **Copy** the `Internal Integration Token`. This is your `NOTION_TOKEN`.

#### Notion Database ID
- Open your Vocab database in your browser (or create a new one).
- Click the **Share** button at the top right.
- Share the database with the integration you just created (Click **Invite** and select your integration name).
- Copy the database URL. it looks like this: `https://www.notion.so/workspace_name/DATABASE_ID?v=...`
- The alphanumeric string between the last `/` and the `?` is your `NOTION_DATABASE_ID`.
- **Note**: Ensure you have added the integration to the database connections: Click `...` (3 dots) top right -> **Add connections** -> Select your integration.

### 2. Configuration
Create a `.env` file in the root directory and add your credentials:
```env
BOT_TOKEN=your_telegram_bot_token
NOTION_TOKEN=your_notion_api_token
NOTION_DATABASE_ID=your_notion_database_id
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

---

## Running the Bot

### Using Docker Compose (Recommended)
1. Run: `docker-compose up -d --build`

### Using Docker
1. Build the image: `docker build -t vocab-bot .`
2. Run the container: `docker run --env-file .env vocab-bot`

### Running Locally
1. Install dependencies: `pip install -r requirements.txt`
2. Run the bot: `python bot.py`

---

## Commands
- `/add <word>`: Generate and add a word to Notion.
- `/setmodel`: Switch between LLM models.
- `/info`: Show current configuration.
- `/help`: Display help message.
