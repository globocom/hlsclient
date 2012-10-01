import logging
import os

from sh import ffmpeg

# FIXME: not tested
# FIXME: transcode video
def transcode_segments(playlists, modified_playlist, segments, m3u8_path):
    for action in playlists.get('actions', {}):
        if action['type'] == 'transcode' and action['input'] == modified_playlist:
            for new_audio_stream in action['output'].get('audio', {}).values():
                extract_audio_from_segments(segments)
                create_transcoded_audio_m3u8(m3u8_path, new_audio_stream)

# FIXME: not tested
# FIXME: should not treat (read/dump) m3u8 as strings
# FIXME: should pass bitrate to transcode function
def create_transcoded_audio_m3u8(original_m3u8_path, new_audio_stream):
    content = open(original_m3u8_path, 'r').read()
    new_content = content.replace('.ts', '.aac')
    new_m3u8_path = os.path.join(os.path.dirname(original_m3u8_path), new_audio_stream['path'])
    with open(new_m3u8_path, 'w') as f:
        f.write(new_content)

def extract_audio_from_segments(segments):
    for segment in segments:
        output_path = segment.replace('.ts', '.aac')
        logging.info('transcoding from {segment} to {path}'.format(segment=segment, path=output_path))
        transcode(segment, output=[{"path": output_path, "type": "audio"}])

def transcode(src, output):
    args = ["-y"]
    args += ["-threads", len(output)]
    args += ["-i", src]
    for output_file in output:
        if output_file["type"] == "audio":
            args += ["-vn"]
            args += ["-ar", 44100]
            args += ["-acodec", "copy"]
            args += ["-ac", 2]
            args += ["-ab", 192000]
            args += [output_file["path"]]
        elif output_file["type"] == "video":
            args += ["-b:v", output_file["bitrate"] * 1000]
            args += "-f mpegts -acodec libfaac -ar 48000 -ab 64k -vcodec libx264 -flags +loop -cmp +chroma -subq 5 -trellis 1 -refs 1 -coder 0 -me_range 16 -keyint_min 25 -sc_threshold 40 -i_qfactor 0.71 -bt 200k -maxrate 96k -bufsize 96k -rc_eq 'blurCplx^(1-qComp)' -qcomp 0.6 -qmin 10 -qmax 51 -qdiff 4 -level 30 -aspect 320:240 -g 30 -s 320x240".split(' ')
            args += [output_file["path"]]
        else:
            raise NotImplementedError("Unsupported type")
    logging.debug('Calling FFMPEG with args={args}'.format(args=' '.join(map(str, args))))
    ffmpeg(args)
