#!/usr/bin/env python
from __future__ import absolute_import, print_function, unicode_literals

import logging
import sys

from cliff.app import App
from cliff.commandmanager import CommandManager

from simple_cloud_site import VERSION


class SimpleCloudSiteApp(App):
    log = logging.getLogger(__name__)

    def __init__(self):
        super(SimpleCloudSiteApp, self).__init__(
            description="Simple Cloud Site",
            version=VERSION,
            command_manager=CommandManager("simple_cloud_site.commands"),
        )


def main(argv=sys.argv[1:]):
    return SimpleCloudSiteApp().run(argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
