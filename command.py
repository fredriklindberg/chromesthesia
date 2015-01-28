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

import tokenize
import cStringIO

class Command(object):
    storage = {}
    tokens = []
    name = ''
    parent = None

    def __init__(self):
        self._commands = {}

    def add(self, command):
        if command.name in self._commands:
            return False
        self._commands[command.name] = command
        command.parent = self
        command.storage = self.storage

        return True

    def _get_command(self):
        if not self.parent:
            return ""

        parent = self.parent._get_command()
        if parent:
            return "{:s} {:s}".format(parent, self.name)
        else:
            return self.name

    def _tokenize(self, string):
        tokens = []
        src = cStringIO.StringIO(string).readline
        for (type, value, _, _, _) in tokenize.generate_tokens(src):
            if type == tokenize.ENDMARKER:
                break
            elif type == tokenize.NAME:
                type = tokenize.STRING
            elif type == tokenize.STRING:
                value = value[1:-1].decode("string-escape")

            tokens.append((type, value))
        return tokens

    def hints(self):
        return []

    def match(self, text, hints=False):
        tokens = self._tokenize(text)

        if self._commands:
            list = self._commands.keys()
        else:
            list = self.hints()

        if len(tokens) <= 0:
            if self._commands or hints:
                return list
            else:
                return []

        token = tokens[0][1]
        if token in self._commands:
            next_str = " ".join(map(lambda x: x[1], tokens[1:]))
            return self._commands[token].match(next_str, hints)

        return sorted(filter(lambda x: x.startswith(token), list))

    def parse(self, str=None):
        if str != None:
            tokens = self._tokenize(str)
        else:
            tokens = self.tokens

        if len(tokens) <= 0:
            return False

        cmd_name = tokens[0][1]
        self.tokens = tokens[1:]
        if not cmd_name in self._commands:
            return False
        self._commands[cmd_name].tokens = self.tokens
        return self._commands[cmd_name].execute()

    def execute(self):
        return self.parse()

class CmdBranch(Command):
    def __init__(self, name):
        super(CmdBranch, self).__init__()
        self.name = name

command_root = Command()
