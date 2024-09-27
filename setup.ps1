# setup.ps1

# Create a virtual environment
python -m venv venv-dev

# Activate the virtual environment
# Note: The activation script path may vary depending on your Python installation
.\venv-dev\Scripts\Activate.ps1

# Install the package with optional dependencies
pip install -e .[test]

# Deactivate the virtual environment
deactivate