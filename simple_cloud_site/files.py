#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from collections import deque
import os

from .html import parse_html, is_blog_post, extract_last_modified

IGNORE_DIRECTORIES = ['.git', '.hg', '.svn', '_templates']


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
        if f.endswith(".html"):
            yield f


def find_recent_pages(source_dir, count=8):
    """Returns a list of recent content pages"""

    pages = deque()

    for f in find_html_files(source_dir):
        h = parse_html(f)

        if not is_blog_post(h):
            continue

        d = extract_last_modified(h)

        pages.append((d, f))

    return sorted(pages, reverse=True)[:count]
