from src import tle, paths
import os, datetime, re, logging, shutil, socket

last_port = 56000

COSPAR_ID_REGEX = re.compile(r'^[0-9]{4}-[0-9]{3}[A-Z]{1,3}$')

FREQUENCY_BAND_LETTERS = [
    (0, 30e6, "H"),          # HF and below
    (30e6, 300e6, "V"),      # VHF
    (300e6, 1e9, "U"),       # UHF
    (1e9, 2e9, "L"),         # L-Band
    (2e9, 4e9, "S"),         # S-Band
    (4e9, 8e9, "C"),         # C-Band
    (8e9, 12e9, "X"),        # X-Band
    (12e9, 40e9, "K")       # K-Band (includes Ku and Ka)
    # Anything else will be O (other)
]

def is_poetry():
    """A function to check if program is being run in poetry environment"""
    venv = os.environ.get("VIRTUAL_ENV")
    if not venv:
        return False
    name = os.path.basename(venv)
    if "poetry" in os.path.dirname(venv) or name.startswith(os.path.basename(os.getcwd()) + "-"):
        return True
    return os.environ.get("POETRY_ACTIVE") == "1"

def decorated_input() -> str:
    """A function to get input from the user while maintaining the logging style"""

    time = datetime.datetime.now().strftime("%H:%M:%S")
    decorator_string = f"[{time}] (I) >> "

    return input(decorator_string)

def _check_port_used(port: int) -> bool:
    """A function to check if a port is in use"""

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0
    
def get_frequency_band_letter(frequency: int) -> str:
    """A function to get a frequency band letter by the frequency in herz"""
    for lower, upper, letter in FREQUENCY_BAND_LETTERS:
        if frequency >= lower and frequency <= upper:
            return letter
    return "O"
    
def get_unused_port(purpose: str = "N/A") -> int:
    """
    Get an unused port. Optionally provide the purpose for the port for logging.
    """
    global last_port
    
    while True:
        last_port += 1

        if _check_port_used(last_port):
            logging.log(logging.DEBUG, f"Port {last_port} is in use")
        else:
            logging.log(logging.DEBUG, f"Using port {last_port} for {purpose}")
            return last_port

def satellite_norad_from_input(input: str) -> str:
    """
    Get a satellite NORAD ID by either one of these input opions:
    1. Just the NORAD ID
    2. The satellites name (input required if multiple matches)
    3. COSPAR ID

    Which of these was provided will be detected automatically.
    """

    input = input.strip()

    if input.isdigit(): # Check if input is a NORAD ID
        return input
    
    sat_IDs = tle.load_tle_data() # If it's not a NORAD ID, we have to load some extra data
    if COSPAR_ID_REGEX.match(input): # Check if input is a COSPAR ID
        index = [x for x, y in enumerate(sat_IDs) if y[1] == input]
        if index == []:
            logging.log(logging.ERROR, f"Can't find satellite with COSPAR ID '{input}' in local TLEs.")
            exit()
        sat_ID = sat_IDs[index[0]]
        
        return sat_ID[0]
    else: # Otherwise it's probably a name
        prepared_input = input.lower().replace("-", " ")
        search_hits = [t for t in sat_IDs if prepared_input in t[2].lower().replace("-", " ")]
        if search_hits == []:
            logging.log(logging.ERROR, f"Can't find satellite with name '{input}' in local TLEs.")
            exit()
        
        if len(search_hits) == 1:
            return search_hits[0][0]
        else:
            logging.log(logging.INFO, f"Found multiple hits while searching for '{input}'. Select the index of the satellite you wish to pick.")
            for i, satellite in enumerate(search_hits):
                logging.log(logging.INFO, f"{i+1}. {satellite[0]} \\ {satellite[2]}")
            choice = decorated_input()
            try:
                return search_hits[int(choice)-1][0]
            except (TypeError, ValueError, IndexError):
                logging.log(logging.ERROR, "Invalid choice!")
                exit()

def clean_all_data():
    """
    A function to delete all data files ever created by satgs.
    """

    logging.log(logging.INFO, "Deleting data..")
    shutil.rmtree(paths.CONFIG_DIR)
    shutil.rmtree(paths.DATA_DIR)
    logging.log(logging.INFO, "Done!")
