#!/bin/bash

# echo "Creating virtual environment..."
# python3 -m venv .venv

# echo "Activating virtual environment..."
# # For Linux/macOS:
# source .venv/bin/activate
# # For Windows (Git Bash / WSL):
# # source .venv/Scripts/activate

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r req.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

END

echo "Setup complete!"
