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

class Light(object):
    _lights = {
        "adj_atmospheric_rgl" : "AdjAtmosRGL"
    }

    @staticmethod
    def lights():
        return map(lambda x: x[0], Light._lights.iteritems())

    @staticmethod
    def factory(type):
        if type in Light._lights:
            return eval(Light._lights[type])()
        return None

    def update(self, is_beat, base, mid, treble):
        return None

    @property
    def port(self):
        return self._port
    @port.setter
    def port(self, value):
        self._port = value

    @property
    def channel(self):
        return self._channel
    @channel.setter
    def channel(self, value):
        self._channel = value

from adj_atmos_rgl import *
