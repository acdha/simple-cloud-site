# encoding: utf-8
"""Generate index.html file"""
# FIXME: recursively update subdirectories
from __future__ import absolute_import, print_function, unicode_literals

import logging

from cliff.command import Command
from lxml.html import tostring
from pyquery import PyQuery

from simple_cloud_site.html import html_from_string, lxml_inner_html, parse_html, tidy
from simple_cloud_site.site import load_site


class UpdateIndices(Command):
    def get_description(self):
        return __doc__

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument(
            "--tidy",
            default=False,
            action="store_true",
            help="Tidy HTML using tidy-html5 (https://github.com/w3c/tidy-html5)",
        )
        return parser

    def take_action(self, args):
        site = load_site()

        logging.info("Updating indices under %s", site.base_dir)

        logging.debug("Loading recent posts")
        recent_posts = site.pages.get_recent_posts(4)

        logging.debug("Loading _templates/index.html")
        # TODO: read template name from a config file
        template = PyQuery(parse_html("_templates/index.html").getroot())

        template.find("title").text(site.config.get("site", "site_title"))

        post_list = template.find(".post-list").removeClass("placeholder")
        post_template = post_list.children().eq(0).clone().removeClass("placeholder")
        post_list.empty()

        for post in recent_posts:
            p = post_template.clone()

            uri = site.filename_to_url(post.filename)

            html = post.html.getroot()
            html.make_links_absolute(uri)

            p.find("a.title").removeClass("placeholder").attr("href", uri).text(
                post.title
            )

            post_date = post.get_publication_date()
            p.find(".date").removeClass("placeholder").text(
                post_date.strftime("%b %d")
            ).attr("datetime", post_date.isoformat())

            summary = html.cssselect(".summary")
            if summary:
                p.find(".summary").removeClass("placeholder").html(
                    lxml_inner_html(summary[0]).strip()
                )
            else:
                p.find(".summary").remove()

            # Work around https://github.com/gawel/pyquery/issues/31 by correctly parsing Unicode
            # into an HTML Element instance rather than passing in the text directly.
            body = p.find(".body").removeClass("placeholder").empty()
            for i in PyQuery(html_from_string(post.articleBody)).contents():
                if isinstance(i, str):
                    # Work around https://github.com/gawel/pyquery/issues/32 by forcing
                    # lxml.etree._ElementUnicodeResult into str:
                    i = str(i)
                body.append(i)

            p.appendTo(post_list)

        orphans = template.find(".placeholder")
        if orphans:
            logging.error("Template contained unexpanded placeholders: %s", orphans)

        logging.info("Replacing index.html")
        with open("index.html", "wb") as f:
            # We don't use template.outerHtml because that would lose the doctype
            f.write(
                tostring(template[0].getroottree(), method="html", encoding="utf-8")
            )

        if args.tidy:
            logging.info("Tidying index.html")
            tidy("index.html")
