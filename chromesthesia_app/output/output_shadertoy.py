#!/usr/bin/env python
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

import sdl2
import sdl2.ext
import numpy as np
import ctypes
import datetime as dt
import time
import random
import os
from OpenGL import GL, constant
from OpenGL.GL.ARB import debug_output
from OpenGL.extensions import alternate

alias = "shadertoy"
name = "Shadertoy"
desc = "Shadertoy visualizer, using shaders from shadertoy.com"

vertex = """
#version 120

attribute vec2 position;
void main()
{
    gl_Position = vec4(position, 0.0, 1.0);
}
"""

fragment = """
#version 120

// shadertoy specific inputs
uniform vec3      iResolution;            // The viewport resolution (z is pixel aspect ratio, usually 1.0)
uniform float     iGlobalTime;            // Current time in seconds
uniform float     iChannelTime[4];        // Time for channel (if video or sound), in seconds
uniform vec3      iChannelResolution[4];  // Input texture resolution for each channel
uniform vec4      iMouse;                 // xy = current pixel coords (if LMB is down). zw = click pixel
uniform sampler2D iChannel0;              // Sampler for input textures 0
uniform sampler2D iChannel1;              // Sampler for input textures 1
uniform sampler2D iChannel2;              // Sampler for input textures 2
uniform sampler2D iChannel3;              // Sampler for input textures 3
uniform vec4      iDate;                  // Year, month, day, time in seconds in .xyzw
uniform float     iSampleRate;            // The sound sample rate (typically 44100)

%s
"""

class Window(object):
    def __init__(self, title=b'', width=640, height=360, fullscreen=False):
        if sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO) != 0:
            raise RuntimeError(sdl2.SDL_GetError())
        self.size = (width, height)
        self._programs = {}

        flags = sdl2.SDL_WINDOW_OPENGL | sdl2.SDL_WINDOW_RESIZABLE
        self.window = sdl2.SDL_CreateWindow(
            title, sdl2.SDL_WINDOWPOS_UNDEFINED,
            sdl2.SDL_WINDOWPOS_UNDEFINED, width, height, flags)
        self.context = sdl2.SDL_GL_CreateContext(self.window)
        self.renderer = sdl2.SDL_CreateRenderer(self.window, -1, sdl2.SDL_RENDERER_PRESENTVSYNC)
        sdl2.SDL_ShowCursor(False)
        self.desktop_mode = sdl2.SDL_DisplayMode()
        sdl2.SDL_GetDesktopDisplayMode(0, self.desktop_mode)
        self.set_fullscreen(fullscreen)

    def close(self):
        self.set_fullscreen(False)
        for prog in self._programs:
            self._programs[prog].destroy()
        self._programs = {}
        sdl2.SDL_DestroyRenderer(self.renderer)
        sdl2.SDL_GL_DeleteContext(self.context)
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    def is_fullscreen(self):
        return sdl2.SDL_GetWindowFlags(self.window) & sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP

    def set_fullscreen(self, fullscreen):
        if fullscreen:
            ratio = float(self.desktop_mode.w) / float(self.desktop_mode.h)
            (w, h) = (640, int(640/ratio))

            sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b"linear")
            sdl2.SDL_RenderSetLogicalSize(self.renderer, w, h)
            sdl2.SDL_SetWindowFullscreen(self.window, sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP)
        else:
            sdl2.SDL_SetWindowFullscreen(self.window, 0)

    def add_program(self, name, shadertoy):
        program = Program(shadertoy)
        (w, h) = self.size
        program["iResolution"] = [float(w), float(h), 1.0]
        self._programs[name] = program

    def programs(self):
        return list(self._programs.keys())

    def select_program(self, name):
        self.program = self._programs[name]
        self.program.activate()
        (width, height) = self.size
        self.program["iResolution"] = [float(width), float(height), 1.0]
        GL.glViewport(0, 0, width, height);

    def set_channel_input(self, i, data):
        self.program['iChannel%d' % i] = data
        self.program['iChannelResolution[%d]' % i] = data.shape

    def on_resize(self, width, height):
        self.size = (width, height)
        self.program["iResolution"] = [float(width), float(height), 1.0]
        GL.glViewport(0, 0, width, height)

    def on_event(self, event):
        if event.type == sdl2.SDL_WINDOWEVENT:
            if event.window.event == sdl2.SDL_WINDOWEVENT_RESIZED:
                self.on_resize(event.window.data1, event.window.data2)
        elif event.type == sdl2.SDL_KEYDOWN:
            self.set_fullscreen(not self.is_fullscreen())

    def draw(self):
        self.program.draw()
        sdl2.SDL_GL_SwapWindow(self.window)

