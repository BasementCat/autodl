import os
import logging

logger = logging.getLogger('autodl')
logging.basicConfig(level=logging.DEBUG)

from lib.config import CONFIG
from lib.led import LED, Blink, ExtBlink
from lib import dl

logging.getLogger().setLevel(getattr(logging, CONFIG['LOG_LEVEL'].upper()))


def run_autodl():
    with LED(CONFIG['LED']) as led:
        with Blink(led, 1):
            inotify = dl.get_inotify()
            while True:
                for path in dl.read_events(inotify):
                    with ExtBlink(led, 0.1, on_count=3, cycle_time=1):
                        dests = list(dl.get_destinations_for_card(path))
                        for fname in dl.get_files(path):
                            missing_dests = list(dl.get_missing_destinations(path, fname, dests))
                            if not missing_dests:
                                continue
                            dl.copy_file(fname, missing_dests)
                        logger.info("Unmounting %s", path)
                        os.system('umount ' + path)


if __name__ == '__main__':
    run_autodl()