import os

def ensure_data_directory():
    """Ensure that the data directory exists."""
    os.makedirs('data', exist_ok=True)