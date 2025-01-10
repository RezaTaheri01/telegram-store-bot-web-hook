from django.views.decorators.csrf import csrf_exempt
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest, Http404
from telegram import Update
import json
from bot_module.bot import ptb_application, WebhookUpdate, logger


# Create your views here.
@csrf_exempt
async def telegram(request: HttpRequest) -> HttpResponse:
    if request.method == "GET":
        raise Http404

    print("Telegram")
    try:
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
        await ptb_application.update_queue.put(
            Update.de_json(data=json.loads(request.body), bot=ptb_application.bot)
        )
    except Exception as e:
        logger.error(f"Error in ptb_application.update_queue.put: {e}")

    return HttpResponse()


@csrf_exempt
async def custom_updates(request: HttpRequest) -> HttpResponse:
    """
    Handle incoming webhook updates by also putting them into the `update_queue` if
    the required parameters were passed correctly.
    """
    try:
        user_id = int(request.GET["user_id"])
        payload = request.GET["payload"]
    except KeyError:
        return HttpResponseBadRequest(
            "Please pass both `user_id` and `payload` as query parameters.",
        )
    except ValueError:
        return HttpResponseBadRequest("The `user_id` must be a string!")

    await ptb_application.update_queue.put(WebhookUpdate(user_id=user_id, payload=payload))
    return HttpResponse()


@csrf_exempt
async def health(_: HttpRequest) -> HttpResponse:
    """For the health endpoint, reply with a simple plain text message."""
    return HttpResponse("The bot is still running fine :)")
