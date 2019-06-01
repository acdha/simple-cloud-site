# encoding: utf-8
"""Simple local HTTP development server

This is intended to preview a local static HTML site during development. It
extends the default ``python -m http.server`` behaviour with several extensions:

1. Cache-Control headers will be sent to avoid browser caching
2. Minified media will be replaced with uncompressed counterparts if present to avoid needing to alter
   templates for more convenient development:
    * Requests for *.min.css will be treated as requests for *.css
    * Requests for *.min.js will be treated as requests for *.js
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import re
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from cliff.command import Command

from simple_cloud_site import VERSION

DEMINIFY_RE = re.compile(r"[.]min[.](css|js)$")


class DevRequestHandler(SimpleHTTPRequestHandler):
    server_version = "simple-cloud-site/%s" % VERSION

    def send_response(self, code, message=None):
        super().send_response(code, message=message)

        self.send_header("Cache-Control", "private, no-cache, must-revalidate")

        if code == 200 and hasattr(self, "old_path") and self.old_path != self.path:
            self.send_header("Content-Location", self.path)
            self.send_header(
                "X-Content-Location-Notice",
                "served {0.path} for {0.old_path}".format(self),
            )

    def do_GET(self, *args, **kwargs):
        new_path, count = DEMINIFY_RE.subn(r".\1", self.path)
        if count and os.path.exists(new_path):
            self.log_message("Override: %s ➟ %s" % (self.path, new_path))
            self.old_path = self.path
            self.path = new_path

        return super().do_GET(*args, **kwargs)


def run_server(address, port):
    httpd = TCPServer((address, port), DevRequestHandler)

    print("Serving %s at http://%s:%s/" % (os.getcwd(), address, port))
    httpd.serve_forever()


class DevServer(Command):
    def get_description(self):
        return __doc__

    def get_parser(self, prog_name):
        parser = super(DevServer, self).get_parser(prog_name)
        parser.add_argument(
            "--address", type=str, default="127.0.0.1", help="Local server address"
        )
        parser.add_argument(
            "--port", type=int, default=8000, help="Local server port number"
        )
        return parser

    def take_action(self, args):
        run_server(args.address, args.port)
