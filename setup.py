#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import versioneer
versioneer.VCS = 'git'
versioneer.versionfile_source = 'chromesthesia_app/_version.py'
versioneer.versionfile_build = None
versioneer.tag_prefix = ''
versioneer.parentdir_prefix = 'chromesthesia-'

setup(name="chromesthesia",
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='Realtime sound visualizer with modular output support',
      author='Fredrik Lindberg',
      author_email='fli@shapeshifter.se',
      packages=['chromesthesia_app',
                'chromesthesia_app/output',
                'chromesthesia_app/output/helpers'],
      scripts=['chromesthesia'],
      setup_requires=['numpy', 'PyAudio']
    )
