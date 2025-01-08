import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update
from .bot import app as bot_app  # Import the bot application

# Set up logging
logging.basicConfig(level=logging.INFO)


@csrf_exempt
async def webhook(request):
    """
    Handle incoming Telegram webhook requests asynchronously.
    """
    if request.method == "POST":
        try:
            # Parse the incoming update
            update = Update.de_json(json.loads(request.body), bot_app.bot)

            # Process the update with the bot_app instance
            await bot_app.process_update(update)

            return JsonResponse({"status": "ok"})
        except Exception as e:
            logging.error(f"Error handling webhook: {e}")
            return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"error": "Invalid request"}, status=400)
