# North- and Southcrossings

North- and Southcrossings are an issue that occur with rotors that have limited movement ranges. For example, imagine a rotor that has 360° with 0° and 360° being north. The rotor can't move through the 0-359° barrier. Instead, it must move 359° around the whole movement range, causing loss of signal for as much as a minute. These barriers can theoretically be anywhere (depending on hardware and software), but usually they're either in the north or south. Satellites passing through the north or south is quite common, and such a long time without any signal is not acceptable. There are a few different solutions to this probblem, which will be discussed in the next section.

## Rotor control modes

Currently, there are two rotor control modes implemented in satgs to help avoid north-/southcrossings.

The first one (mode 1) is the normal mode. This mode just sends the satllites azimuth and elevation straight to the rotor. On most rotors (those that can't move through the 0-359° barrier) this mode will cause northcrossing issues. Even if your rotor supports a broader range, this mode is probably not the right one for you as it will only help you avoid northcrossing issues in one direction.

The second mode (mode 2) sets the center of the supported movement range to act as north. This means you will have to physically move your rotor so the center of the movement range aligns with the real north. On 360° azimuth range rotors, this has the effect of essentially flipping the motion range, meaning that instead of northcrossing problems the rotor will have trouble with southcrossings. If your rotor supports as 540° or larger azimuth motion range, choosing this mode will completely eliminate any north- or southcrossing issues for all (?) satellite passes, as the rotor gets 90° of motion range past the original north / now southcrossing barrier.

There is one more mode that helps to avoid these problems which is not currently implemented. If your rotor supports (at least almost) 180° elevation motion range, you can move the elevation contiuously from either 0-180° or 180-0°. Depending on which of these you choose, it flips the azimuth range that the satellite pass uses by 180°, meaning you can just choose the option where the satellite doesn't pass through the north- or southcrossing barrier. This mode will be implemented in the future.

If you have a portable setup, choosing between mode 1 or 2 depending on the pass will allow you to completely avoid any problems. The only thing your have to do is rotate the rotor 180° yourself, and then pass either the `-n` (normal) or the `-i` (inverted) flag to satgs.
