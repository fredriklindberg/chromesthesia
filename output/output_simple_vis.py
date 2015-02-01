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

import pyglet
from pyglet2d import Shape

alias = "simplevis"
name = "Simple visualizer"
desc = "Simple graphical visualizer, suitable for testing"

class SimpleVis(pyglet.window.Window):
    def __init__(self, width, height):
        config = pyglet.gl.Config(sample_buffers=1, samples=4)
        super(SimpleVis, self).__init__(width, height, config=config,
            resizable=True, caption="Simple visualizer")

    def on_draw(self):
        self.clear()

        self.beatradius = int(self.width * 0.045 * 0.5)
        self.beaty = int(self.height - (self.beatradius * 2.5))

        self.barheight = int(self.height - (self.beatradius * 4))
        self.barwidth = int(self.width * 0.06)
        self.begin = int(self.barwidth * 0.5)

        shapes = []
        x = self.begin
        width = self.barwidth
        for bin in "bass", "mid", "tre":
            d = self.data["bins"][bin]
            level = int(d["level"] * self.barheight)
            flux =  int(d["flux"] * self.barheight)
            trans = int(d["transient"] * 255)

            if not self.data["silence"]:
                shapes.append(Shape.circle([x + self.beatradius, self.beaty],
                    self.beatradius, color=(0, trans, 0)))

            shapes.append(
                Shape.rectangle([(x, 0), (x+width, level)], color=(255, 0, 0)))
            x += width
            shapes.append(
                Shape.rectangle([(x, 0), (x+width, flux)], color=(255, 128, 0)))
            x += int(width * 1.5)

        x += self.barwidth
        width = int((self.width - x) / (len(self.data["spectrum"]) + 1))
        g = 0
        for level in self.data["spectrum"]:
            level = int(level * self.barheight)

            shapes.append(
                Shape.rectangle([(x, 0), (x+width, level)], color=(0, g, 255)))
            g = min(g + 20, 255)
            x += width

        for shape in shapes:
            shape.draw()

class Output(object):
    def __init__(self):
        pyglet.gl.glBlendFunc(pyglet.gl.GL_SRC_ALPHA,
                              pyglet.gl.GL_ONE_MINUS_SRC_ALPHA)
        pyglet.gl.glEnable(pyglet.gl.GL_BLEND)
        pyglet.gl.glEnable(pyglet.gl.GL_LINE_SMOOTH)
        pyglet.gl.glHint(pyglet.gl.GL_LINE_SMOOTH_HINT, pyglet.gl.GL_NICEST)
        pyglet.gl.glLineWidth(3)

    def on_enable(self):
        self.window = SimpleVis(width=512, height=200)

    def on_disable(self):
        self.window.close()
        self.window = None

    def update(self, data):
        self.window.data = data
        pyglet.clock.tick()
        self.window.switch_to()
        self.window.dispatch_events()
        self.window.dispatch_event('on_draw')
        self.window.flip()
