import asyncio
from django.apps import AppConfig


class BotModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot_module'

    def ready(self):
        from .bot import main

        # We will schedule the async main function outside the django setup
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there is already a running loop (like when running in an async context), don't create a new one
            loop.create_task(main())  # Create task instead of running it immediately
        else:
            asyncio.run(main())  # Only run main() if there is no running loop
