from src import tle, util
import argparse, logging

def set_debug():
    logging.getLogger().setLevel(logging.DEBUG)

def show_version(args):
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
    

# TLE subcommand functions
def update_TLEs(args):
    logging.log(logging.INFO, "Updating TLEs...")
    tle.download_TLEs()
    logging.log(logging.INFO, "Done!")
    exit()

# sources subcommand functions
def add_source(args):
    logging.log(logging.INFO, "Enter the URL to the source your would like to add.")
    source_url = util.decorated_input()
    tle.add_source(source_url)
    exit()

def list_sources(args):
    logging.log(logging.INFO, "Listing sources...")
    tle.list_sources()
    exit()

def remove_source(args):
    logging.log(logging.INFO, "Listing sources...")
    sources = tle.list_sources()
    logging.log(logging.INFO, "Enter the index of the source you'd like to remove.")
    remove_index = int(util.decorated_input())-1
    tle.remove_source(sources[remove_index])

def set_up_argparse():
    # Set up base parser
    parser = argparse.ArgumentParser(prog="satgs", add_help=True)
    parser.add_argument("--debug", action="store_true",
                        help="set logging level to debug")

    # Set up subcommands
    sub_parsers = parser.add_subparsers()

    # version subcommand
    parser_version = sub_parsers.add_parser("version", help="Show version")
    parser_version.set_defaults(func=show_version)

    # TLE subcommands
    parser_tle = sub_parsers.add_parser("tle", help="Manage TLEs")
    tle_sub = parser_tle.add_subparsers(required=True)

    parser_tle_update = tle_sub.add_parser("update", help="Update all TLEs")
    parser_tle_update.set_defaults(func=update_TLEs)

    # sources subcommands
    parser_sources = sub_parsers.add_parser("sources", help="Manage TLE sources")
    sources_sub = parser_sources.add_subparsers(required=True)

    parser_sources_add = sources_sub.add_parser("add", help="Add a TLE source")
    parser_sources_add.set_defaults(func=add_source)

    parser_sources_list = sources_sub.add_parser("list", help="List all current TLE sources")
    parser_sources_list.set_defaults(func=list_sources)

    parser_sources_remove = sources_sub.add_parser("remove", help="Remove a TLE source")
    parser_sources_remove.set_defaults(func=remove_source)
    
    # Set default function (if no subcommand was provided) to show error message
    parser.set_defaults(func=no_args_message)

    # Parse arguments
    args = parser.parse_args()
    logging.log(logging.DEBUG, "Got args "+str(args))

    # Handle global arguments
    if args.debug:
        set_debug()

    # Run subcommand associated functions
    args.func(args)