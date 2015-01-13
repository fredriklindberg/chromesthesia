# Copyright (C) 2013 Fredrik Lindberg <fli@shapeshifter.se>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
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
import os
import signal
import math
import pyaudio
import numpy as np
from struct import unpack
from multiprocessing import Process, Value, Pipe

class SoundAnalyzer(object):

    _clip = 256

    def __init__(self, sample, chunk, scale):
        self._chunk = chunk
        self._sample = sample
        self._scale = scale

        bins = []
        freq = sample
        # Split sample rate into bins with an exponential decay
        # and 0-156 selected as the smallest band.  We calculate
        # the mean power over these bins.
        while freq > 156:
            prev_freq = freq
            freq = freq / 2

            # Pre-calculate offset into power array
            prev_power_idx = 2 * chunk * prev_freq / sample
            power_idx = 2 * chunk * freq / sample

            bins.insert(0, [power_idx, prev_power_idx])

        bins.insert(0, [0, (2 * chunk * freq / sample)])
        self._bins = bins

        # Calculate EQ weights
        # Start with power of 2 up to 64 and stretch to match number of bins
        self._eq = []
        eq = [1, 2, 4, 8, 16, 32, 64]
        if len(eq) < len(self._bins):
            ith = len(eq)/(len(self._bins) - len(eq))
            for i in xrange(0, len(eq) - 1):
                self._eq.append(eq[i])
                if (i % ith) == 0:
                    self._eq.append((eq[i] + eq[i+1]) / 2)
            self._eq.append(eq[-1])

    def bins(self):
        return len(self._bins)

    def start(self):
        self._running = Value('i', 1)
        self._pipe, pipe = Pipe(duplex=False)

        self._p = Process(target=self._run, args=(self._running, pipe))
        self._p.daemon = True
        self._p.start()
        pipe.close()

    def stop(self):
        self._running.value = 0
        self._p.terminate()
        self._p.join()

    def _run(self, running, pipe):
        self._pipe.close()
        self._pipe = pipe
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        pa = pyaudio.PyAudio()
        input = pa.open(format=pyaudio.paInt16, input=True,
            channels=1, rate=self._sample, frames_per_buffer=self._chunk)

        spectrum = [0] * len(self._bins)

        bin_per_band = len(self._bins) / 3
        bass_e = max(1, bin_per_band - 1) + 1
        mid_e = bass_e + bin_per_band + 1

        data = {
            "bass" : {
                "level" : 0
            },
            "mid" : {
                "level" : 0
            },
            "tre" : {
                "level" : 0
            }
        }

        while running:
            try:
                frame = input.read(self._chunk)
            except:
                continue

            # Convert raw to numpy array
            frame = unpack("%dh" % (len(frame) / 2), frame)
            frame = np.array(frame, dtype='h')

            # Run numpy real FFT
            fourier = np.fft.rfft(frame)
            power = np.abs(fourier)

            i = 0
            for bin in self._bins:
                s,e = bin
                try:
                    spectrum[i] = int(np.mean(power[s:e:1]))
                except:
                    spectrum[i] = 0
                i = i + 1

            spectrum = np.multiply(spectrum, self._eq)
            spectrum = np.divide(spectrum, self._scale)
            spectrum = spectrum.clip(0, self._clip)

            data["bass"]["level"] = int(np.mean(spectrum[0:bass_e]))
            data["mid"]["level"] = int(np.mean(spectrum[bass_e:mid_e]))
            data["tre"]["level"] = int(np.mean(spectrum[mid_e:]))

            pipe.send({"bins" : data, "spectrum" : spectrum})

    def scaled(self):
        return self._pipe.recv()

    @property
    def levels(self):
        return self._average
