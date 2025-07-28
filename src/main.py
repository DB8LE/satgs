from src import custom_logging, arguments, paths, tle
import logging, os, shutil
import importlib_resources # backport for pre python 3.12 compatibility

def main():
    # Set up logging
    custom_logging.set_up_logging()

    # Ensure necessary directories exist
    if not os.path.exists(paths.CONFIG_DIR):
        os.makedirs(paths.CONFIG_DIR, exist_ok=True)

    if not os.path.exists(paths.DATA_DIR):
        os.makedirs(paths.DATA_DIR, exist_ok=True)

    if not os.path.exists(paths.TLE_DIRECTORY_PATH):
        os.makedirs(paths.TLE_DIRECTORY_PATH, exist_ok=True)

    if not os.path.exists(paths.TRANSPONDERS_DIRECTORY_PATH):
        os.makedirs(paths.TRANSPONDERS_DIRECTORY_PATH, exist_ok=True)

    resources_files = importlib_resources.files().joinpath("resources")
    if not os.path.exists(paths.ROTOR_CONFIG_DIRECTORY_PATH):
        os.makedirs(paths.ROTOR_CONFIG_DIRECTORY_PATH, exist_ok=True)

        # Copy default config files
        with importlib_resources.as_file(resources_files.joinpath("rotors_default")) as dir:
            shutil.copytree(dir, paths.ROTOR_CONFIG_DIRECTORY_PATH, dirs_exist_ok=True)

    if not os.path.exists(paths.RADIO_CONFIG_DIRECTORY_PATH):
        os.makedirs(paths.RADIO_CONFIG_DIRECTORY_PATH, exist_ok=True)

        # Copy default config files
        with importlib_resources.as_file(resources_files.joinpath("radios_default")) as dir:
            shutil.copytree(dir, paths.RADIO_CONFIG_DIRECTORY_PATH, dirs_exist_ok=True)

    # Ensure necessary files exist
    if not os.path.exists(paths.SOURCES_PATH):
        with open(paths.SOURCES_PATH, "w"): pass
        tle.add_source("https://celestrak.org/NORAD/elements/gp.php?GROUP=amateur&FORMAT=json")
        tle.add_source("https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=json")

    if not os.path.exists(paths.LAST_TLE_UPDATE_PATH):
        with open(paths.LAST_TLE_UPDATE_PATH, "w") as f:
            f.write("0")

    # Settings file is created when load_settings_file is called, so no need to do it here.

    # Check for TLE age
    TLE_age_human_readable = tle.get_TLE_age_human_readable()
    if TLE_age_human_readable == "never":
        logging.log(logging.WARN, "TLEs have never been updated. Update using `satgs update tles` when possible.")
    else:
        if tle.check_TLEs_outdated():
            logging.log(logging.WARN, f"TLEs are {TLE_age_human_readable} old. Update when possible.")
        else:
            logging.log(logging.INFO, f"TLEs are {TLE_age_human_readable} old.")

    # Set up argument parsing and parse args
    arguments.set_up_argparse()
