import random

from hlsclient.workers.playlist import PlaylistWorker

def test_second_worker_should_see_that_other_is_running(monkeypatch):
    stream_name = "%0x" % random.randint(0, 2**64)
    run_calls = []
    def fake_run(*args):
        run_calls.append(args)
    def fake_stop(*args):
        pass

    first = PlaylistWorker(stream_name)
    monkeypatch.setattr(first, 'run', fake_run)
    monkeypatch.setattr(first, 'stop', fake_stop)

    first.run_if_locking()
    assert 1 == len(run_calls)

    second = PlaylistWorker(stream_name)
    assert True == second.other_is_running()

def test_lock_should_be_updated_when_run(monkeypatch):
    stream_name = "%0x" % random.randint(0, 2**64)
    run_calls = []
    lock_update_calls = []
    def fake_run(*args):
        run_calls.append(args)
    def fake_lock_update(*args):
        lock_update_calls.append(args)
    def fake_stop(*args):
        pass

    worker = PlaylistWorker(stream_name)
    monkeypatch.setattr(worker, 'run', fake_run)
    monkeypatch.setattr(worker, 'stop', fake_stop)
    monkeypatch.setattr(worker.lock, 'update_lock', fake_lock_update)

    worker.run_if_locking()
    assert 1 == len(run_calls)
    assert 1 == len(lock_update_calls)

def test_worker_should_stop_if_someone_else_acquires_lock(monkeypatch):
    stream_name = "%0x" % random.randint(0, 2**64)
    run_calls = []
    stop_calls = []
    def fake_run(*args):
        run_calls.append(args)
    def fake_stop(*args):
        stop_calls.append(args)

    first = PlaylistWorker(stream_name)
    monkeypatch.setattr(first, 'run', fake_run)
    monkeypatch.setattr(first, 'stop', fake_stop)
    first.run_if_locking()

    assert 1 == len(run_calls)
    assert 0 == len(stop_calls)

    run_calls = []
    second = PlaylistWorker(stream_name)
    monkeypatch.setattr(second, 'run', fake_run)
    monkeypatch.setattr(second, 'stop', fake_stop)
    second.run_if_locking()
    assert 0 == len(run_calls)
    assert 1 == len(stop_calls)
