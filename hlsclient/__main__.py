import sys

from workers.master import MasterWorker
from workers.playlist import PlaylistWorker

if __name__ == "__main__":
    if len(sys.argv) > 1:
        worker = PlaylistWorker(*sys.argv[1:])
        worker.run_forever()
    else:
        master = MasterWorker()
        master.run_forever()
