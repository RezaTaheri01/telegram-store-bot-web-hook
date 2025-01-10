from django.http import HttpRequest, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
import logging
from bot_module.bot import ptb_application, Update

# Set up logger
logger = logging.getLogger(__name__)


@csrf_exempt
async def telegram(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        return HttpResponse(status=404)

    logger.info("Telegram")
    try:
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
        await ptb_application.update_queue.put(
            Update.de_json(data=json.loads(request.body), bot=ptb_application.bot)
        )
    except Exception as e:
        logger.error(f"Error in ptb_application.update_queue.put: {e}")

    return HttpResponse(status=200)  # Return a successful response
