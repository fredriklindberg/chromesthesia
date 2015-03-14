# Copyright (C) 2015 Fredrik Lindberg <fli@shapeshifter.se>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

# Red is a slow moving laser
# Green is a fast moving laser
# Blue is a waterfall LED
#
# Requires two channels
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

import math
import random

import helpers

alias = "adj_atmos_rgl"
name = "American DJ Atmospheric RG LED"
desc = name

config = {
    "channel" : {
        "type" : int,
        "default" : 1,
        "help" : "DMX channel to use, will use the channel above aswell"
    }
}

class Output(object):

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

    clockwise = True

    def __init__(self, config):
        self._color_channel = config["channel"]
        self._rotation_channel = config["channel"] + 1
        self._helper = helpers.ArtnetDmx()

    def update(self, data, dt):
        if data["silence"]:
            self._helper.dmx.set(self._color_channel, 0)
            self._helper.dmx.set(self._rotation_channel, 0)
            self.clockwise = True if random.randint(0,1) else False
            return

        color = 0

        if data["bins"]["bass"]["transient"] > 0:
            color |= self.RED

        if data["bins"]["mid"]["level"] >= 0.20:
            color |= self.GREEN

        if color == 0:
            color |= self.BLUE

        mid = data["bins"]["mid"]["level"] * 100
        speed = int((pow(mid, 2.0) / pow(100, 2.0)) * 55)
        if self.clockwise:
            rotation = 135 + speed + 55
        else:
            rotation = abs(speed - 110) + 10 + 55

        self._helper.dmx.set(self._color_channel, self.colormap[color])
        self._helper.dmx.set(self._rotation_channel, rotation)

