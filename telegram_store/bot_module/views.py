import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from django.conf import settings

# Set up logging
logging.basicConfig(level=logging.INFO)

# Build the bot application
app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()


# Define command handler
async def start(update: Update, context):
    """
    Handle the /start command.
    """
    await update.message.reply_text("Welcome! I am your bot. How can I assist you?")


# Define a message handler
async def echo(update: Update, context):
    """
    Echo back any text message sent by the user.
    """
    text = update.message.text
    await update.message.reply_text(f"You said: {text}")


# Add handlers to the Application instance
app.add_handler(CommandHandler("start", start))  # Handle /start command
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))  # Handle all text messages


@csrf_exempt
async def webhook(request):
    """
    Handle incoming Telegram webhook requests asynchronously.
    """
    if request.method == "POST":
        try:
            # Parse the incoming update
            update = Update.de_json(json.loads(request.body), app.bot)

            # Process the update with the Application instance
            await app.process_update(update)

            return JsonResponse({"status": "ok"})
        except Exception as e:
            logging.error(f"Error handling webhook: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)


# Optional: Shut down the application gracefully on server stop
import atexit


@atexit.register
def cleanup():
    import asyncio
    asyncio.run(app.shutdown())
