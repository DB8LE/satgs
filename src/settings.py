
import importlib.resources
from typing import Any
from src import paths
import json, logging, os

def restore_default_settings():
    """
    Restores current settings file to defaults.
    """
    # Ensure config parent directory exists
    if not os.path.exists(paths.CONFIG_DIR):
        os.makedirs(paths.CONFIG_DIR, exist_ok=True)

    # Restore default settings file
    with importlib.resources.open_text('src.resources', 'default_settings.json') as f:
        defaults = f.read()

    with open(paths.SETTINGS_FILE_PATH, "w") as f:
        f.write(defaults)

def load_settings_file() -> dict[str, Any]:
    """
    Read and parse the settings file as JSON.
    """
    try:
        with open(paths.SETTINGS_FILE_PATH, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logging.log(logging.ERROR, "JSON decode error while reading parsing settings file. Check if it contains valid JSON and fix invalid syntax.")
        exit()
    except FileNotFoundError:
        logging.log(logging.INFO, "Settings file doesn't exist yet! Creating it...")
        restore_default_settings()
        return load_settings_file()

def get_setting(setting_key: str) -> Any:
    """
    Get a setting from the settings file. Exits program if setting couldn't be found.
    """
    settings = load_settings_file()

    try:
        return settings[setting_key]
    except KeyError:
        logging.log(logging.ERROR, "Couldn't find setting with key: "+setting_key)
        exit()
    
def set_setting(setting_key: str, new_value: Any):
    """
    Set the value of a setting.
    """
    settings = load_settings_file()

    try:
        # NOTE: check if type is the same maybe?
        settings[setting_key] = new_value
    except KeyError:
        logging.log(logging.WARN, "Tried setting value of setting key that doesn't exist in the settings file. Settings not changed.")
        return
    
    with open(paths.SETTINGS_FILE_PATH, "w") as f:
        json.dump(settings, f)