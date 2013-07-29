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

import alsaaudio as alsa
import numpy as np
from struct import unpack

class SoundAnalyzer(object):

    _matrix = []
    _average = []

    def __init__(self, sample, chunk):
        self._input = alsa.PCM(alsa.PCM_CAPTURE, alsa.PCM_NORMAL)
        self._input.setchannels(1)
        self._input.setrate(sample)
        self._input.setformat(alsa.PCM_FORMAT_S16_LE)
        self._input.setperiodsize(chunk)

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
        self._average = self._matrix = [0] * len(bands)

    def bands(self):
        return len(self._bands)

    def poll(self):
        l,data = self._input.read()
        if not l:
            return False

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
                self._matrix[i] = int(np.mean(power[s:e:1]))
            except:
                self._matrix[i] = 0
            i = i + 1

        # Keep a weighted rolling average
        self._average = np.divide(self._average, 2)
        self._average = np.add(self._average, self._matrix)
        self._average = np.divide(self._average, 2)

        return True

    def scaled(self, weights, scale, ceil):
        tmp = self._average
        tmp = np.multiply(tmp, weights)
        tmp = np.divide(tmp, scale)
        return tmp.clip(0, ceil)

    @property
    def levels(self):
        return self._average
