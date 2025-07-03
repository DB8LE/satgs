import json.tool
from src import paths
import logging, json, requests, os, datetime

TLE_OUTDATED_SECONDS = 96 * 3600 # Hours until TLEs will be considered out of date in seconds NOTE: move this to a settings file?

EXPECTED_TLE_JSON_KEYS = ['OBJECT_NAME', 'OBJECT_ID', 'EPOCH', 'MEAN_MOTION', 'ECCENTRICITY', 'INCLINATION', 'RA_OF_ASC_NODE', 'ARG_OF_PERICENTER', 'MEAN_ANOMALY', 'EPHEMERIS_TYPE', 'CLASSIFICATION_TYPE', 'NORAD_CAT_ID', 'ELEMENT_SET_NO', 'REV_AT_EPOCH', 'BSTAR', 'MEAN_MOTION_DOT', 'MEAN_MOTION_DDOT']

def check_source(source_url: str, print_failure_reason: bool = True) -> bool:
    """
    Checks if a given source URL provides valid json format TLE data. This can either be a single TLE, or an array of TLEs.
    """
    level = logging.DEBUG
    if print_failure_reason:
        level = logging.WARN
    
    logging.log(logging.DEBUG, "Checking TLE source: "+source_url)
    
    # Attempt to download the TLE file
    try:
        TLE_request = requests.get(source_url)
    except Exception as e:
        logging.log(level, "TLE source failed check: Failed to download data. "+str(e))
        return False
    
    # Check status code of data
    if TLE_request.status_code != 200:
        logging.log(level, f"TLE source failed check: Returned status code {str(TLE_request.status_code)}.")
        return False

    # Try parsing the data to check if it's valid json
    try:
        json_data = json.loads(TLE_request.text)
    except json.JSONDecodeError:
        logging.log(level, "TLE source failed check: JSON decode error.")
        return False
    
    # Check if required fields are present
    if type(json_data) == list: # Multiple TLEs
        for TLE in json_data:
            if EXPECTED_TLE_JSON_KEYS != list(TLE.keys()):
                logging.log(level, "TLE source failed check: Invalid JSON keys.")
                return False
    elif type(json_data) == dict: # Single TLE
        if EXPECTED_TLE_JSON_KEYS != list(json_data.keys()):
            logging.log(level, "TLE source failed check: Invalid JSON keys.")
            return False
    else:
        logging.log(level, "TLE source failed check: Invalid data type after parsing.")
        return False

    logging.log(logging.DEBUG, "TLE source checked successfully.")

    return True

def add_source(source_url: str):
    """
    Add a source URL to the list of TLE sources. The source must provide valid json TLEs.
    It can provide multiple TLEs in an array of TLEs.
    """

    # Check if source provides valid data
    if check_source(source_url) == False:
        logging.log(logging.WARN, "TLE source didn't provide valid data. Not adding source.")
        return

    # Ensure newline at the end of each line
    if source_url.endswith("\n") == False:
        source_url += "\n"

    # Append to file
    with open(paths.SOURCES_PATH, "a") as f:
        f.write(source_url)
    
    logging.log(logging.DEBUG, f"Added TLE source {source_url} to sources file.")

def remove_source(source_url: str):
    """
    Remove a source URL from the list of TLE sources. The TLE provided by the source will only be removed on the next update.
    """

    # Read lines
    with open(paths.SOURCES_PATH, "r") as f:
        lines = f.readlines()

    # If source is in list of lines, remove it
    try:
        source_line_index = lines.index(source_url+"\n")
        del lines[source_line_index]
    except ValueError:
        logging.log(logging.WARN, f"Failed to remove source {source_url}. Source not found in sources file.")
        return

    # Write new sources to file
    with open(paths.SOURCES_PATH, "w") as f:
        f.writelines(lines)

def list_sources() -> list[str]:
    """
    Logs a list of all sources with indexes, and returns a list of the source URLs corrensponding to the logged indexes-1
    """
    # Read sources
    with open(paths.SOURCES_PATH, "r") as f:
        sources = f.readlines()

    # Prepare output and 
    logged_sources = []
    for source in sources:
        if source == "\n":
            continue
        source = source.strip()
        logging.log(logging.INFO, f"{len(logged_sources)+1}. {source}")
        logged_sources.append(source)

    return logged_sources

