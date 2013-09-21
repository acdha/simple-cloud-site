from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys


setup(
    name='simple-cloud-site',
    version='0.0.1',
    url='http://github.com/acdha/simple-cloud-site/',
    license='CC0',
    author='Chris Adams',
    install_requires=['lxml', 'pyquery', 'python-dateutil', 'apache-libcloud'],
    author_email='chris@improbable.org',
    description='Tools for working with pure HTML static sites',
    long_description=open("README.rst", "r", encoding="utf-8").read(),
    packages=['simple_cloud_site'],
    include_package_data=True,
    platforms='any',
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content'],
)
