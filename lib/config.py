import os
import logging
import json

logger = logging.getLogger(__name__)


CONFIG = {
    'MOUNTS': ['/media'],
    'DESTINATIONS': ['/tmp/autodl'],
    'LOG_LEVEL': 'INFO',
}


logger.info("Loading config from %s", os.path.abspath('config.json'))
with open('config.json', 'r') as fp:
    CONFIG.update(json.load(fp))
