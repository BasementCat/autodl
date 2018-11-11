import time
import os
import subprocess
import logging
import threading
from wsgiref.simple_server import make_server

logger = logging.getLogger('autodl')
logging.basicConfig(level=logging.DEBUG)

from lib.config import CONFIG
from lib.led import LED, Blink, ExtBlink
from lib import dl

from web import app as webapp

logging.getLogger().setLevel(getattr(logging, CONFIG['LOG_LEVEL'].upper()))


def run_autodl(stop_event=None):
    with LED(CONFIG['LED']) as led:
        with Blink(led, 1):
            inotify = dl.get_inotify()
            while (True if stop_event is None else not stop_event.is_set()):
                for path in dl.read_events(inotify):
                    with ExtBlink(led, 0.1, on_count=3, cycle_time=1):
                        dests = list(dl.get_destinations_for_card(path))
                        for fname in dl.get_files(path):
                            missing_dests = list(dl.get_missing_destinations(path, fname, dests))
                            if not missing_dests:
                                continue
                            dl.copy_file(fname, missing_dests)
                        logger.info("Unmounting %s", path)
                        subprocess.call(['umount', path])
                        # os.system('umount ' + path)


def create_web():
    server = make_server('', 8000, webapp)
    return server


def start_web(server):
    server.serve_forever()


def run_web(server, stop_event):
    while not stop_event.is_set():
        time.sleep(1)
    server.shutdown()


if __name__ == '__main__':
    stop_event = threading.Event()
    threads = []

    threads.append(threading.Thread(target=run_autodl, kwargs={'stop_event': stop_event}))

    webserver = create_web()
    threads.append(threading.Thread(target=start_web, kwargs={'server': webserver}))
    threads.append(threading.Thread(target=run_web, kwargs={'server': webserver, 'stop_event': stop_event}))

    for t in threads:
        t.start()

    try:
        while True:
            time.sleep(1)
    finally:
        stop_event.set()
        for t in threads:
            t.join()
