import warnings
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

from config import config
from llm_service import llm_service
from notion_service import notion_service

# --- SUPPRESS WARNINGS ---
warnings.filterwarnings("ignore", category=FutureWarning, module="google.api_core")

# --- GLOBAL STATE ---
USER_MODELS = {}  # chat_id -> model_key

# --- INIT ---
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start', 'help'])
async def help_handler(message: types.Message):
    help_text = """
🚀 **Vocab to Notion Bot**

**Commands:**
/add <word> - Generate and add word to Notion
/setmodel - Switch between LLM models
/info - Show current settings
/help - Show this message

**Examples:**
`/add hello`
    """
    await message.reply(help_text, parse_mode="Markdown")

@dp.message_handler(commands=['info'])
async def info_handler(message: types.Message):
    model_key = USER_MODELS.get(message.chat.id, config.DEFAULT_MODEL)
    cfg = config.MODELS_CONFIG.get(model_key)

    # Obfuscate Database ID for security
    db_id = config.NOTION_DATABASE_ID or "NOT_FOUND"
    obfuscated_id = f"{db_id[:6]}...{db_id[-4:]}" if len(db_id) > 10 else db_id

    info_text = f"""
🛠 **Current Configuration**
- **Model:** {cfg['name']}
- **Provider:** {cfg['provider']}
- **Database ID:** `{obfuscated_id}`
    """
    await message.reply(info_text, parse_mode="Markdown")

@dp.message_handler(commands=['setmodel'])
async def set_model_handler(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    for key, cfg in config.MODELS_CONFIG.items():
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
        text=f"✅ Model switched to: **{config.MODELS_CONFIG[model_key]['name']}**",
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
        model_key = USER_MODELS.get(message.chat.id, config.DEFAULT_MODEL)
        vocab = llm_service.call_llm(word, model_key)
        notion_service.push_to_notion(vocab)
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
