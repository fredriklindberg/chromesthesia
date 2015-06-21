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

import os
import sys

from settings import Settings

def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

INFO = 0x01
WARN = 0x02
ERROR = 0x04
DEBUG = 0x08
DEBUG2 = 0x10

@singleton
class Logger(object):
    _log_fd = sys.stdout.fileno()
    _levels = {
        "info"   : INFO,
        "warn"   : WARN,
        "error"  : ERROR,
        "debug"  : DEBUG,
        "debug2" : DEBUG2,
    }
    _level = INFO + WARN + ERROR

    def set_output(self, fd):
        self._log_fd = fd

    def add_level(self, level):
        self._level = self._level | (level)

    def del_level(self, level):
        self._level = self._level & ~(level)

    def _output(self, level, message):
        if self._levels[level] & self._level:
            if self._log_fd == sys.stdout.fileno():
                message = message + "\n"
            os.write(self._log_fd, bytes(message, "UTF-8"))

    def info(self, message):
        self._output("info", message)

    def warn(self, message):
        self._output("warn", message)

    def error(self, message):
        self._output("error", message)

    def debug(self, message):
        self._output("debug", message)

    def debug2(self, message):
        self._output("debug2", message)
