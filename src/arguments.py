from src import tle, util, tracking, settings, paths, transponders, test
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
        logging.log(logging.INFO, f"You are running satgs v{importlib.metadata.version('satgs')}@{git_branch} ({latest_commit_hash})")
    else:
        logging.log(logging.INFO, f"You are running satgs v{importlib.metadata.version('satgs')}")

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
    rotor_mode_overwrite = None
    if args.rotor_normal:
        rotor_mode_overwrite = 1
    elif args.rotor_inverted:
        rotor_mode_overwrite = 2

    tracking.track(util.satellite_norad_from_input(args.satellite), args.rotor, args.radio, args.rotor_usb, args.rx_usb, args.tx_usb, args.trx_usb, not args.unlock, rotor_mode_overwrite)

# testing subcommands
def test_rotor(args):
    rotor_mode_overwrite = None
    if args.rotor_normal:
        rotor_mode_overwrite = 1
    elif args.rotor_inverted:
        rotor_mode_overwrite = 2

    test.rotor_test(args.rotor, args.rotor_usb, rotor_mode_overwrite)

def test_rotor_full(args):
    rotor_mode_overwrite = None
    if args.rotor_normal:
        rotor_mode_overwrite = 1
    elif args.rotor_inverted:
        rotor_mode_overwrite = 2

    test.rotor_test_full(args.rotor, args.rotor_usb, rotor_mode_overwrite)

def test_rotor_home(args):
    rotor_mode_overwrite = None
    if args.rotor_normal:
        rotor_mode_overwrite = 1
    elif args.rotor_inverted:
        rotor_mode_overwrite = 2

    test.rotor_home(args.rotor, args.rotor_usb, rotor_mode_overwrite)

def test_radio(args):
    test.test_radio(args.radio, args.downlink, args.uplink, args.rx_usb, args.tx_usb, args.trx_usb)

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

    # common parser for arguments shared between tracking and testing subcommands (argparse is very weird)
    parser_control_common = argparse.ArgumentParser(add_help=False)
    parser_control_common.add_argument("--rotor", type=str, choices=tracking.list_rotors(), dest="rotor",
                              help="The name of a rotor config file (without file extension)")
    parser_control_common.add_argument("--radio", type=str, choices=tracking.list_radios(),
                              help="The name of a radio config file (without file extension)")
    parser_control_common.add_argument("-o", "--rotor_usb", type=str,
                              help="USB port that the rotor is connected to (optional)")
    parser_control_common.add_argument("-n", "--rotor_normal", action="store_true",
                              help="Overwrite the rotor config to use rotor control mode 1")
    parser_control_common.add_argument("-i", "--rotor_inverted", action="store_true",
                              help="Overwrite the rotor config to use rotor control mode 2")
    parser_control_common.add_argument("-r", "--rx_usb", type=str,
                              help="USB port that the receiver is connected to (optional)")
    parser_control_common.add_argument("-t", "--tx_usb", type=str,
                              help="USB port that the transmitter is connected to (optional)")
    parser_control_common.add_argument("-x", "--trx_usb", type=str,
                              help="USB port that the transceiver is connected to (optional)")

    # tracking subcommand
    parser_track = sub_parsers.add_parser("track", help="Track a satellite", parents=[parser_control_common])
    parser_track.add_argument("satellite", help="Either the NORAD ID, COSPAR ID or name of the satellite to be tracked." \
                                                  "TLE must be avaliable in local database.")
    parser_track.add_argument("-u", "--unlock", action="store_true",
                              help="Don't lock uplink and downlink together for satellites with a frequency range.")
    parser_track.set_defaults(func=track)

    # testing subcommands
    parser_test = sub_parsers.add_parser("test", help="Test a rotor or radio", parents=[parser_control_common])
    test_sub = parser_test.add_subparsers(required=True)

    parser_test_rotor = test_sub.add_parser("rotor", help="Test a rotor by moving it a bit or select another rotor test", parents=[parser_control_common])
    parser_test_rotor.set_defaults(func=test_rotor)
    test_rotor_sub = parser_test_rotor.add_subparsers(required=False)

    parser_test_rotor_home = test_rotor_sub.add_parser("home", help="Home a rotor", parents=[parser_control_common])
    parser_test_rotor_home.set_defaults(func=test_rotor_home)

    parser_test_rotor_full = test_rotor_sub.add_parser("full", help="Test a rotor by moving it to various points", parents=[parser_control_common])
    parser_test_rotor_full.set_defaults(func=test_rotor_full)

    parser_test_radio = test_sub.add_parser("radio", help="Test a radio", parents=[parser_control_common])
    parser_test_radio.add_argument("--downlink", type=int,
                              help="Downlink frequency in herz to set the radios to")
    parser_test_radio.add_argument("--uplink", type=int,
                              help="Uplink frequency in herz to set the radios to")
    parser_test_radio.set_defaults(func=test_radio)

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