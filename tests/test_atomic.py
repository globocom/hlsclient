import os

from hlsclient import atomic

def test_atomic_write_creates_a_temp_file_and_destroys_it(tmpdir):
    finalfile = str(tmpdir.join('myfile.m3u8'))
    with atomic.AtomicWriteFile(finalfile) as f:
        tempfile = f
        assert tempfile.endswith('m3u8')
        assert os.path.exists(tempfile)
        assert not os.path.exists(finalfile)
    assert os.path.exists(finalfile)
    assert not os.path.exists(tempfile)

def test_atomic_write_object_is_writable(tmpdir):
    final = str(tmpdir.join('myfile.m3u8'))
    with atomic.AtomicWriteFileObj(final) as f:
        f.write('test')
        assert not os.path.exists(final)
    assert os.path.exists(final)
    assert open(final, 'r').read() == 'test'
