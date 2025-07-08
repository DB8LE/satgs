from src import tle
import os, datetime, re, logging

COSPAR_ID_REGEX = re.compile(r'^[0-9]{4}-[0-9]{3}[A-Z]{1,3}$')

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
