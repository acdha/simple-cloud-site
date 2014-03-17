#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from collections import deque
from email.utils import format_datetime
from urllib.parse import urljoin
from warnings import warn

from lxml import etree, objectify


class Feed(object):
    def __init__(self, metadata):
        self.pages = deque()
        self.metadata = metadata

    def add_page(self, url, page):
        # Ensure that the values are always sortable numbers:
        if not page.date_modified:
            date_modified = 0
        else:
            date_modified = page.date_modified.timestamp()

        self.pages.append((date_modified, url, page))

    def serialize(self):
        raise NotImplementedError


class Sitemap(Feed):
    def serialize(self):
        E = objectify.ElementMaker(annotate=False,
                                   namespace='http://www.sitemaps.org/schemas/sitemap/0.9',
                                   nsmap={None: 'http://www.sitemaps.org/schemas/sitemap/0.9'})

        urlset = E.urlset()

        for last_mod, url, page in self.pages:
            url_elem = E.url(E.loc(url))
            if last_mod:
                url_elem.append(E.lastmod(page.date_modified.isoformat()))
            urlset.append(url_elem)

        return etree.tostring(urlset, pretty_print=True, encoding='utf-8')


class RSS(Feed):
    def add_page(self, url, page):
        if not page.title:
            warn("Skipping %s: missing title" % url)
            return

        if not page.date_modified:
            warn("%s: missing last modified timestamp" % url)

        super().add_page(url, page)

    def serialize(self):
        E = objectify.ElementMaker(annotate=False, nsmap={"atom": "http://www.w3.org/2005/Atom"})

        channel = E.channel(E.title(self.metadata['site_title']),
                            E.link(self.metadata['site_url']),
                            E.description(self.metadata['site_description']))

        channel.append(etree.Element("{http://www.w3.org/2005/Atom}link", rel="self",
                                     href=urljoin(self.metadata['site_url'], "/feeds/all.atom")))

        for last_mod, url, page in sorted(self.pages, key=lambda i: i[0], reverse=True)[:10]:
            item = E.item(E.title(page.title), E.link(url),
                          E.guid(url, isPermaLink="true"))

            if page.description:
                item.append(E.description(page.description))

            if page.date_modified:
                item.append(E.pubDate(format_datetime(page.date_modified)))

            channel.append(item)

        rss = E.rss(channel, version="2.0")

        return etree.tostring(rss, pretty_print=True, encoding='utf-8', xml_declaration=True)


class Atom(RSS):
    def serialize(self):
        E = objectify.ElementMaker(annotate=False, nsmap={None: "http://www.w3.org/2005/Atom"})

        feed = E.feed(E.title(self.metadata['site_title']),
                      E.id(self.metadata['site_url']),
                      E.link(rel="self", href=urljoin(self.metadata['site_url'], "/feeds/all.atom")),
                      E.subtitle(self.metadata['site_description']),
                      E.author(E.name(self.metadata['author_name']),
                               E.email(self.metadata['author_email'])))

        pages = sorted(self.pages, key=lambda i: i[0], reverse=True)

        feed.append(E.updated(pages[0][2].date_modified.isoformat()))

        for last_mod, url, page in sorted(self.pages, key=lambda i: i[0], reverse=True)[:10]:
            entry = E.entry(E.title(page.title), E.id(url), E.link(href=url))

            if page.description:
                entry.append(E.summary(page.description))

            if page.articleBody:
                entry.append(E.content(page.articleBody, type="html"))

            if page.date_modified:
                entry.append(E.updated(page.date_modified.isoformat()))

            feed.append(entry)

        return etree.tostring(feed, pretty_print=True, encoding='utf-8', xml_declaration=True)
