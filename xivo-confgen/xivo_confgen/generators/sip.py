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


class SipConf(object):
    def __init__(self, general, authentication, trunk, pickups, user):
        self._general = general
        self._authentication = authentication
        self._trunk = trunk
        self._pickups = pickups
        self._user = user

    def generate(self, output):
        self._gen_general(self._general, output)
        print >> output
        self._gen_authentication(self._authentication, output)
        print >> output
        self._gen_trunk(self._trunk, output)
        print >> output
        self._gen_user(self._user, output)

    def _gen_general(self, data_general, output):
        print >> output, '[general]'
        for item in data_general:
            if item['var_val'] is None:
                continue

            if item['var_name'] in ('register', 'mwi'):
                print >> output, item['var_name'], "=>", item['var_val']

            elif item['var_name'] not in ['allow', 'disallow']:
                print >> output, item['var_name'], "=", item['var_val']

            elif item['var_name'] == 'allow':
                print >> output, 'disallow = all'
                for c in item['var_val'].split(','):
                    print >> output, 'allow = %s' % c

    def _gen_authentication(self, data_authentication, output):
        if len(data_authentication) > 0:
            print >> output, '\n[authentication]'
            for auth in data_authentication:
                mode = '#' if auth['secretmode'] == 'md5' else ':'
                print >> output, "auth = %s%s%s@%s" % (auth['user'], mode, auth['secret'], auth['realm'])

    def _gen_trunk(self, data_trunk, output):
        for trunk in data_trunk:
            print >> output, "\n[%s]" % trunk['name']

            for k, v in trunk.iteritems():
                if k in ('id', 'name', 'protocol', 'category', 'commented', 'disallow') or v in (None, ''):
                    continue

                if isinstance(v, unicode):
                    v = v.encode('utf8')

                if k == 'allow':
                    print >> output, "disallow = all"
                    for c in v.split(','):
                        print >> output, "allow = " + str(c)
                else:
                    print >> output, k, '=', v

    def _gen_user(self, data_user, output):
        sipUnusedValues = ('id', 'name', 'protocol',
                       'category', 'commented', 'initialized',
                       'disallow', 'regseconds', 'lastms',
                       'name', 'fullcontact', 'ipaddr',)

        pickups = {}
        for p in self._pickups:
            user = pickups.setdefault(p[0], {})
            user.setdefault(p[1], []).append(str(p[2]))

        for user in data_user:
            print >> output, "\n[%s]" % user['name']

            for key, value in user.iteritems():
                if key in sipUnusedValues or value in (None, ''):
                    continue

                if key not in ('allow', 'subscribemwi'):
                    print >> output, gen_value_line(key, value)

                if key == 'allow' :
                    print >> output, gen_value_line('disallow', 'all')
                    for codec in value.split(','):
                        print >> output, gen_value_line("allow", codec)

                if key == 'subscribemwi' :
                    value = 'no' if value == 0 else 'yes'
                    print >> output, gen_value_line('subscribemwi', value)
		
		print >> output, "cc_agent_policy = generic"
		print >> output, "cc_monitor_policy = generic"

            if user['name'] in pickups:
                p = pickups[user['name']]
                #WARNING:
                # pickupgroup: trappable calls  (xivo members)
                # callgroup  : can pickup calls (xivo pickups)
                if 'member' in p:
                    print >> output, "pickupgroup = " + ','.join(frozenset(p['member']))
                if 'pickup' in p:
                    print >> output, "callgroup = " + ','.join(frozenset(p['pickup']))

    @classmethod
    def new_from_backend(cls, backend):
        general = backend.sip.all(commented=False)
        authentication = backend.sipauth.all()
        trunk = backend.siptrunks.all(commented=False)
        pickups = backend.pickups.all(usertype='sip')
        user = backend.sipusers.all(commented=False)
        return cls(general, authentication, trunk, pickups, user)


def gen_value_line(key, value):
    return u'%s = %s' % (key, unicodify_string(value))


def unicodify_string(str):
    try:
        return unicode(str)
    except UnicodeDecodeError:
        return str.decode('utf8')
