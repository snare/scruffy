import logging
from scruffy import Plugin

log = logging.getLogger('main')

class SomePlugin(Plugin):
    def do_a_thing(self):
        log.info("{}.{} is doing a thing!".format(__name__, self.__class__.__name__))