def _process_TLE(data: dict[str, str | int], source: str):
    """
    Internal function used by `download_TLEs` to save TLE data after it had been downloaded and parsed.
    """

    # Check if keys in data are the expected keys
    if EXPECTED_TLE_JSON_KEYS != list(data.keys()):
        logging.log(logging.WARN, f"Failed to download TLEs from source {source}. Source provided data with invalid keys. Skipping this source.")
        return

    # Save data to file
    NORAD_ID = data["NORAD_CAT_ID"]
    with open(os.path.join(paths.TLE_DIRECTORY_PATH, str(NORAD_ID)+".json"), "w") as f:
        json.dump(data, f)

def download_TLEs(log_progress: bool = True):
    """
    Download all TLEs from sources in sources file.
    """
    # Read sources file
    with open(paths.SOURCES_PATH, "r") as f:
        sources = f.readlines()

    # Count total sources that aren't new lines
    total_sources = 0
    for source in sources:
        if source != "\n":
            total_sources += 1

    # If log_progress is enabled, set level of progress logs to info instead of debug
    progress_log_level = logging.DEBUG
    if log_progress:
        progress_log_level = logging.INFO

    # Delete old TLE files
        for file in os.listdir(paths.TLE_DIRECTORY_PATH):
            full_path = os.path.join(paths.TLE_DIRECTORY_PATH, file)
            os.remove(full_path)

    # Process each source
    skipped = 0
    for i, source in enumerate(sources):
        if source == "\n": # Skip empty new lines
            skipped += 1
            continue

        source = source.strip()

        # Log progress
        progress_percent = i-skipped/total_sources
        progress_bar = f"[{"="*(round(progress_percent/10))}{" "*(10-round(progress_percent/10))}]"
        logging.log(progress_log_level, f"Updating TLEs... {progress_bar} ({i-skipped}/{total_sources})")
        
        # Try to download TLEs
        try:
            TLE_request = requests.get(source)
        except Exception as e:
            logging.log(logging.WARN, f"Failed to download TLEs from source {source}. {str(e)}. Skipping this source.")
            continue

        # Check status code
        if TLE_request.status_code != 200:
            logging.log(logging.WARN, f"Failed to download TLEs from source {source}. Source returned status code {TLE_request.status_code}. Skipping this source.")
            continue

        # Try to parse json TLE data
        try:
            TLE_json_data = json.loads(TLE_request.text)
        except json.JSONDecodeError:
            logging.log(logging.WARN, f"Failed to download TLEs from source {source}. Source provided invalid JSON. Skipping this source.")
            continue
        
        # Check if source provided a single or multiple TLEs
        if type(TLE_json_data) == list: # multiple
            for TLE in TLE_json_data:
                _process_TLE(TLE, source)
        elif type(TLE_json_data) == dict: # single
            _process_TLE(TLE_json_data, source)
        else:
            logging.log(logging.WARN, f"Failed to download TLEs from source {source}. Source provided data that caused an invalid data type after parsing. Skipping this source.")
            continue
    logging.log(progress_log_level, f"Updating TLEs... [==========] ({total_sources}/{total_sources})")

    # Update last TLE update timestamp
    timestamp = int(datetime.datetime.now(datetime.timezone.utc).timestamp())
    with open(paths.LAST_TLE_UPDATE_PATH, "w") as f:
        f.write(str(timestamp))

def get_last_TLE_update() -> datetime.datetime:
    """
    Get the time of the last TLE update as a datetime object
    """

    with open(paths.LAST_TLE_UPDATE_PATH, "r") as f:
        ts = f.read()
    return datetime.datetime.fromtimestamp(int(ts), datetime.timezone.utc)

def get_TLE_age_human_readable() -> str:
    """
    Returns a string about how long ago the last TLE update was in a human readable format.
    """
    last_update = get_last_TLE_update()
    delta = datetime.datetime.now(datetime.timezone.utc) - last_update
    seconds = delta.total_seconds()

     # Define units and how many seconds they equal
    intervals = (
        ('year', 365 * 24 * 3600),
        ('month', 30 * 24 * 3600),
        ('day', 24 * 3600),
        ('hour', 3600),
        ('minute', 60),
        ('second', 1),
    )

    for name, count in intervals:
        value = seconds // count
        if value:
            # Proper pluralization
            unit = name
            if value != 1:
                unit = name + "s"
            return f"{round(value)} {unit}"
        
    return "1 second"

def check_TLEs_outdated() -> bool:
    """
    Returns True if TLEs are older than 96 hours.
    """
    last_update = get_last_TLE_update()
    delta = datetime.datetime.now(datetime.timezone.utc) - last_update

    return delta.total_seconds() > TLE_OUTDATED_SECONDS
