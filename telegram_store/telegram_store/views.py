from django.views.generic import TemplateView


class HomePage(TemplateView):
    template_name = "home.html"


# region Control Bots

# # with below code you can start or stop bot remotely
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# from django_ratelimit.decorators import ratelimit
# import subprocess


# # Constants for paths and rate limiting
# BOT_SCRIPT_PATH = "<path-to-bot-1>"
# BOT2_SCRIPT_PATH = "<path-to-bot-2>"
# PYTHON_PATH = "<path-to-venv>"

# @ratelimit(key="ip", rate="1/m", block=True)
# @csrf_exempt  # Remove this if CSRF tokens can be used
# def control_bot(request):
#     if request.method != "GET":
#         return JsonResponse({"error": "Invalid request method."}, status=405)
#
#     action = request.GET.get("action")
#     if action not in {"start", "stop"}:
#         return JsonResponse({"error": "Invalid action."}, status=400)
#
#     try:
#         if action == "start":
#             if is_bot_running():
#                 return JsonResponse({"message": "Bots are already running."}, status=200)
#             start_bots()
#             logging.info("Bots started successfully.")
#             return JsonResponse({"message": "Bots started successfully."}, status=200)
#
#         elif action == "stop":
#             stop_bots()
#             logging.info("Bots stopped successfully.")
#             return JsonResponse({"message": "Bots stopped successfully."}, status=200)
#
#     except Exception as e:
#         logging.error(f"Error during bot control: {e}")
#         return JsonResponse({"error": "An error occurred."}, status=500)
#
# def is_bot_running():
#     result = subprocess.run(["pgrep", "-f", BOT_SCRIPT_PATH], stdout=subprocess.PIPE)
#     result2 = subprocess.run(["pgrep", "-f", BOT_DICE_SCRIPT_PATH], stdout=subprocess.PIPE)
#     return bool(result.stdout) and bool(result2.stdout)
#
# def start_bots():
#     subprocess.Popen([PYTHON_PATH, BOT_SCRIPT_PATH])
#     subprocess.Popen([PYTHON_PATH, BOT_DICE_SCRIPT_PATH])
#
# def stop_bots():
#     subprocess.run(["pkill", "-f", BOT_SCRIPT_PATH])
#     subprocess.run(["pkill", "-f", BOT_DICE_SCRIPT_PATH])

# endregion


from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def run_migrations_and_create_superuser(request):
    """
    API view to run migrations and create a superuser if one does not exist.
    """
    try:
        # Run migrations
        call_command('makemigrations', interactive=False)
        call_command('migrate', interactive=False)

        # Check if a superuser exists
        User = get_user_model()
        username = "admin0"
        email = "admin@example.com"
        password = "admin12345678"  # Consider using environment variables here

        if not User.objects.filter(username=username).exists():
            # Create superuser if it doesn't exist
            User.objects.create_superuser(username=username, email=email, password=password)
            return JsonResponse({"message": "Superuser created successfully and migrations ran!"}, status=201)
        else:
            return JsonResponse({"message": "Superuser already exists, migrations ran successfully!"}, status=200)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
