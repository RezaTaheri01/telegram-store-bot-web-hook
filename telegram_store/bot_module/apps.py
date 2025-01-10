from django.apps import AppConfig


class BotModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot_module'

    def ready(self):
        import asyncio
        from .bot import main  # Assume bot logic is in webhook/bot.py
        
        asyncio.run(main())
