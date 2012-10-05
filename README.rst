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
        "streams": [
            "nasa": {
                "input-path": "/msfc/Edge.m3u8",
                servers: [
                    "http://liveips.nasa.gov.edgesuite.net"
                ]
            }
        ]
    }


Variant Playlist Generation
---------------------------

``hlslcient`` can consume multiple playlists and generate a variant playlists grouping then.

To do so, include a ``bandwidth`` for each stream and add an action to combine them in the JSON:

::

    {
        "streams": {
            "Nasa-low": {
                "input-path": "/msfc/Edge.m3u8",
                "servers": ["http://liveips.nasa.gov.edgesuite.net"],
                "bandwidth": 254082
            },
            "Nasa-medium": {
                "input-path": "/msfc/3G.m3u8",
                "servers": ["http://liveips.nasa.gov.edgesuite.net"],
                "bandwidth": 460658
            },
            "Nasa-high": {
                "input-path": "/msfc/Wifi.m3u8",
                "servers": ["http://liveips.nasa.gov.edgesuite.net"],
                "bandwidth": 1080434
            }
        },

        "actions": [
            {
                "type": "combine",
                "input": ["Nasa-low", "Nasa-medium", "Nasa-high"],
                "output": "/msfc/nasa_mbr.m3u8"
            }
        ]
    }


Transcoding
-----------

``hlsclient`` is also able to create an audio only track from a video stream using FFMPEG.

To do so, add a ``transcode`` action an include the new stream on a combine action:

::

    "actions": [
        {
            "type": "combine",
            "input": ["Nasa-audio-only", "Nasa-low", "Nasa-medium", "Nasa-high"],
            "output": "/msfc/nasa_mbr.m3u8"
        },
        {
            "type": "transcode",
            "input": "Nasa-low",
            "output": {
                "audio": {
                    "Nasa-audio-only": {
                        "path": "Nasa-audio-only.m3u8",
                        "audio-bitrate": 64000,
                        "bitrate": 65000
                    }
                }
            }
        }
    ]


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
