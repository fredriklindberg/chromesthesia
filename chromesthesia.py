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
# chromesthesia is a realtime sound visualizer that can generate
# real life physical light shows as well as digital on-screen visuals.

import sys
import output
import console
from threading import Event
from multiprocessing import Pipe
from select import select
from sound import SoundAnalyzer
from command import Command, command_root

class CmdStart(Command):
    def __init__(self, rlist):
        super(CmdStart, self).__init__()
        self.name = "start"
        self.rlist = rlist
    def execute(self):
        if "sound" in self.storage:
            return ["Sound processing already running"]
        self.storage["sound"] = SoundProxy()
        self.storage["sound"].start()
        self.rlist.append(self.storage["sound"])

class CmdStop(Command):
    def __init__(self, rlist):
        super(CmdStop, self).__init__()
        self.name = "stop"
        self.rlist = rlist
    def execute(self):
        if not "sound" in self.storage:
            return ["Sound processing not running"]
        self.storage["sound"].stop()
        del self.storage["sound"]

class SoundProxy(object):
    def __init__(self):
        self.outputs = output.Outputs()
        self.sa = SoundAnalyzer(44100, 60)

    def start(self):
        self.sa.start()
        self.outputs.start()

    def stop(self):
        self.outputs.stop()
        self.sa.stop()

    def fileno(self):
        return self.sa.fileno()

    def read(self):
        try:
            data = self.sa.data()
            self.outputs.update(data)
        except:
            pass

class CmdQuit(Command):
    def __init__(self, name, running):
        super(CmdQuit, self).__init__()
        self.name = name
        self.running = running
    def execute(self):
        for r in self.running:
            r.clear()

class ConsoleProxy(object):
    def __init__(self):
        self._read, self._write = Pipe(duplex=True)

    def fileno(self):
        return self._read.fileno()

    def read(self):
        data = self._read.recv()
        if data["type"] == "completer":
            result = command_root.match(data["line"], data["hints"])
        elif data["type"] == "parser":
            try:
                result = command_root.parse(data["line"])
            except Command.NotFound:
                result = "No such command '{:s}'".format(data["line"])
            except Command.SyntaxError as e:
                result = e.message
        else:
            result = ""

        self._read.send(result)

    def completer(self, line, hints):
        self._write.send({"type" : "completer", "line" : line, "hints" : hints})
        return self._write.recv()

    def parser(self, line):
        self._write.send({"type" : "parser", "line" : line})
        return self._write.recv()


def main(args):
    running = Event()
    cp = ConsoleProxy()

    cons = console.Console()
    cons.parser = cp.parser
    cons.completer = cp.completer
    cons.set_prompt("chromesthesia> ")
    cons.start()

    rlist = []
    command_root.add(CmdQuit("exit", [running, cons.running]))
    command_root.add(CmdQuit("quit", [running, cons.running]))
    command_root.add(CmdStart(rlist))
    command_root.add(CmdStop(rlist))

    rlist.append(cp)
    running.set()
    while running.is_set():
        try:
            rr, _, _ = select(rlist, [], [])
            for obj in rr:
                obj.read()
        except KeyboardInterrupt:
            cons.running.clear()
            running.clear()

    cons.join()
    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
