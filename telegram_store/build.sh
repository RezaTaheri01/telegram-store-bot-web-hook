#!/bin/bash

echo "Installing dependencies..."
pip install -r req.txt

echo "Applying migrations..."
python manage.py makemigrations users payment products
python manage.py migrate

echo "Creating superuser..."
# Set your desired superuser credentials here
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@example.com
DJANGO_SUPERUSER_PASSWORD=admin12345678

# Create superuser if it doesn't exist
python manage.py shell << END
from django.contrib.auth import get_user_model
from django.conf import settings
import django

django.setup()
User = get_user_model()
username = "$DJANGO_SUPERUSER_USERNAME"
email = "$DJANGO_SUPERUSER_EMAIL"
password = "$DJANGO_SUPERUSER_PASSWORD"

if not User.objects.filter(username=username).exists():
    user = User.objects.create_superuser(username=username, email=email, password=password)
    print("Superuser created.")
else:
    print("Superuser already exists.")
END

echo "Setup complete!"
