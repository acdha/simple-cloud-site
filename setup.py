#!/usr/bin/env python
from __future__ import print_function

from setuptools import setup

setup(
    name="simple-cloud-site",
    url="http://github.com/acdha/simple-cloud-site/",
    license="CC0",
    author="Chris Adams",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    install_requires=["cliff", "lxml", "pyquery", "python-dateutil", "apache-libcloud"],
    author_email="chris@improbable.org",
    description="Tools for working with pure HTML static sites",
    long_description=open("README.rst", "r", encoding="utf-8").read(),
    packages=["simple_cloud_site", "simple_cloud_site.commands"],
    include_package_data=True,
    platforms="any",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Natural Language :: English",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    entry_points={
        "console_scripts": ["simple-cloud-site = simple_cloud_site.commands.main:main"],
        "simple_cloud_site.commands": [
            "apply-template = simple_cloud_site.commands.apply_template:ApplyTemplate",
            "devserver = simple_cloud_site.commands.devserver:DevServer",
            "generate-feeds = simple_cloud_site.commands.generate_feeds:GenerateFeeds",
            "publish = simple_cloud_site.commands.publish:Publish",
            "update-indices = simple_cloud_site.commands.indices:UpdateIndices",
        ],
    },
)
