from src import paths, util
from typing import Tuple
import os, requests, logging, json

SATNOGS_TRANSITTERS_API_URL = "https://db.satnogs.org/api/transmitters/"

def download_transponders():
    """
    Download the newest version of the transmitters.json file.
    """

    # Try to download data
    try:
        request = requests.get(SATNOGS_TRANSITTERS_API_URL, params={"format": "json"})
    except Exception as e:
        logging.log(logging.ERROR, "Failed to download transponder data.")
        logging.log(logging.ERROR, e)
        exit()

    # Check status code
    if request.status_code != 200:
        logging.log(logging.ERROR, f"Failed to download transponder data. API returned status code {request.status_code}.")
        exit()

    # Try to parse JSON data
    try:
        json_data = json.loads(request.text)
    except json.JSONDecodeError:
        logging.log(logging.ERROR, "Failed to download transponder data. API returned invalid JSON.")
        exit()
    
    # Sort transponders to a per NORAD ID dict
    transponders = {}
    for trsp in json_data:
        try: # If satellite already exists in formatted transponder list, just add the current transponder to the dict indexed by its uuid
            transponders[trsp["norad_cat_id"]][trsp["uuid"]] = trsp
        except KeyError: # If it doesn't exist yet, create the satellites entry and set it to a dict containing the current transponder indexed by it's uuid
            transponders[trsp["norad_cat_id"]] = {trsp["uuid"]: trsp}

    # Save to dict elements to files
    for NORAD_ID, trsp in transponders.items():
        with open(os.path.join(paths.TRANSPONDERS_DIRECTORY_PATH, str(NORAD_ID)+".json"), "w") as f:
            json.dump(trsp, f)

def get_transponder_frequencies(NORAD_ID: str, transponder_UUID: str) -> Tuple[int, int | None, int, int | None, bool]:
    """
    Get the uplink and downlink frequencies of a transponder by the satellite NORAD ID and the transponder UUID.
    This function returns a tuple with four elements.
    
    The firt element is the lower downlink frequency.
    The second element is the upper downlink frequency. If the downlink is not a range of frequencies, the first value should be used and this one will be None.
    The third and fourth elements are the same but for the uplink.
    """

    # Try to open file and parse json
    try:
        with open(os.path.join(paths.TRANSPONDERS_DIRECTORY_PATH, NORAD_ID+".json"), "r") as f:
            trsp = json.load(f)[transponder_UUID]
    except FileNotFoundError:
        logging.log(logging.ERROR, f"Error while loading transponder file for NORAD ID {NORAD_ID}. File does not exist.")
        exit()
    except json.JSONDecodeError:
        logging.log(logging.ERROR, f"Error while loading transponder file for NORAD ID {NORAD_ID}. File contains invalid JSON.")
        exit()

    return (trsp["downlink_low"], trsp["downlink_high"], trsp["uplink_low"], trsp["uplink_high"], trsp["invert"])

def user_transponder_selection(NORAD_ID: str) -> str:
    """
    Prompt the user to select a transponder out of all transponder available on the satellite. Returns the selected transponders UUID.
    """

    # Load transponder data for satellite
    with open(os.path.join(paths.TRANSPONDERS_DIRECTORY_PATH, NORAD_ID+".json"), "r") as f:
        transponders = json.load(f)

    # Find longest option for spacing (description doesn't matter as it's at the end)
    longest_num = len(str(len(transponders)+1))
    longest_mode = 0
    for _, trsp in transponders.items():
        mode_len = len(trsp["mode"])

        if mode_len > longest_mode:
            longest_mode = mode_len

    # Print options to user
    for i, (_, trsp) in enumerate(transponders.items()):
        num = str(i+1)
        mode = trsp["mode"]
        desc = trsp["description"]
        num = " "*(longest_num-len(num))+num
        mode = mode+" "*(longest_mode-len(mode)) # pad with spaces

        logging.log(logging.INFO, f"{num}. {mode}  /  {desc}")

    # Get input
    choice = util.decorated_input()
    try:
        return list(transponders.items())[int(choice)-1][0]
    except Exception:
        logging.log(logging.ERROR, "Invalid choice!")
        exit()
