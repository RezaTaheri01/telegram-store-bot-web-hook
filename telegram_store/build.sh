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

# Use environment variables to create the superuser non-interactively
python manage.py createsuperuser \
    --noinput \
    --username $DJANGO_SUPERUSER_USERNAME \
    --email $DJANGO_SUPERUSER_EMAIL

# Use a Python script to set the password
echo "Setting password for superuser..."
python << END
from django.contrib.auth import get_user_model
User = get_user_model()
user, created = User.objects.get_or_create(username="$DJANGO_SUPERUSER_USERNAME", email="$DJANGO_SUPERUSER_EMAIL")
if created:
    user.set_password("$DJANGO_SUPERUSER_PASSWORD")
    user.is_superuser = True
    user.is_staff = True
    user.save()
END

echo "Setup complete!"
