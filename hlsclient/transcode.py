from sh import ffmpeg

def transcode(src, output):
    args = ["-threads", len(output)]
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
    ffmpeg(args)
