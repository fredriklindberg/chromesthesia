# Copyright (C) 2013 Fredrik Lindberg <fli@shapeshifter.se>
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

import sys
import os
import signal
import math
import time
import pyaudio
import numpy as np
from struct import unpack
from multiprocessing import Process, Value, Pipe

from command import Command
import output
import filter

class SoundAnalyzer(object):

    class Bin(object):
        def __init__(self, fps):
            self._fps = fps
            self._level = 0
            self._prevlevel = 0
            self._avgflux = filter.RMA(fps * 2.5)
            self._avgflux_rect = filter.RMA(fps * 2.5)
            self._flux_thres = filter.MMF(fps * 5)
            self._attack = False
            self._in_transient = False
            self._transient = 0.0
            self._transient_period = filter.RMA(fps * 2)
            self._transient_period.add(0.25)
            self._ts = time.time()

        @property
        def level(self):
            return self._level

        @level.setter
        def level(self, value):
            now = time.time()
            dt = now - self._ts
            self._ts = now

            self._prevlevel = self._level
            # Approximated rolling average
            self._level = (self._level / 2.0) + (value / 2.0)

            # Update spectral flux value
            flux = self._level - self._prevlevel
            self._avgflux.add(abs(flux))

            # Onset/transient calculation
            in_attack = self._level >= self._prevlevel
            onset = flux - self._avgflux_rect.value() >= self._flux_thres.value()

            if not self._in_transient:
                if onset:
                    self._attack = True
                    self._in_transient = True
                    self._transient = 1.0
                    self._onset_ts = now
                    self._attack_vector = [self._level]
                    self._transient_level = self._level
            else:
                x = 1.0 / (self._transient_period.value() / dt)
                self._transient -= x

                if self._attack:
                    if not in_attack:
                        self._transient_level = \
                            np.mean(self._attack_vector) * 0.75
                    else:
                        self._attack_vector.append(self._level)
                    self._attack = in_attack
                else:
                    if self._level < self._transient_level:
                        if self._transient <= 0.0:
                            self._transient = 0.0
                            self._in_transient = False
                            transient = min(1.0, now - self._onset_ts)
                            self._transient_period.add(transient)
                        self._transient /= 2

                    elif self._transient <= -4.0:
                        self._transient = 0.0
                        self._in_transient = False
                        self._transient_period.add(self._transient_period.value())

            self._avgflux_rect.add(max(0.0, flux))
            if flux > 0:
                self._flux_thres.add(flux)

        @property
        def flux(self):
            return self._avgflux.value()

        @property
        def transient(self):
            return max(0.0, self._transient)

    def __init__(self, sample, fps):
        self._fps = fps
        chunk = int(sample / fps)

        self._chunk = chunk
        self._sample = sample
        self._channels = 1
        self._sample_width = 16

        bins = []
        freq = sample
        # Split sample rate into bins with an exponential decay
        # and 0-156 selected as the smallest band.  We calculate
        # the mean power over these bins.
        scale = 2
        freq = freq / 2
        while freq > 156:
            prev_freq = freq
            while True:
                freq = freq / scale
                # Pre-calculate offset into power array
                prev_power_idx = scale * chunk * prev_freq / sample
                power_idx = scale * chunk * freq / sample
                if (prev_power_idx - power_idx) >= 1:
                    break
            bins.insert(0, [power_idx, prev_power_idx])

        bins.insert(0, [0, (scale * chunk * freq / sample)])
        self._bins = bins

        # Calculate EQ weights
        # Range from 2^0 to 2^6 (64) stretched over the number of bins
        self._eq = np.power(2, np.linspace(0, 6, len(self._bins)))

        self._running = Value('i', 0)
        self._pipe, pipe = Pipe(duplex=False)

        self._p = Process(target=self._run, args=(self._running, pipe))
        self._p.daemon = True
        self._p.start()
        pipe.close()

    def close(self):
        self._running.value = -1
        self._p.terminate()
        self._p.join()

    def start(self):
        self._running.value = 1

    def stop(self):
        self._running.value = 0

    def fileno(self):
        return self._pipe.fileno()

    def _run(self, running, pipe):
        self._pipe.close()
        self._pipe = pipe
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        while running.value >= 0:
            if running.value == 1:
                self._analyze(running, pipe)
            else:
                time.sleep(0.1)

    def _analyze(self, running, pipe):
        pa = pyaudio.PyAudio()
        sample_fmt = pa.get_format_from_width(self._sample_width / 8)
        input = pa.open(format=sample_fmt, input=True,
            channels=self._channels, rate=self._sample,
            frames_per_buffer=self._chunk)

        sample_size = self._sample_width / 8
        frame_len = self._chunk * sample_size * self._channels

        if sample_size == 1:
            data_type = 'b'
            unpack_fmt = "%db" % int(frame_len)
        elif sample_size == 2:
            data_type = 'h'
            unpack_fmt = "%dh" % int(frame_len / 2)

        spectrum = [0] * len(self._bins)

        bin_per_band = (len(self._bins) - 1) / 2
        bass_e = 1
        mid_e = bass_e + bin_per_band

        bass = SoundAnalyzer.Bin(self._fps)
        mid = SoundAnalyzer.Bin(self._fps)
        tre = SoundAnalyzer.Bin(self._fps)

        silence_thres = 0.05
        scale = 128
        avg_loudness = 0

        start = time.time()
        while running.value == 1:
            try:
                frame = input.read(self._chunk)
            except:
                continue

            cur = time.time()
            dt = cur - start
            start = cur

            # Convert raw to numpy array
            frame = unpack(unpack_fmt, frame)
            frame = np.array(frame, dtype=data_type)

            # Run numpy real FFT
            fourier = np.fft.rfft(frame)
            power = np.abs(fourier)

            i = 0
            for bin in self._bins:
                s,e = bin
                spectrum[i] = np.mean(power[s:e])
                i = i + 1

            spectrum = np.multiply(spectrum, self._eq)
            spectrum = np.divide(spectrum, scale)
            spectrum = spectrum.clip(0.0, 1.0)

            bass.level = np.mean(spectrum[0:bass_e])
            mid.level = np.mean(spectrum[bass_e:mid_e])
            tre.level = np.mean(spectrum[mid_e:])

            silence = bass.level <= silence_thres and \
                mid.level <= silence_thres and \
                tre.level <= silence_thres

            loudness = ((2 * bass.level) + mid.level +  tre.level) / 4
            avg_loudness = (0.75 * avg_loudness) + (1.0 - 0.75) * loudness
            peak = bass.level >= 1.0 or mid.level >= 1.0 or tre.level >= 1.0

            if not silence:
                if peak or avg_loudness >= 0.5:
                    scale = scale * 1.1
                elif avg_loudness <= 0.05 and scale >= 2:
                    scale = scale / 1.1

            pipe.send({"bins" : {
                    "bass" : {
                        "level" : bass.level,
                        "flux" : bass.flux,
                        "transient" : bass.transient
                    },
                    "mid" : {
                        "level" : mid.level,
                        "flux" : mid.flux,
                        "transient" : mid.transient
                    },
                    "tre" : {
                        "level" : tre.level,
                        "flux" : tre.flux,
                        "transient" : tre.transient
                    },
                }, "silence": silence, "spectrum" : spectrum})

        input.stop_stream()
        input.close()
        pa.terminate()

    def data(self, drop=True):
        data = self._pipe.recv()
        while drop and self._pipe.poll():
            data = self._pipe.recv()
        return data
