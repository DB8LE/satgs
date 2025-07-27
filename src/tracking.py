from src import radio_controller, rotor_controller, tle, paths, settings, transponders
from skyfield.api import load, wgs84
from skyfield.units import Velocity
from typing import List
import logging, os, datetime, time

TRACKING_UPDATE_INTERVAL = float(settings.get_setting("tracking_update_interval")) # Tracking update interval in seconds

def list_rotors() -> List[str]:
    """Return a list of all rotor config file names (excluding file extension)"""
    files = os.listdir(paths.ROTOR_CONFIG_DIRECTORY_PATH)
    files_no_extension = [file[:-5] for file in files]

    return files_no_extension

def list_radios() -> List[str]:
    """Return a list of all radio config file names (excluding file extension)"""
    files = os.listdir(paths.RADIO_CONFIG_DIRECTORY_PATH)
    files_no_extension = [file[:-5] for file in files]

    return files_no_extension

def track(NORAD_ID: str, rotor_config_name: str | None = None, radio_config_name: str | None = None, rotor_usb_overwrite: str | None = None, rx_usb_overwrite: str | None = None, tx_usb_overwrite: str | None = None, trx_usb_overwrite: str | None = None):
    if rotor_config_name == None and radio_config_name == None:
        logging.log(logging.ERROR, "Must provide either a radio config, rotor config or both. Not none.")
        exit()

    # Initialize timescale
    timescale = load.timescale()

    # Initialize station position
    station_latitude = settings.get_setting("station_latitude")
    station_longitude = settings.get_setting("station_longitude")
    station_altitude = settings.get_setting("station_altitude")
    station_location = wgs84.latlon(float(station_latitude), float(station_longitude), float(station_altitude))

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

    # If radio is defined, prompt user to select transponder
    downlink_start = None
    uplink_start = None
    if radio_config_name:
        logging.log(logging.INFO, "Please select which transponder the radio(s) should track:")
        transponder_UUID = transponders.user_transponder_selection(NORAD_ID)
        transponder_frequencies = transponders.get_transponder_frequencies(NORAD_ID, transponder_UUID)
        downlink_lower, downlink_upper, uplink_lower, uplink_upper = transponder_frequencies

        # Set starting frequency to middle of upper and lower downlink frequency if an upper frequency is given
        downlink_start = downlink_lower
        if downlink_upper:
            downlink_start = (downlink_lower + downlink_upper) // 2

        # The same for uplink
        uplink_start = uplink_lower
        if uplink_upper:
            uplink_start = (uplink_lower + uplink_upper) // 2

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
    logging.log(logging.INFO, f"Found next pass at {earliest_rise_time.strftime('%H:%M:%S')} UTC with an initial azimuth of {round(initial_azimuth.degrees)}°") # type: ignore

    # Initialize rotor
    rotor = None
    if rotor_config_name:
        rotor = rotor_controller.Rotor_Controller(rotor_config_name, rotor_usb_overwrite)
    
    # Initialize radio
    radio = None
    if radio_config_name:
        radio = radio_controller.Radio_Controller(radio_config_name, downlink_start, uplink_start, rx_usb_overwrite, tx_usb_overwrite, trx_usb_overwrite)

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
            pos = (satellite - station_location).at(timescale.from_datetime(utc_now))

            # Handle rotor
            rotor_status_msg = ""
            if rotor:
                # Calculate current satellite position
                elevation, azimuth, _ = pos.altaz()
                azimuth = round(azimuth.degrees) # type: ignore
                elevation = round(elevation.degrees) # type: ignore

                # Update rotor position
                rotor.update(round(azimuth), round(elevation)) # type: ignore

                # Generate rotor status message
                rotor_status_msg = f"AZ: {azimuth}°  EL: {elevation}°     "

            # Handle radios
            radio_status_msg = ""
            if radio:
                # Calculate range rate
                _, _, _, _, _, range_rate = pos.frame_latlon_and_rates(station_location)
            
                # Update frequencies
                radio.update(range_rate) # type: ignore

                # Prepare status message
                downlink_message = ""
                uplink_message = ""

                if radio.corrected_downlink:
                    downlink_message = f"D: {str(round(radio.corrected_downlink/1000000, 4))}M"
                if radio.corrected_uplink:
                    uplink_message = f"U: {str(round(radio.corrected_uplink/1000000, 4))}M"

                radio_status_msg = f"{downlink_message} {uplink_message}"

            # Log current status to console
            logging.log(logging.INFO, rotor_status_msg+radio_status_msg)

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
            rotor.sock.close()
            rotor.rotctld.terminate()

        if radio:
            if radio.rx_sock:
                radio.rx_sock.close()
                radio.rx_rigctld.terminate()

    # Finished
    logging.log(logging.INFO, "Pass completed!")

    # Close sockets and rxxctlds
    if rotor:
        rotor.rotctld.terminate()
        rotor.sock.close()
