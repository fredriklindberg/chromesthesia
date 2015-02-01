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

class CmdOutputModules(Command):
    def __init__(self):
        super(CmdOutputModules, self).__init__()
        self.name = "modules"
    def execute(self):
        output = self.storage["output"]
        list = ["Available output modules:"]
        for o in output.available():
            list.append(" {:s} - {:s}".format(o["alias"], o["desc"]))
        return list

class CmdOutputList(Command):
    def __init__(self):
        super(CmdOutputList, self).__init__()
        self.name = "list"
    def execute(self):
        output = self.storage["output"]
        list = ["Outputs:"]
        for o in output.instances():
            list.append(" {:s} ({:s})".format(o["name"], o["type"]))
        return list

class CmdOutputActive(Command):
    def __init__(self):
        super(CmdOutputActive, self).__init__()
        self.name = "active"
    def execute(self):
        output = self.storage["output"]
        list = ["Active outputs:"]
        for o in output.active():
            list.append(" {:s} ({:s})".format(o["name"], o["type"]))
        return list

class CmdOutputOnOff(Command):
    def __init__(self, name):
        super(CmdOutputOnOff, self).__init__()
        self.name = name
    def hints(self):
        list = self.storage["output"].available()
        return map(lambda x: x["alias"], list)
    def execute(self):
        if len(self.tokens) != 1:
            raise Command.SyntaxError("Output instance required")
        instance_name = self.tokens[0][1]

        output = self.storage["output"]
        if self.name == "enable":
            result = output.enable(instance_name)
        elif self.name == "disable":
            result = output.disable(instance_name)

        if result:
            list = ["Output {:s} {:s}d".format(instance_name, self.name)]
        else:
            list = ["Failed to {:s} output {:s}".format(self.name, instance_name)]

        return list

class CmdOutputCreate(Command):
    def __init__(self):
        super(CmdOutputCreate, self).__init__()
        self.name = "create"
    def execute(self):
        if len(self.tokens) != 1:
            raise Command.SyntaxError("Module name required")
        module_name = self.tokens[0][1]

        output = self.storage["output"]
        instance_name = output.create(module_name)
        if instance_name:
            return ["Output '{:s}' created".format(instance_name)]
        else:
            return ["Failed to create output of type '{:s}'".format(module_name)]

class CmdOutputDestroy(Command):
    def __init__(self):
        super(CmdOutputDestroy, self).__init__()
        self.name = "destroy"
    def execute(self):
        if len(self.tokens) != 1:
            raise Command.SyntaxError("Instance name required")
        instance_name = self.tokens[0][1]

        output = self.storage["output"]
        if output.destroy(instance_name):
            return ["Output '{:s}' destroyed".format(instance_name)]
        else:
            return ["Failed to destroy output '{:s}'".format(instance_name)]

class Outputs(object):
    _outputs = {}
    _instances = {}
    _enabled = []

    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Outputs, cls).__new__(cls, *args, **kwargs)
            c_output = CmdBranch("output")
            c_output.storage["output"] = cls._instance
            command_root.add(c_output)
            c_output.add(CmdOutputList())
            c_output.add(CmdOutputModules())
            c_output.add(CmdOutputActive())
            c_output.add(CmdOutputCreate())
            c_output.add(CmdOutputDestroy())
            c_output.add(CmdOutputOnOff("enable"))
            c_output.add(CmdOutputOnOff("disable"))
        return cls._instance

    # Register a new output module
    def register(self, module):
        self._outputs[module.alias] = module

    # Create an instance of a module
    def create(self, name):
        if name not in self._outputs:
            return False

        index = len(self._instances.keys())
        instance_name = "{:s}{:d}".format(name, index)
        if instance_name in self._instances:
            return False

        module = self._outputs[name]
        try:
            instance = module.Output()
        except:
            return False
        self._instances[instance_name] = {"type" : name, "obj" : instance}
        return instance_name

    # Destroy an instance of a module
    def destroy(self, name):
        if name not in self._instances:
            return False
        self.disable(name)
        del self._instances[name]
        return True

    # Enable module
    def enable(self, name):
        if name not in self._instances:
            return False
        instance = self._instances[name]["obj"]
        if instance in self._enabled:
            return True
        self._enabled.append(instance)
        try:
            instance.on_enable()
        except AttributeError:
            pass
        return True

    # Disable module
    def disable(self, name):
        if name not in self._instances:
            return False
        instance = self._instances[name]["obj"]
        if instance not in self._enabled:
            return False
        self._enabled.remove(instance)
        try:
            instance.on_disable()
        except AttributeError:
            pass
        return True

    # Return list of available output modules
    def available(self):
        return sorted(map(lambda x: {
            "alias" : self._outputs[x].alias,
            "name" : self._outputs[x].name,
            "desc" : self._outputs[x].desc,
        }, self._outputs.keys()))

    # Return list of outputs
    def instances(self):
        return sorted(map(lambda x: {
            "name" : x,
            "type" : self._instances[x]["type"]
        }, self._instances.keys()))

    # Return list of active outputs
    def active(self):
        enabled = []
        for name in self._instances:
            instance = self._instances[name]
            if instance["obj"] in self._enabled:
                enabled.append({ "name" : name, "type" : instance["type"]})
        return sorted(enabled)

    # Update active outputs with new data
    def update(self, data):
        for instance in self._enabled:
            instance.update(data)
