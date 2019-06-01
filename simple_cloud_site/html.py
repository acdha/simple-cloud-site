# encoding: utf-8
"""HTML processing utilities"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import sys
from datetime import timezone
from functools import wraps
from subprocess import PIPE, Popen, check_call

from dateutil.parser import parse as parse_date
from dateutil.tz import tzlocal
from lxml.etree import XPath
from lxml.html import HTMLParser
from lxml.html import fromstring as _html_fromstring
from lxml.html import parse as _html_parse
from lxml.html import tostring

from .utils import cached_property

UTF8_PARSER = HTMLParser(encoding="utf-8")


def parse_html(file_like, **kwargs):
    """lxml.html.parse with UTF-8 compatibility

    lxml is buggy and will interpret all files as latin-1, even when Python 3
    has nicely decoded them into correct objects. See
    https://bugs.launchpad.net/lxml/+bug/898072
    """

    return _html_parse(file_like, parser=UTF8_PARSER, **kwargs)


def html_from_string(string):
    """Parse a string into an lxml fragment

    Works around lxml's bug treating unicode strings as latin-1
    """

    return _html_fromstring(string, parser=UTF8_PARSER)


def lxml_inner_html(elem):
    """
    Return the innerHTML representation of an element

    lxml doesn't actually have a usable way to get the inner HTML so we have
    to walk the tree manually so we can take::

      <div id="foo">bar<b>baaz</b>quux</div>

    and return::

      bar<b>baaz</b>quux
    """

    html = [elem.text or ""]

    for i in elem.getchildren():
        serialized = tostring(i, method="html", encoding="unicode")
        html.append(serialized)

    return "".join(filter(None, html))


def filename_or_document(f):
    """
    Ensure that the calling function receives lxml document, parsing a filename
    if necessary
    """

    @wraps(f)
    def inner(filename_or_doc, *args, **kwargs):
        if not hasattr(filename_or_doc, "docinfo"):
            filename_or_doc = parse_html(filename_or_doc)
        return f(filename_or_doc, *args, **kwargs)

    return inner


def normalize_timestamp(f):
    """Ensure that the decorated function returns UTC datetime or None"""

    @wraps(f)
    def inner(*args, **kwargs):
        timestamp = f(*args, **kwargs)

        if timestamp:
            if timestamp.tzinfo:
                timestamp = timestamp.astimezone(timezone.utc)
            else:
                local_tz = tzlocal()
                logging.warn(
                    "last modified time did not specify timezone, assuming system: %s",
                    timestamp,
                )
                timestamp = timestamp.replace(tzinfo=local_tz)

        return timestamp

    return inner


def get_first_xpath(xpaths, doc):
    """Return the first element matched by the provided list of XPATH expressions"""
    for i in xpaths:
        res = i(doc)
        if res:
            return res[0]


# TODO: Use custom xpath / CSS checks from config file?
BLOG_POST_XPATHS = [
    XPath(i) for i in ('/html/body[@itemtype="http://schema.org/BlogPosting"]',)
]
TITLE_XPATHS = [
    XPath(i) for i in ('//*[@itemprop="title"]/text()', "head/title/text()")
]
DESCRIPTION_XPATHS = [
    XPath(i)
    for i in (
        '//*[@itemprop="description"]/text()',
        'head/meta[@name="description"]/@content',
    )
]

LAST_MODIFIED_XPATHS = [XPath('//meta[@http-equiv="last-modified"]/@content')]

DATE_MODIFIED_XPATHS = [
    XPath(i)
    for i in (
        '//time[@itemprop="dateModified"]/@datetime',
        '//meta[@itemprop="dateModified"]/@content',
    )
]
DATE_CREATED_XPATHS = [
    XPath(i)
    for i in (
        '//time[@itemprop="dateCreated"]/@datetime',
        '//meta[@itemprop="dateCreated"]/@content',
    )
]
DATE_PUBLISHED_XPATHS = [
    XPath(i)
    for i in (
        '//time[@itemprop="datePublished"]/@datetime',
        '//meta[@itemprop="datePublished"]/@content',
    )
]
TIMESTAMP_XPATHS = (
    LAST_MODIFIED_XPATHS
    + DATE_MODIFIED_XPATHS
    + DATE_PUBLISHED_XPATHS
    + DATE_CREATED_XPATHS
)


class Page(object):
    def __init__(self, filename_or_doc, filename=None):
        if filename:
            self.filename = filename
        elif isinstance(filename_or_doc, str):
            self.filename = filename_or_doc
        elif hasattr(filename_or_doc, "name"):
            self.filename = filename_or_doc.name

        # If this has already been parsed, we'll load now. Otherwise we'll let
        # .html lazy-load run on-demand
        if hasattr(filename_or_doc, "docinfo"):
            self.html = filename_or_doc

    @classmethod
    def from_cache(cls, data):
        """Populates a page using cached attributes where possible"""

        if "filename" not in data:
            raise ValueError("from_cache must receive at least the filename")

        c = cls(data["filename"])

        for k in cls.__dict__:
            if k.startswith("_"):
                continue

            if k in data:
                v = data[k]
                c.__dict__[k] = v

        return c

    @cached_property
    def html(self):
        return parse_html(self.filename)

    @property
    def href(self):
        # BUG: decide how we're going to normalize these!
        return self.filename

    @cached_property
    def is_blog_post(self):
        return is_blog_post(self.html)

    @cached_property
    def title(self):
        return extract_title(self.html)

    @cached_property
    def description(self):
        return extract_description(self.html)

    @cached_property
    @normalize_timestamp
    def date_created(self):
        i = get_first_xpath(DATE_CREATED_XPATHS, self.html)
        return parse_date(i) if i else None

    @cached_property
    @normalize_timestamp
    def date_published(self):
        i = get_first_xpath(DATE_PUBLISHED_XPATHS, self.html)
        return parse_date(i) if i else None

    @cached_property
    @normalize_timestamp
    def date_modified(self):
        i = get_first_xpath(DATE_MODIFIED_XPATHS, self.html)
        return parse_date(i) if i else None

    @cached_property
    @normalize_timestamp
    def last_modified(self):
        meta_equiv = get_first_xpath(LAST_MODIFIED_XPATHS, self.html)
        if meta_equiv:
            return parse_date(meta_equiv)

    def get_publication_date(self):
        return (
            self.date_published
            or self.date_created
            or self.date_modified
            or self.last_modified
        )

    def get_modification_date(self):
        dates = filter(
            None,
            (
                self.last_modified,
                self.date_published,
                self.date_modified,
                self.date_created,
            ),
        )
        return max(dates) if dates else None

    # schema.org microdata accessors:
    @cached_property
    def articleBody(self):
        body = self.html.xpath('//*[@itemprop="articleBody"]')
        if body:
            return lxml_inner_html(body[0]).strip()
        else:
            return ""


@filename_or_document
def is_blog_post(html):
    return any(i(html) for i in BLOG_POST_XPATHS)


@filename_or_document
def extract_title(html):
    for xpath in TITLE_XPATHS:
        res = xpath(html)
        if res:
            return res[0].strip()


@filename_or_document
def extract_description(html):
    for xpath in DESCRIPTION_XPATHS:
        res = xpath(html)
        if res:
            return res[0].strip()


def tidy(filename):
    # This is an ugly travesty and depends on https://github.com/w3c/tidy-html5
    # In its defense, it actually works at all which is more than can be said
    # for html5lib, lxml3, BeautifulSoup, etc. and there are no Python 3
    # migration issues…
    tidy = Popen(
        [
            "tidy-html5",
            "-utf8",
            "-modify",
            "-quiet",
            "--tidy-mark",
            "no",
            "--wrap",
            "0",
            "--indent",
            "yes",
            "--indent-spaces",
            "4",
            filename,
        ],
        stderr=PIPE,
        stdout=PIPE,
    )
    stdout, stderr = tidy.communicate()

    if stderr:
        stderr = stderr.decode("utf-8").strip()
        stderr = "\n".join("\t%s" % i.strip() for i in stderr.splitlines())
        print(
            "HTML tidy reported problems for %s:\n" % filename, stderr, file=sys.stderr
        )

    check_call(["perl", "-p", "-i", "-e", 's|itemscope=""|itemscope|', filename])
    # See: https://github.com/w3c/tidy-html5/pull/58
