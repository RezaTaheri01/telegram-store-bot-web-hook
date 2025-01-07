import asyncio
from telegram import Bot
from decouple import config


# to check if webhook set correctly
# https://api.telegram.org/bot<your-bot-token>/getWebhookInfo
async def set_webhook():
    # replace <your-domain> section with your domain
    WEBHOOK_URL = 'https://<your-domain>/telegram_bot/webhook/'

    token = config("TOKEN_WEB")
    bot = Bot(token)

    try:
        if await bot.set_webhook(url=WEBHOOK_URL):
            print(f"Webhook set successfully for {WEBHOOK_URL}")
        else:
            print(f"Failed to set webhook for {WEBHOOK_URL}")
    except Exception as e:
        print(f"Error setting webhook: {e}")


if __name__ == "__main__":
    asyncio.run(set_webhook())
