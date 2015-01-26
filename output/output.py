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

from command import Command, CmdBranch, command_root

class CmdOutputList(Command):
    def __init__(self):
        super(CmdOutputList, self).__init__()
        self.name = "list"
    def execute(self):
        output = self.storage["output"]
        list = ["Available output modules:"]
        for o in output.available():
            list.append(" {:s} - {:s}".format(o["alias"], o["desc"]))
        return list

class CmdOutputOnOff(Command):
    def __init__(self, name):
        super(CmdOutputOnOff, self).__init__()
        self.name = name
    def execute(self):
        if len(self.tokens) != 1:
            return False
        module_name = self.tokens[0][1]

        output = self.storage["output"]
        if self.name == "enable":
            result = output.enable(module_name)
        elif self.name == "disable":
            result = output.disable(module_name)

        if result:
            list = ["Output module {:s} {:s}d".format(module_name, self.name)]
        else:
            list = ["Unable to {:s} module {:s}".format(self.name, module_name)]

        return list

class Outputs(object):
    _outputs = {}
    _active = {}
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Outputs, cls).__new__(cls, *args, **kwargs)
            c_output = CmdBranch("output")
            c_output.storage["output"] = cls._instance
            command_root.add(c_output)
            c_output.add(CmdOutputList())
            c_output.add(CmdOutputOnOff("enable"))
            c_output.add(CmdOutputOnOff("disable"))
        return cls._instance

    # Register a new output module
    def register(self, module):
        self._outputs[module.alias] = module

    # Enable module
    def enable(self, name):
        if not name in self._outputs:
            return False
        if name in self._active:
            return True

        module = self._outputs[name]
        try:
            self._active[name] = module.Output()
        except:
            return False

        return True

    # Disable module
    def disable(self, name):
        if not name in self._active:
            return False
        del self._active[name]
        return True

    def _presentable(self, names):
        return map(lambda x: {
            "alias" : self._outputs[x].alias,
            "name" : self._outputs[x].name,
            "desc" : self._outputs[x].desc,
        }, names)

    # Return list of available outputs
    def available(self):
        return self._presentable(self._outputs.keys())

    # Return list of active outputs
    def active(self):
        return self._presentable(self._active.keys())

    # Update active outputs with new data
    def update(self, data):
        for output in self._active:
            module = self._active[output]
            module.update(data)
