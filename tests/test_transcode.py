from sh import mediainfo
from hlsclient.transcode import transcode

def test_extracts_audio_from_ts(tmpdir):
    output_path = tmpdir.join("output.aac")
    transcode(src="tests/data/tvglobo.ts", output=[{"path": str(output_path), "type": "audio"}])
    assert output_path.check()

    info = mediainfo(str(output_path))
    assert 'Audio Data Transport Stream' in info
    assert 'Advanced Audio Codec' in info