class Program(object):
    _vars = {
        'iResolution' : 'vec3',
        'iGlobalTime' : 'float',
        'iChannelTime[0]' : 'float',
        'iChannelTime[1]' : 'float',
        'iChannelTime[2]' : 'float',
        'iChannelTime[3]' : 'float',
        'iChannelResolution[0]' : 'vec3',
        'iChannelResolution[1]' : 'vec3',
        'iChannelResolution[2]' : 'vec3',
        'iChannelResolution[3]' : 'vec3',
        'iMouse' : 'vec4',
        'iChannel0' : 'sampler2D',
        'iChannel1' : 'sampler2D',
        'iChannel2' : 'sampler2D',
        'iChannel3' : 'sampler2D',
        'iDate' : 'vec4',
        'iSampleRate' : 'float'
    }
    _texmap = {
        'iChannel0' : 0,
        'iChannel1' : 1,
        'iChannel2' : 2,
        'iChannel3' : 3,
    }

    def __init__(self, program):
        self._data = {}
        self._vertices = [
            -1.0, -1.0,
            -1.0,  1.0,
             1.0,  1.0,
            -1.0, -1.0,
             1.0,  1.0,
             1.0, -1.0]
        # Setup and bind vertices
        vert_array = ((ctypes.c_float * len(self._vertices)) (*self._vertices))
        self._vbo = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo)
        GL.glBufferData(GL.GL_ARRAY_BUFFER,
            ctypes.sizeof(vert_array), vert_array, GL.GL_STATIC_DRAW)

        # Compile vertex shader
        vertex_shader = GL.glCreateShader(GL.GL_VERTEX_SHADER)
        GL.glShaderSource(vertex_shader, vertex)
        GL.glCompileShader(vertex_shader)
        if GL.glGetShaderiv(vertex_shader, GL.GL_COMPILE_STATUS) != GL.GL_TRUE:
            raise RuntimeError(GL.glGetShaderInfoLog(vertex_shader).decode('ASCII'))

        # Compile fragment shader
        frag_shader = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
        GL.glShaderSource(frag_shader, fragment % program)
        GL.glCompileShader(frag_shader)
        if GL.glGetShaderiv(frag_shader, GL.GL_COMPILE_STATUS) != GL.GL_TRUE:
            raise RuntimeError(GL.glGetShaderInfoLog(frag_shader).decode('ASCII'))

        # Create shader program
        self._shader_program = GL.glCreateProgram()
        GL.glAttachShader(self._shader_program, vertex_shader)
        GL.glAttachShader(self._shader_program, frag_shader)

        # Link and validate program
        GL.glLinkProgram(self._shader_program)
        if GL.glGetProgramiv(self._shader_program, GL.GL_LINK_STATUS) != GL.GL_TRUE:
            raise RuntimeError(GL.glGetProgramInfoLog(self._shader_program).decode('ASCII'))
        GL.glValidateProgram(self._shader_program)
        if GL.glGetProgramiv(self._shader_program, GL.GL_VALIDATE_STATUS) != GL.GL_TRUE:
            raise RuntimeError(GL.glGetProgramInfoLog(self._shader_program).decode('ASCII'))

        # Activate so we can setup inputs
        GL.glUseProgram(self._shader_program)

        # Vertext data layout
        self._vertpos = GL.glGetAttribLocation(self._shader_program, "position")
        GL.glEnableVertexAttribArray(self._vertpos)
        GL.glVertexAttribPointer(self._vertpos, 2, GL.GL_FLOAT, False, 0, ctypes.c_voidp(0))

        # Setup default values for inputs
        self["iResolution"] = [0.0, 0.0, 1.0]
        self["iGlobalTime"] = 0.0
        for i in range(0, 3):
            self["iChannelTime[%d]" % i] = 0.0
            self["iChannelResolution[%d]" % i] = [0.0, 0.0, 1.0]
        self["iMouse"] = [0.0, 0.0, 0.0, 0.0]
        self["iDate"] = [0.0, 0.0, 0.0, 0.0]
        self["iSampleRate"] = 44100.0

        empty = np.array([
            [[0], [0]],
            [[0], [0]]
        ]).astype(np.uint8)

        for chan in "iChannel0", "iChannel1", "iChannel2", "iChannel3":
            handle = GL.glGetUniformLocation(self._shader_program, chan)
            GL.glUniform1i(handle, self._texmap[chan])
            self[chan] = empty

        GL.glDeleteShader(frag_shader)
        GL.glDeleteShader(vertex_shader)

    def destroy(self):
        GL.glDisableVertexAttribArray(self._vertpos)
        GL.glDeleteProgram(self._shader_program)
        GL.glDeleteBuffers(1, [self._vbo])

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, val):
        self._data[key] = val
        handle = GL.glGetUniformLocation(self._shader_program, key)
        if handle < 0:
            return
        type = self._vars[key]

        if type == 'float':
            GL.glUniform1f(handle, float(val))
        elif type == 'vec3':
            GL.glUniform3fv(handle, 1, val)
        elif type == 'vec4':
            GL.glUniform4fv(handle, 1, val)
        elif type == 'sampler2D':
            texture_id = self._texmap[key]
            self._set_texture(texture_id, val)

    def _set_texture(self, texture_id, data):
        (h, w, _) = data.shape

        GL.glActiveTexture(GL.GL_TEXTURE0 + texture_id)

        id = GL.glGenTextures(1)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, id)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_REPEAT)

        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
        GL.glTexParameterf(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_DEPTH_COMPONENT, w, h, 0,
            GL.GL_DEPTH_COMPONENT, GL.GL_UNSIGNED_BYTE, data)

    def activate(self):
        GL.glUseProgram(self._shader_program)

    def draw(self):
        GL.glClearColor(0.0, 0.0, 0.0, 1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT)
        GL.glDrawArrays(GL.GL_TRIANGLES, 0, int(len(self._vertices) / 2))

