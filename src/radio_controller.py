from src import paths
from typing import Dict
import subprocess, os, json, logging, socket

RADIO_SDR_CONF_EXPECTED_KEYS = ["rigctl_port"]

def parse_radio_config(radio_config_name: str) -> Dict[str, Dict[str, str | int]]:
    """
    Parse a radio config file by its file name (excluding file exension).
    Returns all values specified in the README section for the radio config files in a dictionary.
    """
    
    # Try to read and parse JSON data
    file_path = os.path.join(paths.RADIO_CONFIG_DIRECTORY_PATH, radio_config_name+".json")
    try:
        with open(file_path, "r") as f:
            json_data = json.load(f)
    except json.JSONDecodeError as e:
        logging.log(logging.ERROR, "Failed parsing file radio config file '"+radio_config_name+".json'.")
        logging.log(logging.ERROR, e)
        exit()

    # Checks to see if data is valid
    if type(json_data) != dict:
        logging.log(logging.ERROR, "Failed parsing file radio config file '"+radio_config_name+".json'. JSON data parsed to invalid data type.")
        exit()

    # Make sure that atleast one valid radio type is defined and that the defined ones have the expected keys.
    valid_radio_type_defined = False
    if "sdr" in json_data:
        if list(json_data["sdr"].keys()) != RADIO_SDR_CONF_EXPECTED_KEYS:
            logging.log(logging.ERROR, "Failed parsing file radio config file '"+radio_config_name+".json'. Invalid keys present in SDR section of config file.")
            exit()
        valid_radio_type_defined = True

    # TODO: Other types

    if valid_radio_type_defined == False:
        logging.log(logging.ERROR, "Failed parsing file radio config file '"+radio_config_name+".json'. Couldn't find any valid radio types defined.")

    return json_data

class Radio_Controller():
    def __init__(self, radio_config_name: str, downlink_frequency: int | None, uplink_frequency: int | None) -> None:
        """
        Initialize radio object. Must provide the name of the radio config file to be read (without the file extension),
        and optionally the downlink and uplink frequency of the satellite transponder.
        """
        
        self.downlink_freq = downlink_frequency
        self.uplink_freq = uplink_frequency

        self.corrected_downlink = None
        self.corrected_uplink = None

        # Parse config
        radio_config = parse_radio_config(radio_config_name)

        if (("tx" in radio_config) or ("trx" in radio_config)) and uplink_frequency == None: # Warn user if a receiver has been defined but no downlink freq was provided
            logging.log(logging.WARN, "Receiver/Transceiver/SDR is defined in the configuration but no uplink frequency was provided. Receivers will be ignored.")

        if (("tx" in radio_config) or ("trx" in radio_config)) and uplink_frequency == None: # Warn user if a transmitter has been defined but no uplink freq was provided
            logging.log(logging.WARN, "Transmitter/Transceiver is defined in the configuration but no uplink frequency was provided. Transmitters will be ignored.")

        if "sdr" in radio_config:
            sdr_config = radio_config["sdr"]
            self.sdr_rigctl_port = int(sdr_config["rigctl_port"])

            try:
                logging.log(logging.DEBUG, "Opening socket to rotctld")
                self.sdr_sock = socket.create_connection(("localhost", int(self.sdr_rigctl_port)), timeout=3)
            except Exception as e:
                logging.log(logging.ERROR, "Failed to open connection to SDR rigctl server. Skipping this radio.")
                logging.log(logging.ERROR, e)
                self.sdr_sock = None

    def _send_rigctl_command(self, sock: socket.socket, cmd: str):
        """
        Send a command to a specified rigctl(d) and return response lines (without newlines).
        """
        logging.log(logging.DEBUG, f"Sending rigctl command '{cmd}'")
        sock.sendall((cmd + '\n').encode('ascii'))
        response = sock.recv(4096).decode('ascii')
    
        # multiple lines, strip trailing newline
        return [line.strip() for line in response.splitlines()]

    def set_frequency(self, sock: socket.socket, freq: int):
        """
        Send a rigctl(d) command to a specified socket to change the rig frequency. Frequency must be in herz.
        """

        self._send_rigctl_command(sock, f"F {freq}")

    def update(self, range_rate: float):
        """
        Update all defined transmitters/receivers with the satellites range rate.
        """

        # Handle downlink
        if self.downlink_freq:
            # Calulate corrected frequency
            self.corrected_downlink = -(float(range_rate.km_per_s) / 299792.458) * self.downlink_freq # type: ignore
            self.corrected_downlink += self.downlink_freq

            # Update downlink listeners
            if self.sdr_sock:
                self.set_frequency(self.sdr_sock, self.corrected_downlink) # type: ignore

        if self.uplink_freq:
            # Calulate corrected frequency
            self.corrected_uplink = -(float(range_rate.km_per_s) / 299792.458) * uplink_start # type: ignore
            self.corrected_uplink += self.downlink_freq

            # Update uplink listeners
            # ..
