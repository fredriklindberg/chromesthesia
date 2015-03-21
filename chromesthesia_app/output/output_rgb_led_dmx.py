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

import helpers

alias = "rgb_led_dmx"
name = "DMX controlled RGB LED strip"
desc = name

config = {
    "channel" : {
        "type" : int,
        "default" : 1,
        "values" : range(1, 512),
        "help" : "Base DMX channel, requires 3 channels"
    },
    "mode" : {
        "type" : str,
        "default" : "mix",
        "values" : ["mix", "beat", "level"]
    },
    "red" : {
        "type" : str,
        "default" : "bass",
        "values" : ["bass", "mid", "tre"]
    },
    "green" : {
        "type" : str,
        "default" : "mid",
        "values" : ["bass", "mid", "tre"]
    },
    "blue" : {
        "type" : str,
        "default" : "tre",
        "values" : ["bass", "mid", "tre"]
    },
}

class Output(object):
    def __init__(self, config):
        self._helper = helpers.ArtnetDmx()

        self._mode = config["mode"]
        self._channels = {
            "red" : config["channel"],
            "green" : config["channel"] + 1,
            "blue" : config["channel"] + 2
        }
        self._src = {
            "red" : config["red"],
            "green" : config["green"],
            "blue" : config["blue"]
        }

        self._level = 0

    def update(self, data, dt):
        if data["silence"]:
            return

        for src in self._src:
            d = data["bins"][self._src[src]]
            trans = int(d["transient"] * 255)
            self._level = (self._level + d["level"]) / 2
            level = int(self._level * 255)

            if trans > 0 and self._mode in ["beat", "mix"]:
                color = trans
            elif self._mode in ["level", "mix"]:
                color = level
            else:
                color = 0

            self._helper.dmx.set(self._channels[src], color)
