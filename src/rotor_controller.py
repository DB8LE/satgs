from src import paths, util
from typing import Dict, Tuple
import subprocess, os, json, logging, socket, time

ROTOR_CONF_EXPECTED_KEYS = set(["usb_port", "rotctl_ID", "min_az", "max_az", "min_el", "max_el", "control_type", "home_on_end"])

def parse_rotor_config(rotor_config_name: str) -> Dict[str, str | int]:
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

    if type(json_data) is not dict:
        logging.log(logging.ERROR, "Failed parsing file rotor config file '"+rotor_config_name+".json'. JSON data parsed to invalid data type.")
        exit()

    if set(json_data.keys()) != ROTOR_CONF_EXPECTED_KEYS:
        logging.log(logging.ERROR, "Failed parsing file rotor config file '"+rotor_config_name+".json'. Invalid keys present in config file.")
        exit()

    return json_data

class Rotor_Controller():
    def __init__(self, rotor_config_name: str, usb_overwrite: str | None = None, rotor_mode_overwrite: int | None = None) -> None:
        """
        Initialize rotor object. Must provide the name of the rotor config file to be read, without the extension.
        Optionally, define a usb port to overwrite the one in the config.
        """

        # Parse config
        rotor_config = parse_rotor_config(rotor_config_name)

        self.usb_port = str(rotor_config["usb_port"]) if usb_overwrite is None else usb_overwrite
        self.rotctl_ID = str(rotor_config["rotctl_ID"])
        self.rotctld_port = util.get_unused_port("rotctld")
        self.min_az = int(rotor_config["min_az"])
        self.max_az = int(rotor_config["max_az"])
        self.min_el = int(rotor_config["min_el"])
        self.max_el = int(rotor_config["max_el"])
        self.control_type = int(rotor_config["control_type"]) if rotor_mode_overwrite is None else rotor_mode_overwrite
        self.home_on_end = bool(rotor_config["home_on_end"])

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
                logging.log(logging.ERROR, "Rotctld failed with error code "+str(self.rotctld.returncode))
                logging.log(logging.ERROR, "Error: "+str(stderr))
                if stderr == "rot_open: error = IO error":
                    logging.log(logging.INFO, "Tip: Make sure you have the correct USB port selected." \
                                              "You can overwrite the USB port in the config file using -o")
                exit()
            if self.rotctld is None:
                logging.log(logging.ERROR, "Rotctld failed to start.")
        except subprocess.TimeoutExpired: # Rotctld is running
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
    
    def _apply_control_mode(self, azimuth: int, elevation: int) -> Tuple[int, int]:
        """
        Applies control mode to target azimuth/elevation to get the real position that the rotor needs to spin to.
        """

        if self.control_type == 2:
            azimuth = (round(self.max_az/2) + azimuth) % self.max_az

        return (azimuth, elevation)
    
    def rotate_to(self, azimuth: int, elevation: int):
        """
        Send rotctld command to spin rotor to a certain azimuth and elevation.
        Automatically sets too low elevations to minmum elevation.
        """

        # Clamp elevation value
        if elevation < self.min_el:
            elevation = self.min_el
        elif elevation > self.max_el:
            if self.max_el > 90:
                logging.log(logging.WARN, "Tried to rotate to a too high elevation on a rotor that supports elevations of more than 90°. This is likely due to a bug and will cause issues.")
            elevation = self.max_az

        # Clamp azimuth value
        if azimuth < self.min_az:
            azimuth = self.min_az
        elif azimuth > self.max_az:
            if self.max_az > 360:
                logging.log(logging.WARN, "Tried to rotate to a too high azimuth on a rotor that supports azimuths of more than 360°. This is likely due to a bug and will cause issues.")
            azimuth = self.max_az

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

        # Apply alternate control style if option is set
        new_azimuth, new_elevation = self._apply_control_mode(new_azimuth, new_elevation)

        self.rotate_to(new_azimuth, new_elevation)

    def rotate_to_blocking(self, azimuth: int, elevation: int, tolerance:int = 2):
        """
        Spins the rotor to a certain position and blocks (sleeps) until it has reached the target position.
        Requires target azimuth, elevation, and inaccuracy tolerance in degrees.
        """

        # If alternate control type is used, make sure the correct target azimuth is being checked for
        target_azimuth, target_elevation = self._apply_control_mode(azimuth, elevation)

        # Check if target is in supported rotor range (TODO: in non-blocking rotation this is done silently. Change that?)
        if target_azimuth < self.min_az:
            if abs(target_azimuth - self.min_az) > tolerance:
                logging.log(logging.WARN, f"Target azimuth {target_azimuth} is too far from minimum possible azimuth to be in tolerance. Setting target to closest azimuth possible.")
                target_azimuth = self.min_az
        elif target_azimuth > self.max_az:
            if abs(target_azimuth - self.max_az) > tolerance:
                logging.log(logging.WARN, f"Target azimuth {target_azimuth} is too far from maximum possible azimuth to be in tolerance. Setting target to closest azimuth possible.")
                target_azimuth = self.max_az

        if target_elevation < self.min_el:
            if abs(target_elevation - self.min_el) > tolerance:
                logging.log(logging.WARN, f"Target elevation {target_elevation} is too far from minimum possible elevation to be in tolerance. Setting target to closest elevation possible.")
                target_elevation = self.min_el
        elif target_elevation > self.max_el:
            if abs(target_elevation - self.max_el) > tolerance:
                logging.log(logging.WARN, f"Target elevation {target_elevation} is too far from maximum possible elevation to be in tolerance. Setting target to closest elevation possible.")
                target_elevation = self.min_el

        # Rotate to target location
        self.update(azimuth, elevation)

        # Check if current rotation is within tolerated range of target angles
        while (abs(target_azimuth-self.current_az) > 2) or (abs(target_elevation-self.current_el) > 2): # type: ignore
            self.update_current_position()
            logging.log(logging.DEBUG, f"Rotating to target - AZ {self.current_az} -> {target_azimuth}  EL {self.current_el} -> {target_elevation}")
            time.sleep(0.5)

    def close(self):
        """Close socket and terminate rotctl instance"""
        logging.log(logging.DEBUG, "Closing rotor controller")

        self.sock.close()
        self.rotctld.terminate()

