from src import tle, paths, settings, radios, rotors
from skyfield.api import load, wgs84
import logging, os, datetime, time

TRACKING_UPDATE_INTERVAL = int(settings.get_setting("tracking_update_interval")) # Tracking update interval in seconds

def list_rotors() -> list[str]:
    """Return a list of all rotor config file names (excluding file extension)"""
    files = os.listdir(paths.ROTOR_CONFIG_DIRECTORY_PATH)
    files_no_extension = [file[:-5] for file in files]

    return files_no_extension

def list_radios() -> list[str]:
    """Return a list of all radio config file names (excluding file extension)"""
    files = os.listdir(paths.RADIO_CONFIG_DIRECTORY_PATH)
    files_no_extension = [file[:-5] for file in files]

    return files_no_extension

def track(NORAD_ID: str, rotor_config_name: str | None = None, radio_config_name: str | None = None, usb_overwrite: str | None = None):
    if rotor_config_name == None and radio_config_name == None:
        logging.log(logging.ERROR, "Must provide either a radio config, rotor config or both. Not none.")
        exit()

    # Initialize timescale
    timescale = load.timescale()

    # Initialize station position
    station_latitude = settings.get_setting("station_latitude")
    station_longitude = settings.get_setting("station_longitude")
    station_altitude = settings.get_setting("station_altitude")
    station_location = wgs84.latlon(station_latitude, station_longitude, station_altitude)

    # Try to load TLE
    satellite = tle.load_tle(NORAD_ID, timescale)
    if satellite == None:
        logging.log(logging.ERROR, "Failed to load TLE for NORAD "+NORAD_ID+". Not found in local files.")
        exit()
    else:
        if satellite.name == None:
            logging.log(logging.WARN, "Successfully loaded TLE for satellite with NORAD ID "+NORAD_ID+", but satellite name was None.")
        else:
            logging.log(logging.INFO, "Successfully loaded TLE for satellite '"+satellite.name+"'")

    # Calculate time of next pass
    utc_now = datetime.datetime.now(datetime.timezone.utc)
    stop = utc_now + datetime.timedelta(hours=12)
    times, events = satellite.find_events(station_location, timescale.from_datetime(utc_now), timescale.from_datetime(stop))

    earliest_rise_time = None
    try:
        earliest_rise_index = list(events).index(0)
        earliest_rise_time = times[earliest_rise_index]
    except ValueError:
        logging.log(logging.ERROR, "No pass of satellite found within the next 12 hours.")
        exit()

    # Calculate beginnning azimuth of pass
    pos = (satellite - station_location).at(earliest_rise_time)
    _, initial_azimuth, _ = pos.altaz()
    earliest_rise_time = earliest_rise_time.utc_datetime()

    # Notify user
    logging.log(logging.INFO, f"Found next pass at {earliest_rise_time.strftime("%H:%M:%S")} UTC with an initial azimuth of {round(initial_azimuth.degrees)}°") # type: ignore

    # Initialize rotor
    rotor = None
    if rotor_config_name:
        rotor = rotors.Rotor(rotor_config_name, usb_overwrite)
    
    # Initialize radio
    # TODO: radio

    logging.log(logging.INFO, "Ready to start")

    try: # From this point on, catch KeyboardInterrupt or other excpetions and make sure rot/rigctld are terminated and the sockets are closed.
        if rotor:
            logging.log(logging.INFO, "Rotating to starting azimuth")
            initial_azimuth = round(initial_azimuth.degrees) # type: ignore
            rotor.update(initial_azimuth, 0)
            while abs(initial_azimuth-rotor.current_az) > 2: # Only continue when rotor is within 2 degrees of initial azimuth
                rotor.update_current_position()
                time.sleep(0.5)
            logging.log(logging.INFO, "Rotor is at start azimuth")
        
        # Wait for pass to start
        utc_now = datetime.datetime.now(datetime.timezone.utc)
        time_until_pass = earliest_rise_time - utc_now
        seconds_until_pass = time_until_pass.total_seconds()

        if seconds_until_pass > 10:
            if seconds_until_pass > 60:
                logging.log(logging.INFO, f"Waiting for pass to start ({round(seconds_until_pass/60)} min)")
            else:
                logging.log(logging.INFO, f"Waiting for pass to start ({round(seconds_until_pass)}s)")
            time.sleep(seconds_until_pass-10)
            logging.log(logging.INFO, "Pass starting in 10 seconds!")
            time.sleep(10)
        else:
            logging.log(logging.INFO, f"Pass starting in {round(seconds_until_pass)} seconds!")
            time.sleep(seconds_until_pass)

        while True:
            utc_now = datetime.datetime.now(datetime.timezone.utc)

            # Calculate current satellite position
            pos = (satellite - station_location).at(timescale.from_datetime(utc_now))
            elevation, azimuth, _ = pos.altaz()
            azimuth = round(azimuth.degrees) # type: ignore
            elevation = round(elevation.degrees) # type: ignore

            # Log current status to console
            logging.log(logging.INFO, f"AZ: {azimuth}°  EL: {elevation}°")

            # Handle rotor
            if rotor:
                rotor.update(round(azimuth), round(elevation)) # type: ignore
            
            # Wait delay
            time.sleep(TRACKING_UPDATE_INTERVAL)
    except BaseException as e:
        if isinstance(e, KeyboardInterrupt):
            logging.log(logging.INFO, "Caught keyboard interrupt, shutting down subprocesses")
        else:
            logging.log(logging.ERROR, "Caught exception, shutting down subprocesses")
            logging.log(logging.ERROR, e)

        # Shut down rotor socket & rotctld
        if rotor:
            rotor.rotctld.terminate()
            rotor.sock.close() # type: ignore

    # Finished
    logging.log(logging.INFO, "Pass completed!")

    # Close sockets and rxxctlds
    if rotor:
        rotor.rotctld.terminate()
        rotor.sock.close()
