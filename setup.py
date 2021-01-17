#!/usr/bin/env python3

from setuptools import setup

setup(name='photo-workflow',
      python_requires='>=3',
      install_requires = ['easywebdav','jinja2'],
      version='0.2',
      description='marsupium photo workflow helpers',
      author='Magnus Hagdorn',
      author_email='magnus.hagdorn@marsupium.org',
      url='https://github.com/mhagdorn/photo-workflow',
      packages=['photo_workflow'],
      package_data={'photo_workflow': ['data/*.png','data/*.xml']},
      include_package_data = True,
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
