import platformdirs, os

# Definitions for paths of all program files
CONFIG_DIR = platformdirs.user_config_dir("satgs")
DATA_DIR = platformdirs.user_data_dir("satgs")

TLE_DIRECTORY_PATH = os.path.join(DATA_DIR, "tle/")
SOURCES_PATH = os.path.join(CONFIG_DIR, "sources.txt")
LAST_TLE_UPDATE_PATH = os.path.join(DATA_DIR, "last_tle_update.txt")

ROTOR_CONFIG_DIRECTORY_PATH = os.path.join(CONFIG_DIR, "rotors/")
RADIO_CONFIG_DIRECTORY_PATH = os.path.join(CONFIG_DIR, "radios/")

SETTINGS_FILE_PATH = os.path.join(CONFIG_DIR, "settings.json")
