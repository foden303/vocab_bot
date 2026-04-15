from constant import TYPE_WORD
from constant import TYPE_COLLOCATION
import asyncio
import warnings
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor

from config import config
from llm_service import llm_service
from notion_service import notion_service
from anki_service import anki_service
from audio_service import audio_service

# --- SUPPRESS WARNINGS ---
warnings.filterwarnings("ignore", category=FutureWarning,
                        module="google.api_core")

# --- GLOBAL STATE ---
USER_MODELS = {}  # chat_id -> model_key

# --- INIT ---
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def help_handler(message: types.Message):
    help_text = """
🚀 **Vocab to Notion & Anki Bot**

**Commands:**
/add <word> - Generate and add word to Notion
/collo <collocation> - Generate and add collocation to Notion
/getaudio - Download US pronunciations from Oxford
/sync - Sync unsynced vocab & audio to local Anki
/sync_collocation - Sync unsynced collocation & audio to local Anki
/sync_web - Sync local Anki to AnkiWeb
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
    db_id = config.NOTION_DB_WORD_ID or "NOT_FOUND"
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
    model_key = callback_query.data.split('_', 1)[1]
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
    processing_msg = await message.reply(f"⏳ Generating vocab for: **{word}**...", parse_mode="Markdown")

    try:
        model_key = USER_MODELS.get(message.chat.id, config.DEFAULT_MODEL)
        # Both calls are now async — event loop is free for other users
        vocab = await llm_service.call_llm(word, TYPE_WORD, model_key)
        await notion_service.push_to_notion_word_db(vocab)
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


@dp.message_handler(commands=['collo'])
async def add_collocation_handler(message: types.Message):
    args = message.get_args()
    if not args:
        await message.reply("Usage: /collo <collocation>")
        return

    collocation = args.strip()
    processing_msg = await message.reply(f"⏳ Generating collocation for: **{collocation}**...", parse_mode="Markdown")

    try:
        model_key = USER_MODELS.get(message.chat.id, config.DEFAULT_MODEL)
        # Both calls are now async — event loop is free for other users
        collocation_data = await llm_service.call_llm(collocation, TYPE_COLLOCATION, model_key)
        await notion_service.push_to_notion_collocation_db(collocation_data)
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            text=f"✅ Added **{collocation}** to Notion collocation database.",
            parse_mode="Markdown"
        )
    except Exception as e:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=processing_msg.message_id,
            text=f"❌ Error: {str(e)}"
        )


@dp.message_handler(commands=['sync'])
async def sync_handler(message: types.Message):
    # Check if Anki is open first
    if not anki_service.is_connected():
        await message.reply("⚠️ **Anki is not open!**\n\nPlease open Anki and make sure the AnkiConnect add-on is installed before syncing.", parse_mode="Markdown")
        return

    sync_msg = await message.reply("⏳ Fetching unsynced vocab from Notion...")

    try:
        unsynced_items = await notion_service.get_unsynced_vocab()

        if not unsynced_items:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=sync_msg.message_id,
                text="✅ All vocabulary items are already synced."
            )
            return

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sync_msg.message_id,
            text=f"🔄 Syncing {len(unsynced_items)} items to Anki..."
        )

        sync_results = anki_service.sync_to_anki(unsynced_items)

        success_ids = [res["page_id"]
                       for res in sync_results if res["success"]]
        failed_items = [res for res in sync_results if not res["success"]]

        if success_ids:
            await notion_service.mark_as_synced(
                notion_service.PROP_SYNCED_TO_ANKI, success_ids)

        report = f"✅ Synced **{len(success_ids)}** items to Anki."
        if failed_items:
            report += f"\n❌ Failed **{len(failed_items)}** items."

            # Show up to 10 failures to avoid Message_too_long
            max_show = 10
            for f in failed_items[:max_show]:
                # Find word name for error reporting
                word = next(
                    (item["word"] for item in unsynced_items if item["page_id"] == f["page_id"]), "Unknown")
                report += f"\n- {word}: {f['error']}"

            if len(failed_items) > max_show:
                report += f"\n... and {len(failed_items) - max_show} more."

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sync_msg.message_id,
            text=report,
            parse_mode="Markdown"
        )
    except Exception as e:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sync_msg.message_id,
            text=f"❌ Sync Error: {str(e)}"
        )


@dp.message_handler(commands=['sync_collocation'])
async def sync_collocation_handler(message: types.Message):
    # Check if Anki is open first
    if not anki_service.is_connected():
        await message.reply("⚠️ **Anki is not open!**\n\nPlease open Anki and make sure the AnkiConnect add-on is installed before syncing.", parse_mode="Markdown")
        return

    sync_msg = await message.reply("⏳ Fetching unsynced collocation from Notion...")

    try:
        unsynced_items = await notion_service.get_unsynced_collocation()

        if not unsynced_items:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=sync_msg.message_id,
                text="✅ All vocabulary items are already synced."
            )
            return

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sync_msg.message_id,
            text=f"🔄 Syncing {len(unsynced_items)} items to Anki..."
        )

        sync_results = anki_service.sync_to_anki(
            unsynced_items, TYPE_COLLOCATION)

        success_ids = [res["page_id"]
                       for res in sync_results if res["success"]]
        failed_items = [res for res in sync_results if not res["success"]]

        if success_ids:
            await notion_service.mark_as_synced(
                notion_service.PROP_SYNCED_TO_ANKI, success_ids)

        report = f"✅ Synced **{len(success_ids)}** items to Anki."
        if failed_items:
            report += f"\n❌ Failed **{len(failed_items)}** items."

            # Show up to 10 failures to avoid Message_too_long
            max_show = 10
            for f in failed_items[:max_show]:
                # Find word name for error reporting
                word = next(
                    (item["word"] for item in unsynced_items if item["page_id"] == f["page_id"]), "Unknown")
                report += f"\n- {word}: {f['error']}"

            if len(failed_items) > max_show:
                report += f"\n... and {len(failed_items) - max_show} more."

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sync_msg.message_id,
            text=report,
            parse_mode="Markdown"
        )
    except Exception as e:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sync_msg.message_id,
            text=f"❌ Sync Error: {str(e)}"
        )


@dp.message_handler(commands=['sync_web'])
async def sync_web_handler(message: types.Message):
    # Check if Anki is open first
    if not anki_service.is_connected():
        await message.reply("⚠️ **Anki is not open!**\n\nPlease open Anki and make sure the AnkiConnect add-on is installed before syncing.", parse_mode="Markdown")
        return

    sync_msg = await message.reply("⏳ Syncing local Anki to AnkiWeb...")

    try:
        res = anki_service.sync_web()

        if res.get("error"):
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=sync_msg.message_id,
                text=f"❌ AnkiWeb Sync Error: {res['error']}"
            )
        else:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=sync_msg.message_id,
                text="✅ Successfully triggered AnkiWeb synchronization."
            )
    except Exception as e:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=sync_msg.message_id,
            text=f"❌ Fatal Error: {str(e)}"
        )


@dp.message_handler(commands=['getaudio'])
async def get_audio_handler(message: types.Message):
    wait_msg = await message.reply("⏳ Searching for unsynced vocab in Notion...")

    try:
        unsynced_items = await notion_service.get_unsynced_audio()

        if not unsynced_items:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=wait_msg.message_id,
                text="✅ All current items in Notion already have 'Synced to Anki' = True. Nothing to download audio for."
            )
            return

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            text=f"🎧 Found {len(unsynced_items)} unsynced items. Downloading audio in parallel..."
        )

        # Download all audio files in parallel using asyncio.gather
        async def _download_one(item):
            word = item["word"]
            page_id = item["page_id"]
            success, result = await audio_service.download_audio(word)
            return {"page_id": page_id, "word": word, "success": success, "result": result}

        results = await asyncio.gather(
            *[_download_one(item) for item in unsynced_items]
        )

        success_ids = [r["page_id"] for r in results if r["success"]]
        failed_list = [
            f"{r['word']} ({r['result']})" for r in results if not r["success"]]

        if success_ids:
            await notion_service.mark_as_synced(
                notion_service.PROP_SYNC_AUDIO, success_ids)

        report = f"📊 **Audio Download Report**\n- Success: {len(success_ids)}\n- Failed: {len(failed_list)}"
        if failed_list:
            report += "\n\n❌ **Failures:**\n" + \
                "\n".join([f"- {i}" for i in failed_list[:10]])
            if len(failed_list) > 10:
                report += f"\n... and {len(failed_list) - 10} more."

        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            text=report,
            parse_mode="Markdown"
        )
    except Exception as e:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            text=f"❌ Error during audio download: {str(e)}"
        )

if __name__ == "__main__":
    print("Bot is starting...")
    executor.start_polling(dp, skip_updates=True)
