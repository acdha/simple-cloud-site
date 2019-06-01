# encoding: utf-8
from __future__ import absolute_import, print_function, unicode_literals

import logging
import os

from cliff.command import Command

from simple_cloud_site.site import load_site
from simple_cloud_site.templates import apply_template


class ApplyTemplate(Command):
    __doc__ = apply_template.__doc__

    def get_parser(self, prog_name):
        parser = super().get_parser(prog_name)
        parser.add_argument("files", metavar="HTML_FILE", nargs="*")
        parser.add_argument("--verbose", "-v", default=False, action="store_true")
        parser.add_argument(
            "--tidy",
            default=False,
            action="store_true",
            help="Tidy HTML using tidy-html5 (https://github.com/w3c/tidy-html5)",
        )
        parser.add_argument(
            "--update-timestamps",
            default=False,
            action="store_true",
            help="Replace timestamps with the current time when updating files",
        )
        parser.add_argument(
            "--all-posts",
            default=False,
            action="store_true",
            help="Update all blog posts",
        )
        parser.add_argument(
            "--template",
            default="_templates/post.html",
            help="Template filename (default: %(default)s)",
        )
        return parser

    def take_action(self, args):
        if not os.path.exists(args.template):
            raise RuntimeError("Template file %s does not exist" % args.template)

        if not args.all_posts and not args.files:
            raise RuntimeError(
                "Either list one or more files to update or use --all-posts"
            )

        site = load_site()
        blog_posts = site.pages.get_blog_posts()

        if not args.all_posts:
            files = args.files
        else:
            files = [i.filename for i in blog_posts]

        for f in files:
            if args.verbose:
                logging.info("Applying %s to %s", args.template, f)

            apply_template(
                args.template,
                f,
                site,
                blog_posts=blog_posts,
                tidy_html=args.tidy,
                update_timestamps=args.update_timestamps,
            )
