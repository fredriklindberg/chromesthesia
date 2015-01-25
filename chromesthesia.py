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
# chromesthesia is a realtime sound analyzer and semi-beat detection
# system that generates DMX output to light rigs based on sound.

import sys
import output
from sound import SoundAnalyzer

def main(args):

    outputs = output.Outputs()
    outputs.enable("debug")

    sa = SoundAnalyzer(44100, 60)
    sa.start()

    try:
        while True:
            data = sa.data()
            outputs.update(data)

    except KeyboardInterrupt:
        pass

    sa.stop()

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
