import os
import tempfile

class AtomicWriteFile(object):
    """Returns a temporary filename that will be moved to the
    final destination when closed."""

    def __init__(self, filename):
        self.filename = filename

        dirname = os.path.dirname(filename)
        _, ext = os.path.splitext(filename)
        fd, self.tmp_filename = tempfile.mkstemp(dir=dirname, suffix=ext)
        os.close(fd)
        os.chmod(self.tmp_filename, 0644)

    def __enter__(self):
        return self.tmp_filename

    def __exit__(self, exception_type, exception_val, trace):
        os.rename(self.tmp_filename, self.filename)


class AtomicWriteFileObj(AtomicWriteFile):
    """Returns a handler to a temporary file that will be moved to the
    final destination when closed."""

    def __enter__(self):
        self.handler = open(self.tmp_filename, 'wb')
        return self.handler

    def __exit__(self, exception_type, exception_val, trace):
        self.handler.close()
        super(AtomicWriteFileObj, self).__exit__(exception_type, exception_val, trace)
