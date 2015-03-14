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

from . import singleton
from output import outputs

import artnet

@singleton
class ArtnetDmx(object):
    def __init__(self):
        self._ac = artnet.Controller("chromesthesia")
        self.dmx = artnet.port.DMX(direction=artnet.port.DMX.INPUT)
        self._ac.add_port(self.dmx)
        outputs.register_helper(self)

    def after_stop(self):
        self.dmx.reset()
        self.dmx.send()

    def after_update(self):
        self.dmx.send()
        self.dmx.reset()
