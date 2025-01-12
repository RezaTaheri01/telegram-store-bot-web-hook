import asyncio
from django.apps import AppConfig


class BotModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot_module'

    # Todo: Search about ready function and the method that used
    # The current ready(self) approach is functional but not ideal for production.
    # best way is to run it separately. (main branch)
    def ready(self):
        from .bot import main
        import threading
        thread = threading.Thread(target=asyncio.run, args=(main(),))
        thread.daemon = True  # Ensure the thread doesn't block app shutdown
        thread.start()
