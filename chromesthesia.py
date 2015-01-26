#!/usr/bin/env python
# Copyright (C) 2013-2015 Fredrik Lindberg <fli@shapeshifter.se>
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

#
# chromesthesia
#   a form of synesthesia in which nonvisual stimulation
#   results in the experience of color sensations.
#
# chromesthesia is a realtime sound visualizer that can generate
# real life physical light shows as well as digital on-screen visuals.

import sys
import output
import console
from sound import Sound
from command import Command, command_root

class CmdStart(Command):
    name = "start"
    def execute(self):
        if "sound" in self.storage:
            return ["Sound processing already running"]
        self.storage["sound"] = Sound()
        self.storage["sound"].start()

class CmdStop(Command):
    name = "stop"
    def execute(self):
        if not "sound" in self.storage:
            return ["Sound processing not running"]
        self.storage["sound"].running.clear()
        del self.storage["sound"]

def main(args):
    command_root.add(CmdStart())
    command_root.add(CmdStop())
    cons = console.Console()
    cons.set_prompt("chromesthesia> ")
    cons.start()

    try:
        cons.join()
        command_root.parse("stop")
    except:
        pass

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
