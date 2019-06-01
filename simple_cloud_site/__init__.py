# encoding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import pkg_resources

__all__ = ["VERSION"]

VERSION = "DEVELOPMENT"

pkgs = pkg_resources.require("simple_cloud_site")
if pkgs:
    VERSION = pkgs[0].version
