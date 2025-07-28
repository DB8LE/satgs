from src import paths, util
from typing import Dict
import subprocess, os, json, logging, socket

RADIO_SDR_CONF_EXPECTED_KEYS = ["rigctl_port"]
RADIO_RX_CONF_EXPECTED_KEYS = ["usb_port", "rigctl_ID", "serial_speed", "offset"]
RADIO_TX_CONF_EXPECTED_KEYS = RADIO_RX_CONF_EXPECTED_KEYS

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
    if type(json_data) is not dict:
        logging.log(logging.ERROR, "Failed parsing file radio config file '"+radio_config_name+".json'. JSON data parsed to invalid data type.")
        exit()

    # Make sure that atleast one valid radio type is defined and that the defined ones have the expected keys.
    valid_radio_type_defined = False
    if "sdr" in json_data:
        if list(json_data["sdr"].keys()) != RADIO_SDR_CONF_EXPECTED_KEYS:
            logging.log(logging.ERROR, "Failed parsing file radio config file '"+radio_config_name+".json'. Invalid keys present in SDR section of config file.")
            exit()
        valid_radio_type_defined = True
    
    if "rx" in json_data:
        if list(json_data["rx"].keys()) != RADIO_RX_CONF_EXPECTED_KEYS:
            logging.log(logging.ERROR, "Failed parsing file radio config file '"+radio_config_name+".json'. Invalid keys present in RX section of config file.")
            exit()
        valid_radio_type_defined = True
    
    if "tx" in json_data:
        if list(json_data["tx"].keys()) != RADIO_TX_CONF_EXPECTED_KEYS:
            logging.log(logging.ERROR, "Failed parsing file radio config file '"+radio_config_name+".json'. Invalid keys present in TX section of config file.")
            exit()
        valid_radio_type_defined = True

    # TODO: transceiver

    if not valid_radio_type_defined:
        logging.log(logging.ERROR, "Failed parsing file radio config file '"+radio_config_name+".json'. Couldn't find any valid radio types defined.")

    return json_data

