#!/usr/bin/env python
# encoding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import logging
import os
from datetime import datetime, timezone

from lxml.html import tostring
from pyquery import PyQuery

from simple_cloud_site.html import Page, parse_html, tidy


def apply_template(
    template_filename,
    filename,
    site,
    blog_posts=None,
    tidy_html=False,
    update_timestamps=False,
):
    """Create or update an HTML file using a template"""

    logging.debug("Loading template file %s", template_filename)
    template = PyQuery(
        parse_html(template_filename).getroot()
    )  # TODO: cache parsed templates

    if os.path.exists(filename):
        logging.info("Loading HTML file %s", filename)
        original_post = Page(filename)
    else:
        logging.info("Creating new HTML file %s", filename)
        original_post = Page(template_filename)
        update_timestamps = True

        # We'll open the template file and prepare the destination:
        output_dir = os.path.dirname(filename)
        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

    original = PyQuery(original_post.html.getroot())

    template('title,*[itemprop="title"]').removeClass("placeholder").text(
        original_post.title
    )

    logging.debug("Processing timestamps")

    now = datetime.now(timezone.utc)

    for i in ("dateCreated", "dateModified", "datePublished"):
        src_val = None

        j = original('*[itemprop="%s"]' % i)

        if j:
            src_val = j.attr("datetime" if j.is_("time") else "content")

        if update_timestamps or not src_val:
            src_val = now.isoformat()

        target = template('*[itemprop="%s"]' % i)
        if target:
            target.attr("datetime" if target.is_("time") else "content", src_val)

    post_date = original_post.get_publication_date()
    if update_timestamps or not post_date:
        post_date = now

    # TODO: make post date format configurable
    template("time.date").removeClass("placeholder").text(
        post_date.strftime("%b %d")
    ).attr("datetime", post_date.isoformat())

    last_modified = original_post.last_modified
    if update_timestamps or not last_modified:
        last_modified = now

    template('meta[http-equiv="last-modified"]').attr(
        "content", last_modified.strftime("%a, %d %b %Y %H:%M:%S GMT")
    )

    logging.debug("Updating summary")
    summary = original(".summary").eq(0)
    if summary:
        template(".summary").removeClass("placeholder").empty().html(summary.html())
    else:
        template(".summary").remove()

    logging.debug("Updating body")
    template('*[itemprop="articleBody"]').removeClass("placeholder").empty().append(
        original('*[itemprop="articleBody"]').children()
    )

    logging.debug("Updating meta description")
    desc = original_post.description or summary.text()
    if desc:
        template('meta[name="description"]').attr("content", desc)
    else:
        template('meta[name="description"]').remove()

    logging.debug("Updating navigation")
    post_nav = template("#post-nav")
    if not blog_posts:
        post_nav.remove()
    else:
        prev_post = next_post = None

        for post in blog_posts:
            pub_date = post.get_publication_date()

            if pub_date < post_date and (
                not prev_post or pub_date > prev_post.date_published
            ):
                prev_post = post
            elif pub_date > post_date and (
                not next_post or pub_date < next_post.date_published
            ):
                next_post = post

        if not prev_post:
            post_nav(".previous").remove()
        else:
            post_nav(".previous").removeClass("placeholder").attr(
                "href", site.filename_to_url(prev_post.filename)
            ).text(prev_post.title)

        if not next_post:
            post_nav(".next").remove()
        else:
            post_nav(".next").removeClass("placeholder").attr(
                "href", site.filename_to_url(next_post.href)
            ).text(next_post.title)

    orphans = template.find(".placeholder")
    if orphans:
        logging.warning("Template contained unexpanded placeholders: %s", orphans)

    logging.info("Saving %s", filename)
    with open(filename, "wb") as f:
        # We don't use template.outerHtml because that would lose the doctype
        f.write(tostring(template[0].getroottree(), method="html", encoding="utf-8"))

    if tidy_html:
        logging.info("Tidying HTML in %s", filename)
        tidy(filename)
