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

import os
import glob
import sys
import importlib

from .outputs import Outputs

sys.path.append(os.path.dirname(__file__))

outputs = Outputs()

modules = glob.glob(os.path.dirname(__file__)+"/output_*.py")
__all__ = []
for module in modules:
    try:
        name = os.path.basename(module)[:-3]
        module = importlib.import_module(name)
        outputs.register(module)
        __all__.append(name)
    except:
        pass
