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
import pyaudio
import numpy as np
from struct import unpack
from multiprocessing import Process, Value, Pipe

class SoundAnalyzer(object):

    def __init__(self, sample, chunk):
        self._chunk = chunk
        self._sample = sample

        bands = []
        freq = sample
        # Split sample rate into bands with an exponential decay
        # and 0-156 selected as the smallest band.  We calculate
        # the mean power over these bands.
        while freq > 156:
            prev_freq = freq
            freq = freq / 2

            # Pre-calculate offset into power array
            prev_power_idx = 2 * chunk * prev_freq / sample
            power_idx = 2 * chunk * freq / sample

            bands.insert(0, [power_idx, prev_power_idx])

        bands.insert(0, [0, (2 * chunk * freq / sample)])
        self._bands = bands

    def bands(self):
        return len(self._bands)

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

        spectrum = [0] * len(self._bands)

        while running:
            try:
                data = input.read(self._chunk)
            except:
                continue

            # Convert raw to numpy array
            data = unpack("%dh" % (len(data) / 2), data)
            data = np.array(data, dtype='h')

            # Run numpy real FFT
            fourier = np.fft.rfft(data)
            power = np.abs(fourier)

            i = 0
            for band in self._bands:
                s,e = band
                try:
                    spectrum[i] = int(np.mean(power[s:e:1]))
                except:
                    spectrum[i] = 0
                i = i + 1

            pipe.send(spectrum)

    def scaled(self, weights, scale, ceil):
        tmp = self._pipe.recv()
        tmp = np.multiply(tmp, weights)
        tmp = np.divide(tmp, scale)
        return tmp.clip(0, ceil)

    @property
    def levels(self):
        return self._average
