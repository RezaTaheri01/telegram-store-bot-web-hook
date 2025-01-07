import asyncio
from django.core.management.base import BaseCommand
from telegram import Bot
from django.conf import settings


# to check if webhook set correctly:
# https://api.telegram.org/bot<your-bot-token>/getWebhookInfo
class Command(BaseCommand):
    help = "Set or delete the Telegram webhook"

    def add_arguments(self, parser):
        parser.add_argument(
            "--action",
            type=str,
            choices=["set", "delete"],
            default="set",
            help="Specify whether to set or delete the webhook. Default is 'set'.",
        )

    def handle(self, *args, **options):
        action = options["action"]
        token = settings.TELEGRAM_BOT_TOKEN  # Fetch token from environment variables
        bot = Bot(token)

        # Async function to set the webhook
        async def set_webhook():
            try:
                webhook_url = settings.TELEGRAM_WEBHOOK_URL
                if await bot.set_webhook(url=webhook_url):
                    self.stdout.write(self.style.SUCCESS(f"Webhook set successfully for {webhook_url}"))
                else:
                    self.stdout.write(self.style.ERROR(f"Failed to set webhook for {webhook_url}"))
            except Exception as e:
                self.stderr.write(f"Error setting webhook: {e}")

        # Async function to delete the webhook
        async def delete_webhook():
            try:
                if await bot.delete_webhook():
                    self.stdout.write(self.style.SUCCESS("Webhook deleted successfully"))
                else:
                    self.stdout.write(self.style.ERROR("Failed to delete webhook"))
            except Exception as e:
                self.stderr.write(f"Error deleting webhook: {e}")

        # Run the appropriate action
        if action == "set":
            asyncio.run(set_webhook())
        elif action == "delete":
            asyncio.run(delete_webhook())
