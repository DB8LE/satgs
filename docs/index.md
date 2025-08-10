# Welcome to SatGS's documentation

## Installation

To install satgs, you will first need to have python 3.10 or newer and hamlib (rigctld and rotctld) installed.

To install on windows, simply run `$ pip install satgs` in the terminal.

On other operating systems, use [pipx](https://pipx.pypa.io/latest/installation/) to install by running `$ pipx install satgs`.

The first things you should do after installing satgs are:

1. Update TLE and transponder data using `$ satgs update`
2. Configure your location using `$ satgs settings modify <station_latitude, station_longitude or station_altitude> <value>`

## Updating

Before updating, you might have to reset your config files to prevent problems. Simply backup your custom configuration files, wipe your config, update, and then check if anything has changed in the config format by looking at the new example config files or the wiki. When you're ready, wipe your settings with `$ satgs settings clean`.

Then, run either `$ pip install satgs --upgrade` or `$ pipx upgrade satgs` based on which installation method you used. Remember to update your TLEs and set your station location again if you wiped your settings before updating.

## Basic usage

You can track a satellite by using `$ satgs track <some satellite>` and then adding `--rotor` and `--radio` flags followed by your [config file](interfaces.md) name.

To get more info on available commands and options, run `$ satgs --help`. You can also get info by adding --help to any subcommand. For example: `$ satgs track --help`.
