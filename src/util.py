import os, datetime

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
