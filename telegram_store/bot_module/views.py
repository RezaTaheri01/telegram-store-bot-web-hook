from django.views.decorators.csrf import csrf_exempt
from django.http import HttpRequest, HttpResponse
import json
from .bot import logger, ptb_application, Update


# region Views
@csrf_exempt
async def telegram(request: HttpRequest) -> HttpResponse:
    # logger.info(f"Received: {request.body}")
    if request.method == "GET":
        return HttpResponse(status=404)

    logger.info("Telegram")
    try:
        """Handle incoming Telegram updates by putting them into the `update_queue`"""
        # update = Update.de_json(data=json.loads(request.body), bot=ptb_application.bot)
        # logger.info(update.effective_user.id)
        # logger.info(update.effective_user.username)
        await ptb_application.update_queue.put(
            Update.de_json(data=json.loads(request.body), bot=ptb_application.bot)
        )
    except Exception as e:
        logger.error(f"Error in ptb_application.update_queue.put: {e}")

    return HttpResponse(status=200)  # Return a successful response


# @csrf_exempt
# async def custom_updates(request: HttpRequest) -> HttpResponse:
#     """
#     Handle incoming webhook updates by also putting them into the `update_queue` if
#     the required parameters were passed correctly.
#     """
#     try:
#         user_id = int(request.GET["user_id"])
#         payload = request.GET["payload"]
#     except KeyError:
#         return HttpResponseBadRequest(
#             "Please pass both `user_id` and `payload` as query parameters.",
#         )
#     except ValueError:
#         return HttpResponseBadRequest("The `user_id` must be a string!")
#
#     await ptb_application.update_queue.put(WebhookUpdate(user_id=user_id, payload=payload))
#     return HttpResponse()


@csrf_exempt
async def health(_: HttpRequest) -> HttpResponse:
    """For the health endpoint, reply with a simple plain text message."""
    return HttpResponse("The bot is still running fine :)")

# endregion
