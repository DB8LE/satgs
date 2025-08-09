from src import radio_controller, rotor_controller
import logging, time

def rotor_home(rotor_config_name: str, usb_overwrite: str | None = None, rotor_mode_overwrite: int | None = None):
    """A testing function to home a rotor to north"""

    logging.log(logging.INFO, "Initializing rotor")
    rotor = rotor_controller.Rotor_Controller(rotor_config_name, usb_overwrite, rotor_mode_overwrite)

    logging.log(logging.INFO, "Homing rotor..")
    rotor.rotate_to_blocking(0, 0) # This might output warnings with strange rotor limits
    logging.log(logging.INFO, "Done")

    rotor.close()

def rotor_test(rotor_config_name: str, usb_overwrite: str | None = None, rotor_mode_overwrite: int | None = None):
    """A test function to rotate a rotor slightly to check if it's working properly"""

    logging.log(logging.INFO, "Initializing rotor")
    rotor = rotor_controller.Rotor_Controller(rotor_config_name, usb_overwrite, rotor_mode_overwrite)

    rotor.update_current_position()
    start_azimuth: int = rotor.current_az # type: ignore
    start_elevation: int = rotor.current_el # type: ignore

    # Check if rotor is in safe range and if it is spin 10° in in each direction
    if start_elevation+10 < rotor.max_el:
        logging.log(logging.INFO, "Rotating 10° up")
        rotor.rotate_to_blocking(start_azimuth, start_elevation+10)
        rotor.rotate_to_blocking(start_azimuth, start_elevation)
    else:
        logging.log(logging.INFO, "Not rotating 10° up to not go out of possible range.")
    
    if start_elevation-10 > rotor.min_el:
        logging.log(logging.INFO, "Rotating 10° down")
        rotor.rotate_to_blocking(start_azimuth, start_elevation-10)
        rotor.rotate_to_blocking(start_azimuth, start_elevation)
    else:
        logging.log(logging.INFO, "Not rotating 10° down to not go out of possible range.")
    
    if start_azimuth+10 < rotor.max_az:
        logging.log(logging.INFO, "Rotating 10° clockwise")
        rotor.rotate_to_blocking(start_azimuth+10, start_elevation)
        rotor.rotate_to_blocking(start_azimuth, start_elevation)
    else:
        logging.log(logging.INFO, "Not rotating 10° clockwise to not go out of possible range.")

    if start_azimuth-10 > rotor.min_az:
        logging.log(logging.INFO, "Rotating 10° counterclockwise")
        rotor.rotate_to_blocking(start_azimuth-10, start_elevation)
        rotor.rotate_to_blocking(start_azimuth, start_elevation)
    else:
        logging.log(logging.INFO, "Not rotating 10° counterclockwise to not go out of possible range.")

    rotor.close()

def rotor_test_full(rotor_config_name: str, usb_overwrite: str | None = None, rotor_mode_overwrite: int | None = None):
    """A test function to rotate a rotor to a few different points to evaluate possible issues at rotor limits"""

    logging.log(logging.INFO, "Initializing rotor")
    rotor = rotor_controller.Rotor_Controller(rotor_config_name, usb_overwrite, rotor_mode_overwrite)

    max_az = rotor.max_az
    min_az = rotor.min_az
    max_el = rotor.max_el
    min_el = rotor.min_el
    el_third = max_el / 3

    TEST_POINTS = [(min_az, min_el), (max_az/2, el_third), (max_az, el_third*2), (min_az, max_el), (min_az, min_el)]

    for i, (az, el) in enumerate(TEST_POINTS):
        az = round(az)
        el = round(el)
        logging.log(logging.INFO, f"Rotating to point {i+1}/{len(TEST_POINTS)} - AZ {az} EL {el}")
        rotor.rotate_to_blocking(az, el)
    logging.log(logging.INFO, "Done")

    rotor.close()

def test_radio(radio_config_name: str, downlink_frequency: int | None, uplink_frequency: int | None, rx_usb_overwrite: str | None, tx_usb_overwrite: str | None, trx_usb_overwrite: str | None):
    """A test function to set a radio to a certain frequency (specified in herz)"""

    logging.log(logging.INFO, "Initializing radio")
    radio = radio_controller.Radio_Controller(radio_config_name, downlink_frequency, uplink_frequency, rx_usb_overwrite, tx_usb_overwrite, trx_usb_overwrite)
    
    logging.log(logging.INFO, "Updating frequency")
    radio.update(0)

    logging.log(logging.INFO, "Entering lock update loop. Press ctrl+C to exit.")
    try:
        while True:
            radio.update_lock()
            radio.update(0)
            time.sleep(1)
    except Exception:
        radio.close()
