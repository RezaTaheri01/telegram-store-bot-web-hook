# Simple bot for testing webhook
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler
import json
import logging
from decouple import config

# Initialize logging
logger = logging.getLogger(__name__)

# Create the bot application
BOT_TOKEN = config("TOKEN_WEB")
bot = Bot(token=BOT_TOKEN)
app = Application.builder().token(BOT_TOKEN).build()


# Define a simple command handler
async def start(update: Update, context):
    await update.message.reply_text("Hello! Welcome to the bot!")


# Add the handler to the application
app.add_handler(CommandHandler("start", start))


@csrf_exempt
async def telegram_webhook(request):
    """Webhook view to handle Telegram updates."""
    if request.method == "POST":
        try:
            # Decode and parse the JSON payload
            body = request.body.decode("utf-8")
            data = json.loads(body)

            # Convert to a Telegram Update object
            update = Update.de_json(data, bot)

            # Initialize the application if needed
            if not app.running:
                await app.initialize()

            # Process the incoming update
            await app.process_update(update)
            return JsonResponse({"status": "success"})
        except Exception as e:
            logger.error(f"Error processing update: {e}", exc_info=True)
            return JsonResponse({"status": "error", "message": str(e)})
    return HttpResponse("OK")
