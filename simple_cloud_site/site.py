# encoding: utf-8

from configparser import RawConfigParser
import os


class Site(object):
    def __init__(self, config_filename):
        # BUG: validation & instructions for missing config file

        config_filename = os.path.realpath(config_filename)

        self.base_dir = os.path.dirname(config_filename)

        self.config = config = RawConfigParser()
        config.read(config_filename)

        self.base_url = config.get('site', 'base_url')

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
