import argparse, logging

def set_debug():
    logging.getLogger().setLevel(logging.DEBUG)

def show_version():
    # If check for testing branch. If it is detected, also show latest commit hash
    # We could use a library for this to gurantee that it works, regardless if git is installed,
    # but the user probably has git installed anyway so no need for another library 
    import subprocess
    try:
        git_branch = subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).strip().decode('utf-8')
        latest_commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except FileNotFoundError:
        logging.log(logging.DEBUG, "Git not installed, failed to check for branch.")
        git_branch = "main" # it the user doesn't have git installed, they're probably using the master branch anyway
        latest_commit_hash = "N/A"
    except subprocess.CalledProcessError as e:
        logging.log(logging.DEBUG, "Error while checking git branch & lastest commit hash.")
        logging.log(logging.DEBUG, e)
        git_branch = "main" # it the user doesn't have git installed, they're probably using the master branch anyway
        latest_commit_hash = "N/A"

    import importlib.metadata
    if git_branch != "main":
        logging.log(logging.INFO, f"You are running satgs v{importlib.metadata.version("satgs")}@{git_branch} ({latest_commit_hash})")
    else:
        logging.log(logging.INFO, f"You are running satgs v{importlib.metadata.version("satgs")}")

    exit()

def no_args_message(args):
    logging.log(logging.ERROR, "Please provide a subcommand to run. Run `satgs --help` for help.")
    

def test_func(args):
    logging.log(logging.INFO, "Test")
    if args.foo:
        logging.log(logging.INFO, "Got test argument")


def set_up_argparse():
    # Set up base parser
    parser = argparse.ArgumentParser(prog="satgs", add_help=True)
    parser.add_argument("--debug", action="store_true",
                        help="set logging level to debug")
    parser.add_argument("--version", action="store_true",
                        help="show program version and exit")


    # Set up sub commands
    sub_parsers = parser.add_subparsers(required=False)


    sub_test = sub_parsers.add_parser("test", parents=[parser], add_help=False,
                                      help="A test subcommand. Temporary!")
    sub_test.set_defaults(func=test_func)
    sub_test.add_argument("--foo", action="store_true", help="Test argument!")
    
    # Set default function (if no subcommand was provided) to show error message
    parser.set_defaults(func=no_args_message)

    # Parse arguments
    args = parser.parse_args()
    logging.log(logging.DEBUG, "Got args "+str(args))

    # Handle global arguments
    if args.debug:
        set_debug()
    if args.version:
        show_version()

    # Run subcommand associated functions
    args.func(args)