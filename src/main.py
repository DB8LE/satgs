from src import custom_logging, arguments

def main():
    # Set up logging
    custom_logging.set_up_logging()

    # Set up argument parsing and parse args
    arguments.set_up_argparse()