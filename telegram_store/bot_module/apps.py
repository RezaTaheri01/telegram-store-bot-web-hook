import asyncio
from django.apps import AppConfig


class BotModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot_module'

    # Todo: Search about ready function and the method that used
    def ready(self):
        from .bot import main
        import threading
        thread = threading.Thread(target=asyncio.run, args=(main(),))
        thread.start()
