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

from command import Command, command_root

def singleton(cls):
    instances = {}
    def getinstance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return getinstance

@singleton
class Settings(object):
    _settings = {}

    def create(self, key, value=""):
        self._settings[key] = value

    def __getitem__(self, key):
        if key in self._settings:
            return self._settings[key]
        else:
            raise AttributeError("No such setting " + key)

    def __setitem__(self, key, val):
        if key in self._settings:
            self._settings[key] = val
        else:
            raise AttributeError("No such setting " + key)

class CmdSet(Command):
    def __init__(self):
        super(CmdSet, self).__init__()
        self.name = "set"
    def execute(self):
        tokens = self.tokens
        if len(tokens) % 3:
            raise Command.SyntaxError(
                "Supply settings on the format key=value")

        tokens = iter(tokens)
        tokens = zip(tokens, tokens, tokens)
        settings = {}
        for ((key_t,key), (_,sep), (_,value)) in tokens:
            if sep != "=":
                raise Command.SyntaxError(
                    "Settings should be supplied on the format key=value")
            if key_t != str:
                raise Command.SyntaxError(
                    "Key must be a string")

            settings[key] = value

        lines = []
        for setting in settings:
            try:
                Settings()[setting] = settings[setting]
                line = setting + " = " + str(settings[setting]) + ", ok"
                lines = lines + [line]
            except AttributeError as e:
                line = setting + " = " + str(settings[setting]) + ", " + str(e)
                lines = lines + [line]
        return lines

class CmdGet(Command):
    def __init__(self):
        super(CmdGet, self).__init__()
        self.name = "get"
    def execute(self):
        if len(self.tokens) < 1:
            tokens = map(lambda x: ("", x), list(Settings()._settings.keys()))
        else:
            tokens = self.tokens

        lines = []
        for (key_t, key) in tokens:
            try:
                lines = lines + [key + " = " + str(Settings()[key])]
            except AttributeError as e:
                raise Command.NotFound(str(e))
        return lines
