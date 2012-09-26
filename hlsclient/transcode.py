from sh import ffmpeg

def transcode(src, output):
    args = ["-threads", len(output)]
    args += ["-i", src]
    for output_file in output:
        if output_file["type"] == "audio":
            args += ["-vn"]
            args += ["-ar", "44100"]
            args += ["-acodec", "copy"]
            args += ["-ac", 2]
            args += ["-ab", 192000]
            args += [output_file["path"]]
        else:
            raise NotImplementedError
    ffmpeg(args)
