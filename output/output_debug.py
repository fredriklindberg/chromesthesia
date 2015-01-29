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

alias = "debug"
name = "Debug"
desc = "Prints raw data"

class Output(object):
    def __init__(self):
        pass

    def update(self, data):
        for bin in "bass", "mid", "tre":
            print "{:s}: l:{:.3f} f:{:.3f} t:{:.3f} ".format(bin,
                data["bins"][bin]["level"],
                data["bins"][bin]["flux"],
                data["bins"][bin]["transient"]
            ),
        print ""
