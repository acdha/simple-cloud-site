simple-cloud-site
=================

Experiment: going all in on a static site, where pure HTML is the only storage format using semantic HTML5
and schema.org microdata.

Currently developed and tested only on Python 3, although some effort has been made to keep backporting easy
if necessary.

*WARNING*: changes highly likely until it hits 1.0…

Philosophy
~~~~~~~~~~


* Command-line tools used to manage a static site which will be uploaded to something supported by
  `Apache libcloud <http://https://libcloud.apache.org/>`_ — currently tested with Rackspace Cloud Files.
* No template language is assumed, avoiding any impedance mismatches between modern HTML and the tooling or
  the need to have anything other than a browser to render pages. What you test is what you get.
* HTML templates can be developed live in a browser; all content with the ``placeholder`` class will be
  removed by the ``apply-template`` command.
* No attempt is made to provide change tracking – it's highly recommended that you use Git, Mercurial, etc. on
  the site base directory instead.

Getting Started
---------------

Installation
~~~~~~~~~~~~

* ``pip install simple-cloud-site``
* Run ``simple-cloud-site --help`` to list commands

Configuration
~~~~~~~~~~~~~

1. Create ``index.html`` and ``post.html`` templates in ``_templates/``
2. Create ``.simple-cloud-site.cfg`` with site-specific configuration::

    [auth]
    username=YOUR_USERNAME
    api-key=YOUR_API_KEY
    region=YOUR_REGION

    [site]
    container=YOUR_CONTAINER_NAME
    base_url=BASE_URL
    site_title=SITE_TITLE_FOR_FEEDS
    site_description=SITE_DESCRIPTION_FOR_FEEDS

    [author]
    name = YOUR_NAME
    email = YOUR_EMAIL

3. Optionally, enable shell completion using the output of ``simple-cloud-site complete`` – for example, in a
   virtualenvwrapper postactivate script::

    eval "$( simple-cloud-site complete )"

Applying Templates
~~~~~~~~~~~~~~~~~~

``simple-cloud-site apply-template [--template=filename] path/to/post.html``

Previewing
~~~~~~~~~~

``simple-cloud-site devserver``

Open the listed URL in your browser

Publishing
~~~~~~~~~~

``simple-cloud-site publish``

Open the public URL in your browser