# Welcome to SatGS's documentation

## Installation

To install satgs first [install pipx](https://pipx.pypa.io/latest/installation/) and make sure you have hamlib (rigctld and rotctld) installed.

Then run: `$ pipx install git+https://github.com/DB8LE/satgs`

SatGS should now be accessible in your commandline by running `satgs`

The first things you should do are:

1. Update TLE and transponder data using `$ satgs update`
2. Configure your location using `$ satgs settings modify <station_latitude, station_longitude or station_altitude> <value>`

## Updating

Before updating, you might have to reset your config files to prevent problems. Simply backup your custom configuration files, wipe your config, update, and then check if anything has changed in the config format by looking at the new example config files or the wiki. When you're ready, wipe your settings with `$ satgs settings clean`.

Then, simply run `$ pipx upgrade satgs`. Remember to update your TLEs and set your station location again after updating.

## Basic usage

You can track a satellite by using `$ satgs track <some satellite>` and then adding `--rotor` and `--radio` flags followed by your [config file](interfaces.md) name.

To get more info on available commands and options, run `$ satgs --help`. You can also get info by adding --help to any subcommand. For example: `$ satgs track --help`.
