from django.apps import AppConfig
import asyncio
from bot_module.bot import app  # Import the global app instance


class BotModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot_module'

    def ready(self):
        # Initialize the bot application once
        # from bot_module.bot import app  # Import the global app instance
        from bot_module.bot import app  # Import the global app instance
        import asyncio

        async def start_bot():
            if not app.running:
                await app.initialize()
                await app.start()

        asyncio.run(start_bot())