class Radio_Controller():
    def __init__(self, radio_config_name: str, downlink_frequency: int | None, uplink_frequency: int | None, rx_usb_overwrite: str | None, tx_usb_overwrite: str | None, trx_usb_overwrite: str | None) -> None:
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

        if (("tx" in radio_config) or ("trx" in radio_config)) and uplink_frequency is None: # Warn user if a receiver has been defined but no uplink freq was provided
            logging.log(logging.WARN, "Transmitter/Transceiver/SDR is defined in the configuration but no uplink frequency was provided. Transmitters will be ignored.")

        if (("rx" in radio_config) or ("trx" in radio_config)) and downlink_frequency is None: # Warn user if a transmitter has been defined but no downlink freq was provided
            logging.log(logging.WARN, "Receiver/Transceiver is defined in the configuration but no downlink frequency was provided. Receivers will be ignored.")

        if ("tx" in radio_config) and ("rx" in radio_config):
            if radio_config["tx"]["usb_port"] == radio_config["rx"]["usb_port"]:
                logging.log(logging.ERROR, "Defined transmitter and receiver can't be the same device! Try defining a transceiver instead.")
                exit()

        # Initialize SDR if present in config
        if "sdr" in radio_config:
            sdr_config = radio_config["sdr"]
            self.sdr_rigctld_port = int(sdr_config["rigctl_port"])

            # Try to connect to SDR rigctl
            try:
                logging.log(logging.DEBUG, "Opening socket to rigctl (SDR)")
                self.sdr_sock = socket.create_connection(("localhost", int(self.sdr_rigctld_port)), timeout=3)
            except Exception as e:
                logging.log(logging.ERROR, "Failed to open connection to SDR rigctl server. Skipping this radio.")
                logging.log(logging.ERROR, e)
                self.sdr_sock = None
        else:
            self.sdr_sock = None

        # Initialize receiver in config
        if "rx" in radio_config:
            rx_config = radio_config["rx"]
            self.rx_usb_port = rx_usb_overwrite if rx_usb_overwrite else rx_config["usb_port"]
            self.rx_rigctl_ID = rx_config["rigctl_ID"]
            self.rx_serial_speed = rx_config["serial_speed"]
            self.rx_offset = rx_config["offset"]
            self.rx_rigctld_port = util.get_unused_port("rigctld (receiver)")

            # Check if offset and speed are ints
            try:
                self.rx_serial_speed = int(self.rx_serial_speed)
            except ValueError:
                logging.log(logging.ERROR, f"Configured receiver serial speed '{self.rx_serial_speed}' is not a valid integer.")
                exit()
            try:
                self.rx_offset = int(self.rx_offset)
            except ValueError:
                logging.log(logging.ERROR, f"Configured receiver offset '{self.rx_offset}' is not a valid integer.")
                exit()

            # Attempt to start rigctld
            logging.log(logging.INFO, "Starting rigctld (receiver)")
            self.rx_rigctld = subprocess.Popen(
                ["rigctld", "-m", str(self.rx_rigctl_ID), "-r", str(self.rx_usb_port), "-t", str(self.rx_rigctld_port), "-s", str(self.rx_serial_speed)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            try:
                stdout, stderr = self.rx_rigctld.communicate(timeout=1)
                if self.rx_rigctld.returncode != 0:
                    logging.log(logging.ERROR, "Rigctld failed with error code "+str(self.rx_rigctld.returncode))
                    logging.log(logging.ERROR, "Error: "+str(stderr))
                    if stderr == "rig_open: error = IO error":
                        logging.log(logging.INFO, "Tip: Make sure you have the correct USB port selected." \
                                                  "You can overwrite the USB port in the config file using -r")
                    exit()
                if self.rx_rigctld is None:
                    logging.log(logging.ERROR, "Rigctld failed to start.")
            except subprocess.TimeoutExpired: # Rigctld is running
                pass

            # Open socket to rigctld
            try:
                logging.log(logging.DEBUG, "Opening socket to rigctl (receiver)")
                self.rx_sock = socket.create_connection(("localhost", int(self.rx_rigctld_port)), timeout=3)
            except Exception as e:
                logging.log(logging.ERROR, "Failed to open connection to receiver rigctl server. Skipping this radio.")
                logging.log(logging.ERROR, e)
                self.rx_sock = None
        else:
            self.rx_sock = None

        # Initialize transmitter in config (this is the same as the receiver part)
        if "tx" in radio_config:
            tx_config = radio_config["tx"]
            self.tx_usb_port = tx_usb_overwrite if tx_usb_overwrite else tx_config["usb_port"]
            self.tx_rigctl_ID = tx_config["rigctl_ID"]
            self.tx_serial_speed = tx_config["serial_speed"]
            self.tx_offset = tx_config["offset"]
            self.tx_rigctld_port = util.get_unused_port("rigctld (transmitter)")

            # Check if offset and speed are ints
            try:
                self.tx_serial_speed = int(self.tx_serial_speed)
            except ValueError:
                logging.log(logging.ERROR, f"Configured transmitter serial speed '{self.tx_serial_speed}' is not a valid integer.")
                exit()
            try:
                self.tx_offset = int(self.tx_offset)
            except ValueError:
                logging.log(logging.ERROR, f"Configured transmitter offset '{self.tx_offset}' is not a valid integer.")
                exit()

            # Attempt to start rigctld
            logging.log(logging.INFO, "Starting rigctld (transmitter)")
            self.tx_rigctld = subprocess.Popen(
                ["rigctld", "-m", str(self.tx_rigctl_ID), "-r", str(self.tx_usb_port), "-t", str(self.tx_rigctld_port), "-s", str(self.tx_serial_speed)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            try:
                stdout, stderr = self.tx_rigctld.communicate(timeout=1)
                if self.tx_rigctld.returncode != 0:
                    logging.log(logging.ERROR, "Rigctld failed with error code "+str(self.tx_rigctld.returncode))
                    logging.log(logging.ERROR, "Error: "+str(stderr))
                    if stderr == "rig_open: error = IO error":
                        logging.log(logging.INFO, "Tip: Make sure you have the correct USB port selected." \
                                                  "You can overwrite the USB port in the config file using -t")
                    exit()
                if self.tx_rigctld is None:
                    logging.log(logging.ERROR, "Rigctld failed to start.")
            except subprocess.TimeoutExpired: # Rigctld is running
                pass

            # Open socket to rigctld
            try:
                logging.log(logging.DEBUG, "Opening socket to rigctl (transmitter)")
                self.tx_sock = socket.create_connection(("localhost", int(self.tx_rigctld_port)), timeout=3)
            except Exception as e:
                logging.log(logging.ERROR, "Failed to open connection to transmitter rigctl server. Skipping this radio.")
                logging.log(logging.ERROR, e)
                self.tx_sock = None
        else:
            self.tx_sock = None

        # TODO: transceiver

    def _send_rigctl_command(self, sock: socket.socket, cmd: str):
        """
        Send a command to a specified rigctl(d) and return response lines (without newlines).
        """
        logging.log(logging.DEBUG, f"Sending rigctl command '{cmd}'")
        sock.sendall((cmd + '\n').encode('ascii'))
        response = sock.recv(4096).decode('ascii') # if this line fails its probably a config error
    
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

            if self.rx_sock:
                self.set_frequency(self.rx_sock, round(self.corrected_downlink)+self.rx_offset) # type: ignore

        # Handle uplink
        if self.uplink_freq:
            # Calulate corrected frequency
            self.corrected_uplink = -(float(range_rate.km_per_s) / 299792.458) * self.uplink_freq # type: ignore
            self.corrected_uplink += self.uplink_freq

            # Update uplink listeners
            if self.tx_sock:
                print(type(self.corrected_uplink))
                print(type(self.tx_offset))
                self.set_frequency(self.tx_sock, round(self.corrected_uplink)+self.tx_offset) # type: ignore

    def close(self):
        """Close all sockets and terminate rigctl instances"""
        logging.log(logging.DEBUG, "Closing radio controller")

        if self.sdr_sock:
            self.sdr_sock.close()
        
        if self.rx_sock:
            self.rx_sock.close()
            self.rx_rigctld.terminate()

        if self.tx_sock:
            self.tx_sock.close()
            self.tx_rigctld.terminate()
