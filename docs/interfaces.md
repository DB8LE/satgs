# Interfaces

The structure of rotor & radio configuration files described with comments. Note that this isn't valid JSON because of the comments.

Config files are stored in the settings directory inside the rotors and radios folders. You can find the config directory using `$ satgs settings path`.

## Radios

There are multiple radio types you can configure. You can define any combination of these, as long as at least one is defined, and only a maximum of one of each type is defined.

```json
{
    "sdr": {                   // a connection to a rigctld server like the one in SDR++ to serve as a receiver (downlink)
        "rigctl_port": 4532    // port of the rigctl server
    },
    "rx": {                    // a hamlib controlled rig to serve as a receiver (downlink)
        "usb_port": "/dev/ttyUSB0",
        "rigctl_ID": 123,      // rigctl id of your receiver
                               // to find this, run `rigctl --list`
        "serial_speed": 38400, // serial speed of the connection
        "offset": 0            // frequency offset in hz
    },
    "tx": {                    // a hamlib controlled rig to serve as a transmitter (uplink)
        "usb_port": "/dev/ttyUSB0",
        "rigctl_ID": 123,      // rigctl id of your transmitter
                               // to find this, run `rigctl --list`
        "serial_speed": 38400, // serial speed of the connection
        "offset": 0            // frequency offset in hz
    },
    "trx": {                   // a hamlib controlled rig to serve as a transceiver [NOT IMPLEMENTED YET]

    }
}
```

## Rotors

In the config the words north- and southcrossings are refrenced. These are explained in the [North- and Southcrossings section](crossings.md)

!!! note
    In GPredict there is the option to set a rotor type which has its azimuth split as a negative and positive half. I don't really know how these work with rotctl (for example if rigctl can respond with a negative value to the `p` command in this case, or if rigctl shifts the range to the positive area). I still have to research this. Until then, I dont know how these rotors will behave with the program.

```json
{
    "usb_port": "/dev/ttyUSB0", // USB port that the rotor is connected to
                                // this can be overwritten with the -u or --usb command line argument
    "rotctl_ID": 123,           // rotctl ID of your rotor
                                // to find this, run `rotctl --list`
    "min_az": 1,                // minimum azimuth that the rotor is capable of
    "max_az": 359,              // maximum azimuth that the rotor is capable of
    "min_el": 2,                // minimum elevation that the rotor is capable of
    "max_el": 90,               // maximum elevation that the rotor is capable of
    "control_type": 1,          // 1 or 2 are valid values. For more info, check the "Rotor control modes" section
    "home_on_end": true         // home the rotor at the end of a pass. Recommended for portable setups.
                                // Takes control type into consideration, so it will home to whatever the current control types north is.
}
```
