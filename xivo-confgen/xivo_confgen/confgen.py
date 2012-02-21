# -*- coding: UTF-8 -*-

__license__ = """
    Copyright (C) 2011  Avencall

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA..
"""

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
