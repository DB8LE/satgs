from src import paths
import subprocess, os, json, logging, socket

ROTOR_CONF_EXPECTED_KEYS = ["usb_port", "rotctl_ID", "rotctld_port", "min_az", "max_az", "min_el", "max_el", "control_type"]

def parse_rotor_config(rotor_config_name: str) -> dict[str, str | int]:
    """
    Parse a rotor config file by its file name (excluding file exension).
    Returns all values specified in the README section for the rotor config files in a dictionary.
    """
    
    file_path = os.path.join(paths.ROTOR_CONFIG_DIRECTORY_PATH, rotor_config_name+".json")
    try:
        with open(file_path, "r") as f:
            json_data = json.load(f)
    except json.JSONDecodeError as e:
        logging.log(logging.ERROR, "Failed parsing file rotor config file '"+rotor_config_name+".json'.")
        logging.log(logging.ERROR, e)
        exit()

    if type(json_data) != dict:
        logging.log(logging.ERROR, "Failed parsing file rotor config file '"+rotor_config_name+".json'. JSON data parsed to invalid data type.")
        exit()

    if list(json_data.keys()) != ROTOR_CONF_EXPECTED_KEYS:
        logging.log(logging.ERROR, "Failed parsing file rotor config file '"+rotor_config_name+".json'. Invalid keys present in config file.")
        exit()

    return json_data

class Rotor():
    def __init__(self, rotor_config_name, usb_overwrite: str | None = None) -> None:
        """
        Initialize rotor object. Must provide the name of the rotor config file to be read, without the extension.
        Optionally, define a usb port to overwrite the one in the config.
        """
        
        # Parse config
        rotor_config = parse_rotor_config(rotor_config_name)

        self.usb_port = str(rotor_config["usb_port"])
        self.rotctl_ID = str(rotor_config["rotctl_ID"])
        self.rotctld_port = int(rotor_config["rotctld_port"])
        self.min_az = int(rotor_config["min_az"])
        self.max_az = int(rotor_config["max_az"])
        self.min_el = int(rotor_config["min_el"])
        self.max_el = int(rotor_config["max_el"])
        self.control_type = int(rotor_config["control_type"])

        # Check for USB overwrite
        if usb_overwrite:
            self.usb_port = usb_overwrite

        # Attempt to start rotctld
        logging.log(logging.INFO, "Starting rotctld")
        set_conf_arg = "--set-conf=min_az="+str(self.min_az)+",max_az="+str(self.max_az)+",min_el="+str(self.min_el)+",max_el="+str(self.max_el)
        self.rotctld = subprocess.Popen(
            ["rotctld", "-m", str(self.rotctl_ID), "-r", str(self.usb_port), "-t", str(self.rotctld_port), set_conf_arg],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            stdout, stderr = self.rotctld.communicate(timeout=1)
            if self.rotctld.returncode != 0:
                logging.log(logging.ERROR, "Rigctld failed with error code "+str(self.rotctld.returncode))
                logging.log(logging.ERROR, "Error: "+str(stderr))
                if stderr == "rot_open: error = IO error":
                    logging.log(logging.INFO, "Tip: Make sure you have the correct USB port selected." \
                                              "You can overwrite the USB port in the config file using --usb.")
                exit()
            if self.rotctld == None:
                logging.log(logging.ERROR, "Rigctld failed to start.")
        except subprocess.TimeoutExpired: # Rigctld is running
            pass

        logging.log(logging.DEBUG, "Opening socket to rotctld")
        self.sock = socket.create_connection(("localhost", int(self.rotctld_port)), timeout=3)

        self.current_az = None
        self.current_el = None

    def _send_rotctld_command(self, cmd: str):
        """
        Send a command to rotctld and return response lines (without newlines).
        """
        logging.log(logging.DEBUG, f"Sending rotctld command '{cmd}'")
        self.sock.sendall((cmd + '\n').encode('ascii'))
        response = self.sock.recv(4096).decode('ascii')
    
        # multiple lines, strip trailing newline
        return [line.strip() for line in response.splitlines()]
    
    def rotate_to(self, azimuth: int, elevation: int):
        """
        Send rotctld command to spin rotor to a certain azimuth and elevation.
        Automatically sets too low elevations to minmum elevation.
        """
        if elevation < self.min_el:
            elevation = self.min_el

        self._send_rotctld_command(f"P {azimuth} {elevation}")

    def update_current_position(self):
        """
        Get current rotor position and store it in the current_az and current_el variables.
        """
        resp = self._send_rotctld_command("p")
        
        self.current_az = round(float(resp[0]))
        self.current_el = round(float(resp[1]))

    def update(self, new_azimuth: int, new_elevation: int):
        """
        Update rotor movement with new target elevation and azimuth values.
        """
        
        # Read azimuth and elevation
        self.update_current_position()

        self.rotate_to(new_azimuth, new_elevation)
