import os

import bottle

from lib.config import CONFIG
from lib import util, dl


bottle.TEMPLATE_PATH.append('web/views')
app = bottle.Bottle()


@app.route('/static/<filename:path>')
def static(filename):
    return bottle.static_file(filename, root='web/static')


@app.route('/')
@bottle.view('index')
def index():
    def get_dest(path):
        path = os.path.abspath(os.path.expanduser(path))
        res = os.statvfs(path)

        return {
            'path': path,
            'size': res.f_blocks * res.f_frsize,
            'avail': res.f_bfree * res.f_frsize,
        }

    destinations = list(map(get_dest, CONFIG['DESTINATIONS']))

    def get_card(args):
        path, files = args
        num = 0
        sz = 0
        for f in files:
            num += 1
            sz += os.path.getsize(f)
        return os.path.basename(path), {'size': sz, 'files': num}

    cards = dict(map(get_card, dl.get_cards().values()))
    total_size = sum([s['size'] for s in cards.values()])

    return {'destinations': destinations, 'cards': cards, 'total_size': total_size, 'util': util}