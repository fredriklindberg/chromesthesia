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
import readline
from threading import Thread, Event
from command import Command, command_root

class Console(Thread):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Console, cls).__new__(cls, *args, **kwargs)
            cls._prompt = "> "
            cls.parser = None
            cls.completer = None
            cls.output = sys.stdout
            cls.running = Event()
        return cls._instance

    def _complete(self, text, state):
        hints = (readline.get_endidx() - readline.get_begidx()) == 0
        matches = self.completer(readline.get_line_buffer(), hints)
        return matches[state]

    def set_prompt(self, prompt):
        self._prompt = prompt

    def run(self):
        readline.parse_and_bind('tab: complete')
        readline.set_completer(self._complete)
        self.running.set()
        while self.running.is_set():
            try:
                line = raw_input(self._prompt)
                result = self.parser(line)
                if type(result) is list:
                    for result_line in result:
                        self.output.write(result_line + "\n")
                elif type(result) is str:
                    self.output.write(result + "\n")
            except KeyboardInterrupt:
                self.parser("exit")
            except EOFError:
                self.parser("exit")
