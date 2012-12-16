#!/usr/bin/env python
# encoding: utf-8
"""HTML processing utilities"""
from __future__ import absolute_import, print_function, unicode_literals

from lxml.html import tostring


def lxml_inner_html(elem):
    """
    Return the innerHTML representation of an element

    lxml doesn't actually have a usable way to get the inner HTML so we have
    to walk the tree manually so we can take::

      <div id="foo">bar<b>baaz</b>quux</div>

    and return::

      bar<b>baaz</b>quux
    """

    html = [elem.text or '']

    for i in elem.getchildren():
        serialized = tostring(i, method='html', encoding='unicode')
        html.append(serialized)

    return ''.join(filter(None, html))

