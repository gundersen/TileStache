#!/usr/bin/env python

from distutils.core import setup

version = '0.1.6'

setup(name='TileStache',
      version=version,
      description='A stylish alternative for caching your map tiles.',
      author='Michal Migurski',
      author_email='mike@stamen.com',
      url='http://tilestache.org',
      requires=['ModestMaps'],
      packages=['TileStache',
                'TileStache.Goodies',
                'TileStache.Goodies.Providers'],
      scripts=['scripts/tilestache-render.py', 'scripts/tilestache-seed.py'],
      data_files=[('share/tilestache', ['TileStache/Goodies/Providers/DejaVuSansMono-alphanumeric.ttf'])],
      download_url='http://tilestache.org/download/TileStache-%(version)s.tar.gz' % locals(),
      license='BSD')
