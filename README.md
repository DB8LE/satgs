# SatGS

SatGS is a command line tool that controls radios and rotors for amateur satellite operation. Currently, the focus is portable operation and making software setup as fast as possible. Once you've configured satgs for your setup, you should be able to take care of your entire software setup by just running one command*.

*Unless you're running an SDR, in which case you have to set up your SDR application too.

**For more info, check out the wiki at <https://satgs.readthedocs.io/>**

## Known bugs

- When settings file hasn't been created yet (usually first run of the program), logging logs everything twice. Once with default format, once with the custom format.
- Geostationary satellites might cause undefined behaviour (?)
