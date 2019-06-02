# encoding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import os

IGNORE_DIRECTORIES = [
    "_templates",
    ".git",
    ".hg",
    ".svn",
    "archive",
    "build",
    "data",
    "dist",
    "feeds",
    "node_modules",
    "static",
    "temp",
    "tmp",
]


def find_files(source_dir):
    """Generator which returns filenames from source_dir

    The results will exclude:
    * Makefiles
    * Any file which starts with .
    * Anything under a directory in IGNORE_DIRECTORIES
      (i.e. version control checkout data)
    """
    for root, dirs, files in os.walk(source_dir):
        for f in files:
            if f.startswith(".") or f.endswith("Makefile"):
                continue

            yield os.path.join(root, f)

        for ignore in IGNORE_DIRECTORIES:
            if ignore in dirs:
                dirs.remove(ignore)


def find_html_files(source_dir):
    """Simple find_files() variant which only yields HTML files"""
    for f in find_files(source_dir):
        if os.path.isfile(f) and f.endswith(".html"):
            yield f
