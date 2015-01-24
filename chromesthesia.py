#!/usr/bin/env python
# Copyright (C) 2013 Fredrik Lindberg <fli@shapeshifter.se>
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
import time
from optparse import OptionParser
from ConfigParser import SafeConfigParser
from sound import SoundAnalyzer
from light import *

import numpy as np

def get_cfg_int(config, section, variable, default):
    try:
        val = config.getint(section, variable)
    except Exception as e:
        print e
        val = default
    return val

def get_cfg_list(config, section, variable, default):
    try:
        str = config.get(section, variable)
        val = map(lambda x: int(x), str.split())
    except Exception as e:
        print e
        val = default
    return val

def main(args):
    parser = OptionParser(usage="%prog [options] <config file>")
    parser.add_option("-d", dest="debug",
                  default=False, action="store_true",
                  help="Debug output (very verbose)")

    (opts, args) = parser.parse_args()

    if len(args) == 0:
        parser.error("Configuration missing")

    config = SafeConfigParser()
    try:
        config.read(args[0])
    except Exception as e:
        print e
        return 1

    sample = get_cfg_int(config, "global", "sample", 20000)
    chunk = get_cfg_int(config, "global", "chunk", 160)

    lights = []
    i = 1
    while True:
        name = "light" + str(i)
        i = i + 1
        if not config.has_section(name):
            break
        chan = get_cfg_int(config, name, "channel", -1)
        if chan == -1:
            continue
        if not config.has_option(name, "type"):
            continue
        type = config.get(name, "type")

        l = Light.factory(type)
        if not l:
            continue
        l.channel = chan
        lights.append(l)

    sa = SoundAnalyzer(sample, chunk)
    sa.start()

    try:
        while True:
            data = sa.data()

            bass = data["bins"]["bass"]["level"]
            mid = data["bins"]["mid"]["level"]
            treble = data["bins"]["tre"]["level"]

            if opts.debug:
                print "Bass: {:.3f}, Mid: {:.3f}, Treble: {:.3f}".\
                    format(bass, mid, treble)

    except KeyboardInterrupt:
        pass

    sa.stop()

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
