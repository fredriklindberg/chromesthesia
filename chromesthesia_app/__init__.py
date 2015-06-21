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

import sys
import os
import argparse

sys.path.append(os.path.dirname(__file__))
import log

parser = argparse.ArgumentParser()
parser.add_argument("-v", action="append_const",
                    dest="verbose", const=True, default=[],
                    help="Verbose, specify twice for more verbosity")
config = parser.parse_args()
config.verbose = len(config.verbose)
config.verbose = config.verbose if config.verbose <=2 else 2

# Set debug level early to catch package initialization outputs
if config.verbose >= 1:
    log.Logger().add_level(log.DEBUG)
if config.verbose >= 2:
    log.Logger().add_level(log.DEBUG2)

import chromesthesia

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
