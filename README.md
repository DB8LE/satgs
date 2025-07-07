# SatGS

SatGS is a command line tool that controls radios and rotors for amateur satellite operation. Currently, the focus is portable operation and making software setup as fast as possible. Once you've configured satgs for your setup, you should be able to take care of your entire software setup by just running one command*.

*Unless you're running an SDR, in which case you have to set up your SDR application too.

## Installation

First, [install pipx](https://pipx.pypa.io/latest/installation/). Then run:

`$ pipx install git+https://github.com/DB8LE/satgs`

Now satgs should be installed and accessible by running `satgs` in your command line.

## Configuration files

The structure of rotor & radio configuration files described with comments. Note that this isn't valid JSON because of the comments.

### Rotor

In the config I reference "north crossings" and "south crossings". This is the word I came up with for the issue that occurs when the satellite pass crosses a region that your rotor can't pass through, so the rotor has to rotate 360° to continue the pass, which causes a lot of time without signal, depending on your motor speed. This point will be either north or south for most normal rotors. I do not know if there's already a word for this, it's just what made sense to me. There are two main ways to get of this issue completely. Method one is having an elevation that is limited from 0-180° (or a bit less), which even works with an azimuth limit of 0-360° (or a bit less). If your rotor is limited to 170° or less maximum elevation because of antenna mounting or some other reason, the only other way is to have an azimuth range of 1-539 or larger. This allows you to set your north to the middle of the maximum and minimum azimuth values, and rotating from there. Technically there is another way with 1-359° az and 1-90° el limits tho. You can apply a virtual offset, and then physically rotate your rotor to match that. This limits your azimuth range more, so you have to adjust it for every pass (depending on north or south crossing and crossing direction). This offset feature will be implemented in the future.

Note: In GPredict there is the option to set a rotor type which has its azimuth split as a negative and positive half. I don't really know how these work with rotctl (for example if rigctl can respond with a negative value to the `p` command in this case, or if rigctl shifts the range to the positive area). I still have to research this. Until then, I dont know how these rotors will behave with the program.

Note 2: Support for rotors that communicate with rotctl over anything other than USB () also aren't supported yet, I don't know how rotctl handles these either.

```json
{
    "usb_port": "/dev/ttyUSB0", // usb port that the rotor is connected to
                                // this can be overwritten with the -u or --usb command line argument
    "rotctl_ID": 123, // rotctl id of your rotor
                     // to find this, run `rotctl --list`
    "rotctld_port": 4533, // port for rotctld. make sure this doesn't share a port with any
                          // rigctld instances.
    "min_az": 1, // minimum azimuth that the rotor is capable of
    "max_az": 359, // maximum azimuth that the rotor is capable of
    "min_el": 2, // minimum elevation that the rotor is capable of
    "max_el": 180, // maximum elevation that the rotor is capable of
    "control_type": 1 // mode 1: A normal classic control style that sets 0° to north. 
                      // If your rotor supports the range 0-539° or smaller, you will probably want to use this.
                      // However, if your rotor supports more, this is the wrong choice, as you could potenitally be eliminating
                      // north crossing problems in more directions than just one with the other mode.
                      // mode 2: This control style sets north to the middle of your max and min azimuth.
                      // if your rotor supports 0-539° this essentially only has the effect of inverting your crossing issue point, 
                      // and you needing to point your rotor north in the opposite direction. If your rotor supports up to 540° of 
                      // azimuth or more, this mode will eliminate all south or north crossing problems. Unless you're tracking 
                      // some really weird orbit that has both a north and south crossing.
                      // (MODE 2 NOT IMPLEMENTED YET)
}
```

### Radio

```json
{}
```

## Known bugs

- When settings file hasn't been created yet (usully first run of the program), logging logs everything twice. Once with default format, once with the custom format.
