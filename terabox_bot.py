import os
import re
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes, CommandHandler
from TeraboxDL import TeraboxDL

# ====================== CONFIG ======================
BOT_TOKEN = "8378452706:AAF68D6qp4BJSSSNCEB4LKZHTsiNausRdfA"
OWNER_ID = 8509316210
TERABOX_COOKIE = "lang=en; ndus=Y4ujXe3teHuihU7lpERWF6pE3a7qdk9yziEvSBFj"
MAX_DOWNLOAD_SIZE_MB = 45
DOWNLOAD_FOLDER = "downloads"
# ====================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
terabox = TeraboxDL(TERABOX_COOKIE)

TERABOX_REGEX = re.compile(
    r"https?://(?:www\.)?(?:terabox|1024terabox|teraboxapp|4funbox|mirrobox|nephobox|momerybox|terasharelink|tibibox)\.(?:com|app|fun|co)/s/[a-zA-Z0-9_-]+",
    re.IGNORECASE
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("This bot is private. Only the owner can use it.")
        return
    await update.message.reply_text(
        "Private Terabox Bot is ready!\n\nJust send me any Terabox link."
    )

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("This bot is private.")
        return

    text = update.message.text.strip()
    match = TERABOX_REGEX.search(text)
    if not match:
        await update.message.reply_text("Please send a valid Terabox link.")
        return

    link = match.group(0)
    msg = await update.message.reply_text("Processing Terabox link... Please wait.")

    try:
        file_info = terabox.get_file_info(link, direct_url=True)

        if "error" in file_info:
            await msg.edit_text(f"❌ Error: {file_info['error']}")
            return

        name = file_info.get("file_name", "Unknown")
        size = file_info.get("file_size", "Unknown")
        direct = file_info.get("download_link")

        caption = (
            f"**File Name:** `{name}`\n"
            f"**Size:** `{size}`\n\n"
            f"**Direct Download Link:**\n`{direct}`"
        )

        await msg.edit_text(caption, parse_mode="Markdown")

        # Try to download & send if file is small
        try:
            size_str = str(size).upper().replace(" ", "")
            size_mb = 0
            if "GB" in size_str:
                size_mb = float(re.findall(r"[\d.]+", size_str)[0]) * 1024
            elif "MB" in size_str:
                size_mb = float(re.findall(r"[\d.]+", size_str)[0])
            elif "KB" in size_str:
                size_mb = float(re.findall(r"[\d.]+", size_str)[0]) / 1024

            if 0 < size_mb <= MAX_DOWNLOAD_SIZE_MB:
                await msg.reply_text("File is small. Downloading and sending to you...")
                result = terabox.download(file_info, save_path=DOWNLOAD_FOLDER)

                if "error" not in result:
                    file_path = result["file_path"]
                    await update.message.reply_document(
                        document=open(file_path, "rb"),
                        filename=name,
                        caption=name
                    )
                    try:
                        os.remove(file_path)
                    except:
                        pass
                else:
                    await msg.reply_text(f"Download failed: {result['error']}")
            else:
                await msg.reply_text(
                    f"File is larger than {MAX_DOWNLOAD_SIZE_MB} MB.\n"
                    "Please use the Direct Link above with IDM / browser / aria2c."
                )
        except Exception as e:
            logger.error(f"Download error: {e}")
            await msg.reply_text("Could not auto-download. Use the direct link.")

    except Exception as e:
        logger.error(e)
        await msg.edit_text(f"Something went wrong:\n`{str(e)}`", parse_mode="Markdown")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
 app.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handle_link))

    print("✅ Private Terabox Bot started successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
