import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from telegram import Update, Bot

from django.conf import settings

bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)


@csrf_exempt
def webhook(request):
    if request.method == "POST":
        update = Update.de_json(json.loads(request.body), bot)
        if update.message:  # Check if it's a message update
            chat_id = update.message.chat.id
            text = update.message.text

            # Respond to the message
            bot.send_message(chat_id=chat_id, text=f"You said: {text}")

        return JsonResponse({"status": "ok"})
    return JsonResponse({"error": "Invalid request"}, status=400)
