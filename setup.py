#!/usr/bin/env python3

from setuptools import setup

setup(name='photo-workflow',
      python_requires='>=3',
      install_requires = ['easywebdav',],
      version='0.1',
      description='marsupium photo workflow helpers',
      author='Magnus Hagdorn',
      author_email='magnus.hagdorn@marsupium.org',
      url='https://github.com/mhagdorn/photo-workflow',
      packages=['photo_workflow'],
      entry_points={
          'console_scripts': [
              'photo-create-project = photo_workflow.create:main',
              'photo-backup-project = photo_workflow.backup:main',
              'photo-download-gpx = photo_workflow.getgpx:main',
              'photo-archive = photo_workflow.archive:main',
              'photo-krpano = photo_workflow.krpano:main',
              ],
      },

  )
