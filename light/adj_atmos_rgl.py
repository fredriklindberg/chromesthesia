# Copyright (C) 2013 Fredrik Lindberg <fli@shapeshifter.se>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

#
# Light generation for American DJ Atmospheric RG LED laser
#

from . import *
import random
import math

class AdjAtmosRGL(Light):

    # Red is a slow moving laser
    # Green is a fast moving laser
    # Blue is a waterfall LED
    #
    # Channel 1 Color
    #   0-7   Off
    #   8-37  Red
    #  38-67  Red & Green
    #  68-97  Green
    #  98-127 Green & Blue
    # 128-157 Blue
    # 158-187 Red & Blue
    # 188-217 Red & Green & Blue
    #
    # Channel 2 Rotation
    #   0-9   No rotation
    #  10-120 Counter-clockwise, fast -> slow
    # 121-134 No rotation
    # 135-245 Clockwise, slow -> fast

    data = [0, 0]
    speed = 0
    clockwise = True

    no_beat = 0

    RED = 0x1
    GREEN = 0x2
    BLUE = 0x4

    colormap = {
        0x0: 0,
        RED: 8,
        RED | GREEN: 38,
        GREEN: 68,
        GREEN | BLUE: 98,
        BLUE: 128,
        RED | BLUE: 158,
        RED | GREEN | BLUE: 188
    }

    prev_mid = 0
    no_beat = 0

    def update(self, is_beat, base, mid, treble):

        self.no_beat = self.no_beat + 1 if not is_beat else 0

        if is_beat or base >= 240:
            self.data[0] |= self.RED
        else:
            self.data[0] &= ~self.RED

        mid_delta = mid - self.prev_mid
        # Stribe green based on midrange activty if
        # there is no distinctive bass beat.
        if self.no_beat > 10:
            if mid_delta >= 50 or mid >= 120:
                self.data[0] |= self.GREEN
            else:
                self.data[0] &= ~self.GREEN
        else:
            if mid >= 90:
                self.data[0] |= self.GREEN
            elif mid <= 40:
                self.data[0] &= ~self.GREEN

        if (mid >= 1 and mid <= 40) or (base <= 10 and treble >= 10):
            self.data[0] |= self.BLUE
        elif (mid == 0 and treble == 0) or mid >= 80:
            self.data[0] &= ~self.BLUE

        # Try to do some exponential speed up for the rotation
        speed = int((pow(mid, 1.5) / pow(256, 1.5)) * 110)
        if self.clockwise:
            self.data[1] = 135 + speed
        else:
            self.data[1] = abs(speed - 110) + 10

        self._port.set(self.channel, self.colormap[self.data[0]])
        self._port.set(self.channel + 1, self.data[1])

        # Select a new random rotation when silent
        if self.data[0] == 0:
            self.clockwise = True if random.randint(0,1) else False

        self.prev_mid = mid 
