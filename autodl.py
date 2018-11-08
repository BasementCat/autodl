import os
import uuid
import logging

from inotify_simple import INotify, flags, masks

logger = logging.getLogger('autodl')
logging.basicConfig(level=logging.DEBUG)

from lib.config import CONFIG

logging.getLogger().setLevel(getattr(logging, CONFIG['LOG_LEVEL'].upper()))


def get_inotify():
    inotify = INotify()
    watch_flags = masks.ALL_EVENTS
    logger.debug("inotify flags: %s", watch_flags)
    for path in CONFIG['MOUNTS']:
        logger.info("Watching path %s", path)
        wd = inotify.add_watch(path, watch_flags)
    return inotify


def read_events(inotify):
    for event in inotify.read(timeout=10000, read_delay=1000):
        if event.name:
            ev_flags = list(flags.from_mask(event.mask))
            if flags.ISDIR in ev_flags and flags.CREATE in ev_flags:
                # TODO: if the same path exists in multiple watched directories, this could result in bugs
                # Threading could be a solution for this, if necessary
                for path in CONFIG['MOUNTS']:
                    candidate = os.path.join(path, event.name)
                    if os.path.exists(candidate) and os.path.ismount(candidate):
                        path_in_dest = False
                        for dest_path in CONFIG['DESTINATIONS']:
                            dest_path = os.path.abspath(dest_path)
                            if candidate.startswith(dest_path):
                                logger.debug("Ignore mounted folder %s because it's inside destination %s", candidate, dest_path)
                                path_in_dest = True
                                break

                        if not path_in_dest:
                            logger.info("Mounted %s", candidate)
                            yield candidate


def get_card_id(mountpoint, default=None):
    card_id_file = os.path.join(mountpoint, 'autodl-card-id.txt')
    try:
        with open(card_id_file, 'r') as fp:
            card_id = fp.read().split('\n')[0].strip()
            logger.debug("Read card ID %s from %s", card_id, card_id_file)
            return card_id
    except (IOError, OSError):
        logger.debug("No card ID in %s, generating one", mountpoint)

    card_id = default or str(uuid.uuid4())
    with open(card_id_file, 'w') as fp:
        fp.write(card_id)
    logger.debug("Wrote card ID %s to %s", card_id, card_id_file)
    return card_id


def get_destinations_for_card(mountpoint):
    card_id = get_card_id(mountpoint)
    card_name = os.path.basename(mountpoint)
    for dest in CONFIG['DESTINATIONS']:
        num = 0
        while True:
            candidate = os.path.abspath(os.path.expanduser(os.path.join(dest, card_name)))
            if num > 0:
                candidate += '-' + str(num)
            if not os.path.exists(candidate):
                os.makedirs(candidate)
                logger.debug("Created new destination %s for card %s", candidate, mountpoint)
                yield candidate
                break
            else:
                dest_card_id = get_card_id(candidate, default=card_id)
                if card_id == dest_card_id:
                    logger.debug("Found existing destination %s for card %s", candidate, mountpoint)
                    yield candidate
                    break
            num += 1


def get_files(src_dir):
    for root, dirs, files in os.walk(src_dir):
        for f in files:
            yield os.path.join(root, f)


def get_missing_destinations(src_dir, src_file, dest_dirs):
    fname = os.path.relpath(src_file, start=src_dir)
    src_stat = os.stat(src_file)
    for dest_dir in dest_dirs:
        candidate = os.path.join(dest_dir, fname)
        if os.path.exists(candidate):
            dest_stat = os.stat(candidate)
            if src_stat.st_size != dest_stat.st_size or src_stat.st_mtime != dest_stat.st_mtime:
                yield src_stat, candidate
        else:
            yield src_stat, candidate


def copy_file(src_file, dest_files):
    src_fp = None
    dest_fps = []
    try:
        src_fp = open(src_file, 'rb')
        for _, dest_fname in dest_files:
            dest_dir = os.path.dirname(dest_fname)
            os.makedirs(dest_dir, exist_ok=True)
            dest_fps.append(open(dest_fname, 'wb'))
            logger.info("Copy %s to %s", src_file, dest_fname)

        while True:
            data = src_fp.read(100000)
            if not len(data):
                break
            for fp in dest_fps:
                written = 0
                while written < len(data):
                    written += fp.write(data[written:])

        for stat, fname in dest_files:
            os.utime(fname, (stat.st_atime_ns, stat.st_mtime))
    finally:
        if src_fp:
            src_fp.close()
        for fp in dest_fps:
            fp.close()


inotify = get_inotify()
while True:
    for path in read_events(inotify):
        dests = list(get_destinations_for_card(path))
        for fname in get_files(path):
            missing_dests = list(get_missing_destinations(path, fname, dests))
            if not missing_dests:
                continue
            copy_file(fname, missing_dests)
        logger.info("Unmounting %s", path)
        os.system('umount ' + path)
