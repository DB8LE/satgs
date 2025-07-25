from src import tle, util, tracking, settings, paths, transponders
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
    

# update subcommand functions
def update_all(args):
    logging.log(logging.INFO, "Updating TLEs..")
    tle.download_TLEs()
    logging.log(logging.INFO, "Updating transponders")
    transponders.download_transponders()
    logging.log(logging.INFO, "Done!")
    exit()

def update_TLEs(args):
    tle.download_TLEs()
    logging.log(logging.INFO, "Done!")
    exit()

def update_transponders(args):
    transponders.download_transponders()
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
    try:
        remove_index = int(util.decorated_input())-1
        tle.remove_source(sources[remove_index])
    except (TypeError, ValueError, IndexError):
        logging.log(logging.ERROR, "Invalid choice!")

# tracking subcommand
def track(args):
    # just a wrapper to accept the arguments
    tracking.track(util.satellite_norad_from_input(args.satellite), args.rotor, args.radio, args.usb)

# settings subcommands
def list_settings(args):
    logging.log(logging.INFO, "Listing settings...")
    settings_data = settings.load_settings_file()

    for setting, value in settings_data.items():
        logging.log(logging.INFO, setting+": "+str(value))
    exit()

def modify_setting(args):
    logging.log(logging.INFO, f"Setting value of setting '{args.setting_key}' to '{args.new_setting_value}'")
    settings.set_setting(args.setting_key, args.new_setting_value)
    exit()

def get_settings_path(args):
    logging.log(logging.INFO, "Settings path: "+paths.CONFIG_DIR)

def clean_data(args):
    logging.log(logging.INFO, "Are you sure that you want to delete all settings (rotor config, radio config, sources, settings)? (N/y)")
    choice = util.decorated_input()
    if choice.lower().strip() == "y":
        util.clean_all_data()

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

    # update subcommands
    parser_update = sub_parsers.add_parser("update", help="Update data like TLEs. Can be called without subcommand to update everything")
    update_sub = parser_update.add_subparsers(required=False)

    parser_update_tle = update_sub.add_parser("tles", help="Update all TLEs")
    parser_update_tle.set_defaults(func=update_TLEs)

    parser_update_transponders = update_sub.add_parser("transponders", help="Update transponders file")
    parser_update_transponders.set_defaults(func=update_transponders)

    parser_update.set_defaults(func=update_all)

    # sources subcommands
    parser_sources = sub_parsers.add_parser("sources", help="Manage TLE sources")
    sources_sub = parser_sources.add_subparsers(required=True)

    parser_sources_add = sources_sub.add_parser("add", help="Add a TLE source")
    parser_sources_add.set_defaults(func=add_source)

    parser_sources_list = sources_sub.add_parser("list", help="List all current TLE sources")
    parser_sources_list.set_defaults(func=list_sources)

    parser_sources_remove = sources_sub.add_parser("remove", help="Remove a TLE source")
    parser_sources_remove.set_defaults(func=remove_source)

    # tracking subcommand
    parser_track = sub_parsers.add_parser("track", help="Track a satellite")
    parser_track.add_argument("satellite", help="Either the NORAD ID, COSPAR ID or name of the satellite to be tracked." \
                                                  "TLE must be avaliable in local database.")
    parser_track.add_argument("--radio", type=str, choices=tracking.list_radios(),
                              help="The name of a radio config file (without file extension)")
    parser_track.add_argument("--rotor", type=str, choices=tracking.list_rotors(),
                              help="The name of a rotor config file (without file extension)")
    parser_track.add_argument("-u", "--usb", type=str,
                              help="USB port that the rotor is connected to")
    parser_track.set_defaults(func=track)

    # settings subcommands
    parser_settings = sub_parsers.add_parser("settings", help="View and change settings")
    settings_sub = parser_settings.add_subparsers(required=True)

    parser_settings_list = settings_sub.add_parser("list", help="List all settings")
    parser_settings_list.set_defaults(func=list_settings)

    parser_settings_modify = settings_sub.add_parser("modify", help="Modify the value of a setting")
    parser_settings_modify.add_argument("setting_key", choices=settings.load_settings_file().keys(),
                                        help="The key of the setting to modify (check with `satgs settings list`)")
    parser_settings_modify.add_argument("new_setting_value", help="The new value of the setting")
    parser_settings_modify.set_defaults(func=modify_setting)

    parser_settings_get_path = settings_sub.add_parser("path", help="Get the path in which all config files are stored")
    parser_settings_get_path.set_defaults(func=get_settings_path)

    parser_setting_clean_data = settings_sub.add_parser("clean", help="Delete all config and data files created by satgs")
    parser_setting_clean_data.set_defaults(func=clean_data)
    
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