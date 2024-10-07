#!/bin/bash

# Create a virtual environment
python -m venv venv-dev

# Activate the virtual environment
# Note: The activation script path may vary depending on your Python installation
source venv-dev/bin/activate

# Install the package with optional dependencies
pip install -e .[test]

# Deactivate the virtual environment
deactivate