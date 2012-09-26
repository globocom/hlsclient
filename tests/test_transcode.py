from sh import mediainfo
from hlsclient.transcode import transcode

def test_extracts_audio_from_ts(tmpdir):
    output_path = tmpdir.join("output.aac")
    transcode(src="tests/data/tvglobo.ts", output=[{"path": str(output_path), "type": "audio"}])
    assert output_path.check()

    info = mediainfo(str(output_path))
    assert 'Audio Data Transport Stream' in info
    assert 'Advanced Audio Codec' in info

def test_transcode_video_and_audio_from_ts(tmpdir):
    audio_output_path = tmpdir.join("output.aac")
    video_output_path = tmpdir.join("tvglobo_200.ts")
    transcode(src="tests/data/tvglobo.ts", output=[
        {"path": str(video_output_path), "type": "video", "bitrate": 200, "path": video_output_path},
        {"path": str(audio_output_path), "type": "audio"}
    ])

    assert audio_output_path.check()
    assert video_output_path.check()

    audio_info = mediainfo(str(audio_output_path))
    assert 'Audio Data Transport Stream' in audio_info
    assert 'Advanced Audio Codec' in audio_info

    video_info = mediainfo(str(video_output_path))
    assert 'MPEG-TS' in video_info
    assert 'Advanced Video Codec' in video_info
