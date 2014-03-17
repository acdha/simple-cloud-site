#!/usr/bin/env python
from __future__ import print_function

from setuptools import setup

setup(
    name='simple-cloud-site',
    version='0.0.2',
    url='http://github.com/acdha/simple-cloud-site/',
    license='CC0',
    author='Chris Adams',
    install_requires=['lxml', 'pyquery', 'python-dateutil', 'apache-libcloud'],
    author_email='chris@improbable.org',
    description='Tools for working with pure HTML static sites',
    long_description=open('README.rst', 'r', encoding='utf-8').read(),
    packages=['simple_cloud_site'],
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'
    ],
)
