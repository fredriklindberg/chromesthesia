#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name="chromesthesia",
      version=0,
      description='Realtime sound visualizer with modular output support',
      author='Fredrik Lindberg',
      author_email='fli@shapeshifter.se',
      packages=['chromesthesia_app',
                'chromesthesia_app/output',
                'chromesthesia_app/output/helpers'],
      scripts=['chromesthesia'],
      setup_requires=['numpy', 'PyAudio']
    )
