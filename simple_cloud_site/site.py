# encoding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

import os
import sqlite3
from configparser import RawConfigParser

from dateutil.parser import parse as parse_date

from .files import find_html_files
from .html import Page


class Site(object):
    def __init__(self, config_filename):
        # BUG: validation & instructions for missing config file

        config_filename = os.path.realpath(config_filename)

        self.base_dir = os.path.dirname(config_filename)

        self.config = config = RawConfigParser()
        config.read(config_filename)

        self.base_url = config.get("site", "base_url")

        self.pages = PageCache(self.base_dir)

    def filename_to_url(self, filename):
        path = os.path.relpath(filename, start=self.base_dir)
        path = path.replace("/index.html", "/")
        if not path.startswith("/"):
            path = "/%s" % path
        return path


def load_site(base_dir=None):
    if not base_dir:
        # TODO: find this by searching up for the site config file
        base_dir = os.curdir
    return Site(os.path.join(base_dir, ".simple-cloud-site.cfg"))


# See http://bugs.python.org/issue19065
sqlite3.register_converter("timestamp", parse_date)


class PageCache(object):
    """
    Track page metadata information in a local database to avoid expensive
    operations

    Operations like MD5 sums or extracting page titles, descriptions, dates,
    etc. require a significant amount of overhead. We can cache these values for
    quick access by checking the file inode + mtime.
    """

    def __init__(self, base_dir):
        self.base_dir = base_dir

        db_file = os.path.join(base_dir, ".simple-cloud-site-cache.sqlite")
        self.conn = conn = sqlite3.connect(
            db_file, detect_types=sqlite3.PARSE_DECLTYPES
        )
        conn.row_factory = sqlite3.Row

        self.initialize()
        self.index_site()

    def initialize(self):
        with self.conn as c:
            # FIXME: schema check!

            c.execute(
                """CREATE TABLE IF NOT EXISTS pages (
                             filename VARCHAR(512) PRIMARY KEY,
                             inode INTEGER,
                             mtime INTEGER,
                             is_blog_post BOOLEAN,
                             title TEXT,
                             description TEXT,
                             date_created TIMESTAMP,
                             date_modified TIMESTAMP,
                             date_published TIMESTAMP
                         )"""
            )

    def index_site(self):
        with self.conn as c:
            cursor = c.cursor()

            for html_file in find_html_files(self.base_dir):
                st = os.stat(html_file)

                mtime = int(st.st_mtime)

                cursor.execute(
                    """SELECT inode, mtime FROM pages WHERE filename = ?""",
                    (html_file,),
                )

                row = cursor.fetchone()

                if (
                    row is not None
                    and row["inode"] == st.st_ino
                    and row["mtime"] == mtime
                ):
                    continue

                cursor.execute("""DELETE FROM pages WHERE filename = ?""", (html_file,))

                print("Indexing page: %s" % html_file)

                page = Page(html_file)

                cursor.execute(
                    """INSERT INTO pages
                            (
                                filename, inode, mtime,
                                is_blog_post,
                                title, description,
                                date_created, date_modified, date_published
                            )
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                    (
                        html_file,
                        st.st_ino,
                        mtime,
                        page.is_blog_post,
                        page.title,
                        page.description,
                        page.date_created,
                        page.date_modified,
                        page.date_published,
                    ),
                )

    def get_all_pages(self):
        with self.conn as conn:
            c = conn.cursor()
            for r in c.execute("SELECT * FROM pages ORDER BY date_published"):
                yield Page.from_cache(dict(r))

    def get_blog_posts(self):
        with self.conn as conn:
            c = conn.cursor()
            for r in c.execute(
                "SELECT * FROM pages WHERE is_blog_post = 1 ORDER BY date_published"
            ):
                yield Page.from_cache(dict(r))

    def get_recent_posts(self, count=10):
        with self.conn as conn:
            c = conn.cursor()
            for r in c.execute(
                """SELECT * FROM pages WHERE is_blog_post = 1
                                    ORDER BY date_published DESC
                                    LIMIT %s"""
                % count
            ):
                yield Page.from_cache(dict(r))
