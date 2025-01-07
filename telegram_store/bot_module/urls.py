from django.urls import path
from . import bot

urlpatterns = [
    path('webhook/', bot.telegram_webhook, name="webhook"),
]
