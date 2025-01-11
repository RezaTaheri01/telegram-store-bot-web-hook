from django.urls import path
from . import views

urlpatterns = [
    path("telegram", views.telegram, name="Telegram updates"),
    # path("submitpayload", view.custom_updates, name="custom updates"),
    path("healthcheck", views.health, name="health check"),
]
