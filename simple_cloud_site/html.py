#!/usr/bin/env python
# encoding: utf-8
"""HTML processing utilities"""
from __future__ import absolute_import, print_function, unicode_literals

from datetime import datetime, timezone
from functools import wraps
from warnings import warn

from lxml.etree import HTMLParser, XPath
from lxml.html import tostring, parse as _html_parse
from dateutil.parser import parse as parse_date

UTF8_PARSER = HTMLParser(encoding='utf-8')


def parse_html(file_like, **kwargs):
    """lxml.html.parse with UTF-8 compatibility

    lxml is buggy and will interpret all files as latin-1, even when Python 3
    has nicely decoded them into correct objects. See
    https://bugs.launchpad.net/lxml/+bug/898072
    """

    return _html_parse(file_like, parser=UTF8_PARSER, **kwargs)


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


BLOG_POST_XPATHS = [XPath(i) for i in ('/html/body[@itemtype="http://schema.org/BlogPosting"]', )]
# TODO: Use custom xpath / CSS checks from config file?

def is_blog_post(html):
    return any(i(html) for i in BLOG_POST_XPATHS)


TITLE_XPATHS = [XPath(i) for i in ('//*[@itemprop="title"]/text()', 'head/title/text()')]


def extract_title(html):
    for xpath in TITLE_XPATHS:
        res = xpath(html)
        if res:
            return res[0].strip()


DESCRIPTION_XPATHS = [XPath(i) for i in ('//*[@itemprop="description"]/text()',
                                         'head/meta[@name="description"]/@content')]


def extract_description(html):
    for xpath in DESCRIPTION_XPATHS:
        res = xpath(html)
        if res:
            return res[0].strip()


TIMESTAMP_XPATHS = [XPath(i) for i in ('//*[@itemprop="dateModified"]/@datetime',
                                       '//*[@itemprop="datePublished"]/@datetime',
                                       '//*[@itemprop="dateCreated"]/@datetime')]


def normalize_timestamp(f):
    """Ensure that the decorated function returns UTC datetime or None"""
    @wraps(f)
    def inner(*args, **kwargs):
        timestamp = f(*args, **kwargs)

        if timestamp:
            if timestamp.tzinfo:
                timestamp = timestamp.astimezone(timezone.utc)
            else:
                warn("%s: extracted last modified time without a timezone: %s" % (f, timestamp))
        return timestamp

    return inner


@normalize_timestamp
def extract_last_modified(html):
    """Given an HTML ElementTree, returns the last modification date

    Uses:
        * schema.org dateModified/datePublished/dateCreated
        * <meta http-equiv="last-modified">
    """

    # These use ISO-8601 format dates:
    for i in TIMESTAMP_XPATHS:
        res = i(html)
        if res:
            return parse_date(res[0])

    # This uses a different time format:
    meta_equiv = html.xpath('/head/meta[@http-equiv="last-modified"]/@content')
    if meta_equiv:
        return datetime.strptime(meta_equiv, "%a, %d %b %Y %H:%M:%S %z")
