# Copyright (C) 2015 Fredrik Lindberg <fli@shapeshifter.se>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA

# Rolling moving average
class RMA(object):
    def __init__(self, size):
        self._size = int(size)
        self._index = 0
        self._sum = 0
        self._fill = 0
        self._average = 0.0
        self._a = [0] * self._size

    def add(self, value):
        self._sum = self._sum - self._a[self._index]
        self._a[self._index] = value
        self._sum = self._sum + value
        self._fill = min(self._size, self._fill + 1)
        self._average = float(self._sum / self._fill)
        self._index = (self._index + 1) % self._size

    def value(self):
        return self._average
