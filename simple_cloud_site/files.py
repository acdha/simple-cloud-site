# encoding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from collections import deque
from functools import lru_cache
import os

from .html import Page

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


@lru_cache(maxsize=None)
def find_blog_posts(source_dir):
    """Returns a list of HTML files which are blog posts"""

    pages = deque()

    for f in find_html_files(source_dir):
        p = Page(f)

        if not p.is_blog_post:
            continue
        else:
            pages.append(p)

    return pages


def find_recent_posts(source_dir, count=8):
    """Returns a list of recent content pages"""

    pages = find_blog_posts(source_dir)

    return sorted(pages, reverse=True, key=lambda p: p.date_modified)[:count]
