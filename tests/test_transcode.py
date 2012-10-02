from xml.dom.minidom import parseString
import sh

from hlsclient.transcode import transcode


def get_media_info(path):
    info = sh.mediainfo(str(path), "--Output=XML")
    return parseString(str(info))

def get_xml_tag_text_value(node, tag):
    return node.getElementsByTagName(tag)[0].firstChild.data

def test_extracts_audio_from_ts(tmpdir):
    output_path = tmpdir.join("output.aac")
    transcode(src="tests/data/sample.ts", output=[{"path": str(output_path), "type": "audio"}])
    assert output_path.check()

    info = get_media_info(str(output_path))

    file_track, audio_track = info.getElementsByTagName("track")
    assert 'Audio Data Transport Stream' == get_xml_tag_text_value(file_track, "Format_Info")
    assert 'Advanced Audio Codec' == get_xml_tag_text_value(audio_track, "Format_Info")

def test_transcode_video_and_audio_from_ts(tmpdir):
    audio_output_path = tmpdir.join("output.aac")
    video_output_path = tmpdir.join("tvglobo_200.ts")
    transcode(src="tests/data/sample.ts", output=[
        {"path": str(video_output_path),
         "type": "video",
         "video-bitrate": 100000,
         "size": "32x24",
         },
        {"path": str(audio_output_path), "type": "audio"}
    ])

    audio_info = get_media_info(str(audio_output_path))
    file_track, audio_track = audio_info.getElementsByTagName("track")
    assert 'Audio Data Transport Stream' == get_xml_tag_text_value(file_track, "Format_Info")
    assert 'Advanced Audio Codec' == get_xml_tag_text_value(audio_track, "Format_Info")

    video_info = get_media_info(str(video_output_path))
    file_track, video_track, audio_track, _ = video_info.getElementsByTagName("track")
    assert 'MPEG-TS' == get_xml_tag_text_value(file_track, "Format")

    assert 'Advanced Video Codec' == get_xml_tag_text_value(video_track, "Format_Info")
    assert '100.0 Kbps' == get_xml_tag_text_value(video_track, "Nominal_bit_rate")
    assert '32 pixels' == get_xml_tag_text_value(video_track, "Width")
    assert '24 pixels' == get_xml_tag_text_value(video_track, "Height")
    assert 'High@L3.0' == get_xml_tag_text_value(video_track, "Format_profile")
    assert 'Advanced Audio Codec' == get_xml_tag_text_value(audio_track, "Format_Info")
