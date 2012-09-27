hls-client
==========

This is a simple Python `HTTP Live Streaming Client`_. It consumes a
list of remote playlists, and saves all needed files to serve the
playlist locally: the key, segments, and a modified ``m3u8`` with paths
normalized.

It also supports backups, i.e., if the same playlist is available on
more than one server, it will track each server status and will switch
to the backup if needed.

Through the ``config.ini`` it’s possible to customize where the files
will be saved and what is the URL that provides servers info via JSON.

The JSON must be something like:

::

    {
        actives: [
            {
                m3u8: "/msfc/Edge.m3u8",
                servers: [
                "liveips.nasa.gov.edgesuite.net"
                ],
                bitrates: [],
                needs_index: false
            }
        ]
    }


Encryption
----------

If you set ``encryption=true`` in the config file, ``hlsclient`` will
automatically encrypt all streams with a random AES-128 cipher.


Running
-------

To run the client, simply run:

::

    $ python -m hlsclient

Running tests
-------------

We use py.test for testing.

::

    $ py.test

.. _HTTP Live Streaming Client: https://developer.apple.com/resources/http-streaming/
