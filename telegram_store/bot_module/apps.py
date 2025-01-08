from django.apps import AppConfig


class BotModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot_module'

    def ready(self):
        # Initialize the bot application once
        # from bot_module.bot import app  # Import the global app instance
        from bot_module.views import app  # Import the global app instance
        import asyncio

        async def start_bot():
            await app.initialize()
            await app.start()

        asyncio.run(start_bot())
