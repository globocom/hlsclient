from copy import copy
import logging
import os

import m3u8
from subprocess import Popen

DEFAULT_VIDEO_ARGS = "-f mpegts -acodec libfaac -ar 48000 -ab 64k -vcodec libx264 -flags +loop -cmp +chroma -subq 5 -trellis 1 -refs 1 -coder 0 -me_range 16 -keyint_min 25 -sc_threshold 40 -i_qfactor 0.71 -maxrate 96k -bufsize 96k -rc_eq 'blurCplx^(1-qComp)' -qcomp 0.6 -qmin 10 -qmax 51 -qdiff 4 -level 30 -g 30".split(' ')

def transcode_playlist(playlists, modified_playlist, segments, m3u8_path):
    output = list(get_audio_outputs(playlists, modified_playlist))
    if output:
        transcode_segments(segments, m3u8_path, output)
        for output_stream in output:
            create_transcoded_m3u8(m3u8_path, output_stream)

def get_audio_outputs(playlists, modified_playlist):
    for action in playlists.get('actions', {}):
        if action['type'] == 'transcode' and action['input'] == modified_playlist:
            for audio_action in action['output'].get('audio', {}).values(): # FIXME: filtering audio only
                yield audio_action

def transcode_segments(segments, original_m3u8_path, output):
    for segment in segments:
        transcode_segment(segment, original_m3u8_path, output)

def transcode_segment(segment, original_m3u8_path, output):
    output_options = []
    for output_stream in output:
        output_options.append(get_transcode_options_for_segment(segment, output_stream))
    transcode(segment, output=output_options)

def get_transcode_options_for_segment(segment, output_stream):
    output_path = new_chunk_path(segment, output_stream)
    logging.info('transcoding from {segment} to {path}'.format(segment=segment, path=output_path))
    options = copy(output_stream)
    options.update({"path": output_path, "type": "audio"}) # FIXME: audio only options
    return options

def create_transcoded_m3u8(original_m3u8_path, output_stream):
    playlist = m3u8.load(original_m3u8_path)
    for segment in playlist.segments:
        segment.uri = new_chunk_path(segment.uri, output_stream)
    new_m3u8_path = os.path.join(os.path.dirname(original_m3u8_path), output_stream['path'])
    playlist.dump(new_m3u8_path)

def new_chunk_path(path, output_stream):
    # FIXME: filtering audio only
    return path.replace('.ts', '.aac')

def transcode(src, output):
    args = ["ffmpeg"]
    args += ["-y"]
    args += ["-loglevel", "quiet"]
    args += ["-threads", str(len(output) * 4)]
    args += ["-i", src]
    for output_file in output:
        if output_file["type"] == "audio":
            args += ["-vn"]
            args += ["-acodec", "copy"]
            if "audio-bitrate" in output_file:
                args += ["-b:a", output_file["audio-bitrate"]]
            args += [output_file["path"]]
        elif output_file["type"] == "video":
            if "video-bitrate" in output_file:
                args += ["-b:v", output_file["video-bitrate"]]
            args += ["-s", output_file.get("size", "320x240")]
            args += DEFAULT_VIDEO_ARGS
            args += [output_file["path"]]
        else:
            raise NotImplementedError("Unsupported type")

    args = map(str, args)

    logging.debug('Calling FFMPEG with args={args}'.format(args=' '.join(args)))
    Popen(args).communicate()
