# encoding: utf-8
"""Publish the local directory"""
from __future__ import absolute_import, print_function, unicode_literals

import logging
import mimetypes
import os
from configparser import RawConfigParser
from hashlib import md5
from queue import Queue
from threading import Thread

from cliff.command import Command
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ContainerDoesNotExistError, Provider

from simple_cloud_site.files import find_files

CLOUDFILES = get_driver(Provider.CLOUDFILES_US)


def get_driver_instance(config, container_name):
    """
    Wrapper to safely get a driver

    This allows us to use the non-thread-safe libcloud within a thread pool
    """

    driver = CLOUDFILES(
        config.get("auth", "username"),
        config.get("auth", "api-key"),
        ex_force_service_region=config.get("auth", "region"),
    )

    try:
        container = driver.get_container(container_name=container_name)
    except ContainerDoesNotExistError:
        container = driver.create_container(container_name=container_name)
        logging.warning(
            "Created container %s. You may wish to configure it", container_name
        )

    return driver, container


def upload_worker(i, q, config, container_name):
    driver, container = get_driver_instance(config, container_name)

    while True:
        kwargs = q.get()
        logging.info("Uploading %(object_name)s", kwargs)
        driver.upload_object(container=container, **kwargs)
        q.task_done()


class Publish(Command):
    def get_description(self):
        return __doc__

    def take_action(self, parsed_args):
        config = RawConfigParser()
        # FIXME: support running outside of the site root
        # FIXME: enforce mode 600!
        config.read([".simple-cloud-site.cfg"])

        source_dir = os.path.realpath(os.curdir)

        # TODO: allow provider configuration
        container_name = config.get("site", "container")

        logging.info("Publishing %s to %s", source_dir, container_name)

        driver, container = get_driver_instance(config, container_name)

        upload_queue = Queue()

        workers = [
            Thread(target=upload_worker, args=(i, upload_queue, config, container_name))
            for i in range(8)
        ]

        remote_objects = {i.name: i.hash for i in container.list_objects()}

        for f in find_files(source_dir):
            target_path = f.replace(source_dir, "").lstrip("/")

            # TODO: load ignore list from site config
            if target_path.endswith(".scss"):
                continue

            if target_path in remote_objects:
                # TODO: don't read the file twice:
                with open(f, "rb") as local_file:
                    h = md5()
                    for chunk in iter(lambda: local_file.read(8192), b""):
                        h.update(chunk)
                    if h.hexdigest() == remote_objects[target_path]:
                        continue

            mime_type, encoding = mimetypes.guess_type(f)
            if not mime_type:
                mime_type = "application/octet-stream"
            upload_queue.put(
                {
                    "object_name": target_path,
                    "file_path": f,
                    "extra": {"content_type": mime_type},
                }
            )

        logging.info("Waiting for %d uploads to complete…", upload_queue.qsize())

        for worker in workers:
            worker.setDaemon(True)
            worker.start()

        upload_queue.join()

        logging.info("Configuring static site…")
        driver.ex_enable_static_website(container=container, index_file="index.html")
        driver.ex_set_error_page(container=container, file_name="error.html")
        driver.enable_container_cdn(container=container)

        print("CDN URL:", driver.get_container_cdn_url(container=container))
