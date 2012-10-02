from copy import copy
import logging
import os

import sh

DEFAULT_VIDEO_ARGS = "-f mpegts -acodec libfaac -ar 48000 -ab 64k -vcodec libx264 -flags +loop -cmp +chroma -subq 5 -trellis 1 -refs 1 -coder 0 -me_range 16 -keyint_min 25 -sc_threshold 40 -i_qfactor 0.71 -maxrate 96k -bufsize 96k -rc_eq 'blurCplx^(1-qComp)' -qcomp 0.6 -qmin 10 -qmax 51 -qdiff 4 -level 30 -aspect 320:240 -g 30 -s 320x240".split(' ')

def transcode_segments(playlists, modified_playlist, segments, m3u8_path):
    for action in playlists.get('actions', {}):
        if action['type'] == 'transcode' and action['input'] == modified_playlist:
            # FIXME: transcode to video too (we support audio only)
            # FIXME: we should create all transcoded outputs from one segment in one pass
            for new_audio_stream_options in action['output'].get('audio', {}).values():
                extract_audio_from_segments(segments, new_audio_stream_options)
                create_transcoded_audio_m3u8(m3u8_path, new_audio_stream_options)

def create_transcoded_audio_m3u8(original_m3u8_path, new_audio_stream_options):
    # FIXME: should not handle (read/dump) m3u8 as strings
    content = open(original_m3u8_path, 'r').read()
    new_content = content.replace('.ts', '.aac')
    new_m3u8_path = os.path.join(os.path.dirname(original_m3u8_path), new_audio_stream_options['path'])
    with open(new_m3u8_path, 'w') as f:
        f.write(new_content)

def extract_audio_from_segments(segments, new_audio_stream_options):
    for segment in segments:
        output_path = segment.replace('.ts', '.aac')
        logging.info('transcoding from {segment} to {path}'.format(segment=segment, path=output_path))
        options = copy(new_audio_stream_options)
        options.update({"path": output_path, "type": "audio"})
        transcode(segment, output=[options])

def transcode(src, output):
    args = ["-y"]
    args += ["-threads", len(output)]
    args += ["-i", src]
    for output_file in output:
        if output_file["type"] == "audio":
            args += ["-vn"]
            args += ["-b:a", output_file.get("audio-bitrate", 192000)]
            args += [output_file["path"]]
        elif output_file["type"] == "video":
            args += ["-b:v", output_file["bitrate"] * 1000]
            args += DEFAULT_VIDEO_ARGS
            args += ["-bt", output_file.get("video-bitrate", "200k")]
            args += [output_file["path"]]
        else:
            raise NotImplementedError("Unsupported type")
    logging.debug('Calling FFMPEG with args={args}'.format(args=' '.join(map(str, args))))
    sh.ffmpeg(args)