class Output(object):
    def __init__(self, config):
        pass

    def on_start(self):
        self.window = Window(title=b"Shadertoy")

        path = os.path.join(os.path.dirname(__file__), "shadertoy")
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if not os.path.isfile(file_path) or file[0] == '.':
                continue
            f = open(file_path)
            frag = f.read()
            f.close()
            self.window.add_program(file, frag)

        self._list = []
        self._time = random.randint(7, 15)
        self.select_program()
        self.window.draw()

    def select_program(self, program=None):
        if not program:
            if not self._list:
                self._list = self.window.programs()
                random.shuffle(self._list)
            program = self._list.pop()
        self.window.select_program(program)

    def on_stop(self):
        self.window.close()
        self.window = None

    def update(self, data, dt):
        if not self.window:
            return
        self._time -= dt

        if self._time <= 0.0:
            if data["silence"] or data["bins"]["bass"]["transient"] == 1.0:
                self._time = random.randint(7, 15)
                self.select_program()

        flux = ((data["bins"]["bass"]["flux"]*2 + data["bins"]["mid"]["flux"] + \
            data["bins"]["tre"]["flux"]) / 4) / 0.025
        flux = min(2.0, flux)

        self.window.program["iGlobalTime"] += (flux * dt)

        # Transform the spectrum data into a 2D texture with the
        # dimensions (len(spectrum), height).  Each band represent one
        # point on the x axis with the y axis holding the intensity
        # represented by the color values 0 to 255
        height = 128
        spectrum = np.array(data["spectrum"])
        coef = np.linspace(0, 255, height).reshape(height, 1)
        spectrum = (spectrum * coef).astype(np.uint8)
        spectrum = spectrum.reshape(height, len(data["spectrum"]), 1)

        # Update iChannel0 texture with spectrum data
        self.window.set_channel_input(0, spectrum)

        self.window.draw()
        events = sdl2.ext.get_events()
        for event in events:
            self.window.on_event(event)

# Generate a (pretty bad) test pattern for debugging
if __name__ == '__main__':
    fps = 30
    o = Output({})
    o.on_start()

    data = {
        "bins" : {},
        "spectrum" : [0] * 8,
        "silence" : False
    }

    bins = ["bass", "mid", "tre"]
    for bin in bins:
        data["bins"][bin] = {
            "level" : 0.0,
            "flux" : 0.1,
            "transient" : 0.0
        }

    spectrum_step = [0.008, 0.007, 0.006, 0.005, 0.004, 0.003, 0.002, 0.001]

    bin = 0
    for i in range(0, 60):
        o.update(data, 1.0/fps)
        data["spectrum"] = np.add(data["spectrum"], spectrum_step)
        data["spectrum"] = np.mod(data["spectrum"], 1.0)
        time.sleep(1.0/fps)

    o.on_stop()
    o.update(data, 1.0/fps)
    time.sleep(1)
    o.on_start()
    while True:
        o.update(data, 1.0/fps)
        data["spectrum"] = np.add(data["spectrum"], spectrum_step)
        data["spectrum"] = np.mod(data["spectrum"], 1.0)
        time.sleep(1.0/fps)
