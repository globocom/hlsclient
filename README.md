hls-client
==========

This is a simple Python HLS Client. It consumes a list of remote
playlists, and saves all needed files to serve the playlist
locally: the key, segments, and a modified `m3u8` with
paths normalized.

It also supports backups, i.e., if the same playlist is available
on more than one server, it will track each server status and will
switch to the backup if needed.

Through the `config.ini` it's possible to customize where the files
will be saved and how the streams will be discovered.

We provide one discover module that points to a fixed stream and a
second one that lists all the streams available on a set of Flash
Media Servers (FMS).

Running
--------

To run the client, simply run:

    python -m hlsclient
