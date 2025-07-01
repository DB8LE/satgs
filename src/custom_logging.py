import logging, os, sys

class CustomFormatter(logging.Formatter):
    # A custom logging formatter

    # ANSI escape codes for coloring
    RESET  = "\x1b[0m"
    RED    = "\x1b[31m"
    YELLOW = "\x1b[33m"

    FORMAT = "[%(asctime)s] (%(levelchar)s) %(message)s" # Default

    LEVEL_MAP = {
        logging.ERROR:   ("E", RED),
        logging.WARNING: ("W", YELLOW),
        logging.INFO:    ("I", ""),  # no color
        logging.DEBUG:   ("D", ""),  # no color
    }

    def format(self, record):
        levelno = record.levelno
        char, color = self.LEVEL_MAP.get(levelno, ("?", ""))

        # Inject new attributes into the record
        record.levelchar = char
        fmt = color + self.FORMAT + self.RESET
        formatter = logging.Formatter(fmt, "%H:%M:%S")
        return formatter.format(record)

def is_poetry():
    # Function to check if program is being run in poetry environment
    venv = os.environ.get("VIRTUAL_ENV")
    if not venv:
        return False
    name = os.path.basename(venv)
    if "poetry" in os.path.dirname(venv) or name.startswith(os.path.basename(os.getcwd()) + "-"):
        return True
    return os.environ.get("POETRY_ACTIVE") == "1"

def set_up_logging():
    # Set logging level to debug if run in poetry environment
    logging_level = logging.INFO
    if is_poetry():
        logging_level = logging.DEBUG

    # Set up logging to print to console
    logging_root = logging.getLogger()
    logging_root.setLevel(logging_level)
    logging_handler = logging.StreamHandler(sys.stdout)
    logging_handler.setLevel(logging_level)
    logging_handler.setFormatter(CustomFormatter())
    logging_root.addHandler(logging_handler)

    if logging_level == logging.DEBUG:
        logging.log(logging.INFO, "Poetry environment detected. Logging level set to debug.")
