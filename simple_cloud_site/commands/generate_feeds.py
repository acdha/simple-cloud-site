# encoding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from urllib.parse import urljoin

from cliff.command import Command

from simple_cloud_site.feeds import FeedMaker
from simple_cloud_site.site import load_site


class GenerateFeeds(Command):
    """Generate sitemap.xml and RSS and Atom feeds"""

    def take_action(self, parsed_args):
        site = load_site()

        site_info = {
            "site_url": site.base_url,
            "site_title": site.config.get("site", "site_title"),
            "site_description": site.config.get("site", "site_description"),
            "author_name": site.config.get("author", "name"),
            "author_email": site.config.get("author", "email"),
        }

        feed_maker = FeedMaker(site_info)

        for page in site.pages.get_all_pages():
            path = site.filename_to_url(page.filename)

            if path == "/":
                continue  # Skip the index page

            url = urljoin(site.base_url, path)

            feed_maker.add_page(url, page)

        with open("sitemap.xml", "wb") as f:
            feed_maker.generate_sitemap(f)

        with open("feeds/all.rss", "wb") as f:
            feed_maker.generate_rss(f)

        with open("feeds/all.atom", "wb") as f:
            feed_maker.generate_atom(f)
