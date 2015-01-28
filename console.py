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

import readline
from threading import Thread, Event
from command import Command, command_root

class CmdQuit(Command):
    def __init__(self, name, cons):
        super(CmdQuit, self).__init__()
        self.name = name
        self.cons = cons
    def execute(self):
        self.cons.running.clear()

class Console(Thread):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Console, cls).__new__(cls, *args, **kwargs)
            cls._prompt = "> "
            cls.running = Event()
            command_root.add(CmdQuit("exit", cls))
            command_root.add(CmdQuit("quit", cls))
        return cls._instance

    def _complete(self, text, state):
        hints = (readline.get_endidx() - readline.get_begidx()) == 0
        matches = command_root.match(readline.get_line_buffer(), hints)
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
                result = command_root.parse(line)
                if type(result) is list:
                    for result_line in result:
                        print result_line
            except Command.NotFound:
                print "No such command '{:s}'".format(line)
            except Command.SyntaxError as e:
                print e.message
            except KeyboardInterrupt:
                command_root.parse("exit")
            except EOFError:
                command_root.parse("exit")
