from src import custom_logging, arguments, paths, tle
import logging, os

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

    # Ensure necessary files exist
    if not os.path.exists(paths.SOURCES_PATH):
        with open(paths.SOURCES_PATH, "w"): pass
        tle.add_source("https://celestrak.org/NORAD/elements/gp.php?GROUP=amateur&FORMAT=json")
        tle.add_source("https://celestrak.org/NORAD/elements/gp.php?GROUP=weather&FORMAT=json")

    if not os.path.exists(paths.LAST_TLE_UPDATE_PATH):
        with open(paths.LAST_TLE_UPDATE_PATH, "w") as f:
            f.write("0")

    # Check for TLE age
    TLE_age_human_readable = tle.get_TLE_age_human_readable()
    if tle.check_TLEs_outdated():
        logging.log(logging.WARN, f"TLEs are {TLE_age_human_readable} old. Update when possible.")
    else:
        logging.log(logging.INFO, f"TLEs are {TLE_age_human_readable} old.")

    # Set up argument parsing and parse args
    arguments.set_up_argparse()
