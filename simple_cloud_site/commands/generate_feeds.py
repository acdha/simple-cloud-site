# encoding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

from urllib.parse import urljoin

from cliff.command import Command

from simple_cloud_site.feeds import Atom, RSS, Sitemap
from simple_cloud_site.site import load_site


class GenerateFeeds(Command):
    """Generate sitemap.xml and RSS and Atom feeds"""

    def take_action(self, parsed_args):
        site = load_site()

        site_info = {
            'site_url': site.base_url,
            'site_title': site.config.get('site', 'site_title'),
            'site_description': site.config.get('site', 'site_description'),
            'author_name': site.config.get('author', 'name'),
            'author_email': site.config.get('author', 'email'),
        }

        sitemap = Sitemap(site_info)
        rss = RSS(site_info)
        atom = Atom(site_info)

        # TODO: Split sitemap / feed generation or impement lazy loading to avoid having to parse pages rather than read from the DB
        for page in site.pages.get_all_pages():
            path = site.filename_to_url(page.filename)

            if path == '/':
                continue  # Skip the index page

            url = urljoin(site.base_url, path)

            sitemap.add_page(url, page)
            if page.is_blog_post:
                rss.add_page(url, page)
                atom.add_page(url, page)

        with open('sitemap.xml', 'wb') as f:
            f.write(sitemap.serialize())

        with open('feeds/all.rss', 'wb') as f:
            f.write(rss.serialize())

        with open('feeds/all.atom', 'wb') as f:
            f.write(atom.serialize())
