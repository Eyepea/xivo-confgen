from twisted.internet.protocol import Protocol, ServerFactory
import sys
from xivo_confgen import backends, cache
from xivo_confgen.frontends import frontends


def backendOpts(config, name):
    if not config.has_section('backend-' + name):
        return dict()

    return dict(config.items('backend-' + name))

def frontendOpts(config, name):
    if not config.has_section('frontend-' + name):
        return dict()

    return dict(config.items('frontend-' + name))


class Confgen(Protocol):
    def dataReceived(self, data):
        if data[-1] == '\n':
            data = data[:-1]

        print "serving", data

        # 'asterisk/sip.conf' => ('asterisk', 'sip_conf')
        try:
            (frontend, callback) = data.split('/')
            callback = callback.replace('.', '_')
        except:
            print "cannot split"; return

        if frontend not in self.factory.frontends:
            print "callback not found"; return

        try:
            content = getattr(self.factory.frontends[frontend], callback)()
        except Exception, e:
            import traceback
            print e; traceback.print_exc(file=sys.stdout); content = None

        if content is None:
            # get cache content
            print "cache hit on %s" % data
            content = self.factory.cache.get(data).decode('utf8')
        else:
            # write to cache
            self.factory.cache.put(data, content.encode('utf8'))

        self.transport.write(content.encode('utf8'))
        self.transport.loseConnection()


class ConfgendFactory(ServerFactory):
    protocol = Confgen

    def __init__(self, frontnames, backend, cachedir, config):
        backend = getattr(backends, backend)(**backendOpts(config, backend))

        self.frontends = {}
        for f in frontnames:
            self.frontends[f] = frontends[f](backend, **frontendOpts(config, f))

        self.cache = cache.FileCache(cachedir)
