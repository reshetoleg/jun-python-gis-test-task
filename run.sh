#!/bin/bash

# Create a virtual environment
python3 -m venv myenv

# Activate the virtual environment
source myenv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set Flask app environment variable
export FLASK_APP=main.py

# Run the Flask application
flask run