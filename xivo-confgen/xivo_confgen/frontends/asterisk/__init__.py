# -*- coding: utf8 -*-
from xivo_confgen.frontends.asterisk.extensionsconf import ExtensionsConf

__author__ = "Guillaume Bour <gbour@proformatique.com>"
__license__ = """
    Copyright (C) 2010-2011  Avencall

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
import re
from xivo             import OrderedConf
from xivo             import xivo_helpers

from StringIO        import StringIO
from xivo_confgen.frontend import Frontend
from xivo_confgen.frontends.asterisk.voicemail import VoicemailConf
from xivo_confgen.frontends.asterisk.sccp import SccpConf


class AsteriskFrontend(Frontend):
    def sccp_conf(self):
        output = StringIO()
        sccp_conf = SccpConf.new_from_backend(self.backend)
        sccp_conf.generate(output)
        return output.getvalue()

    def sip_conf(self):
        """
            output - output stream. write to it with *print >>output, 'blablabla'*
        """
        output = StringIO()

        ## section::general
        data_sip_general = self.backend.sip.all(commented=False)
        print >> output, self._gen_sip_general(data_sip_general)

        ## section::authentication
        data_sip_authentication = self.backend.sipauth.all()
        print >> output, self._gen_sip_authentication(data_sip_authentication)

        # section::trunks
        for trunk in self.backend.siptrunks.all(commented=False):
            print >> output, self._gen_sip_trunk(trunk)

        # section::users (xivo lines)
        pickups = {}
        for p in self.backend.pickups.all(usertype='sip'):
            user = pickups.setdefault(p[0], {})
            user.setdefault(p[1], []).append(str(p[2]))

        for user in self.backend.sipusers.all(commented=False):
            print >> output, self.gen_sip_user(user, pickups)
        return output.getvalue()

    def _gen_sip_general(self, data_sip_general):
        output = StringIO()
        print >> output, '[general]'
        for item in data_sip_general:
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
        return output.getvalue()

    def _gen_sip_authentication(self, data_sip_authentication):
        output = StringIO()
        if len(data_sip_authentication) > 0:
            print >> output, '\n[authentication]'
            for auth in data_sip_authentication:
                mode = '#' if auth['secretmode'] == 'md5' else ':'
                print >> output, "auth = %s%s%s@%s" % (auth['user'], mode, auth['secret'], auth['realm'])
        return output.getvalue()

    def _gen_sip_trunk(self, data_sip_trunk):
        output = StringIO()
        print >> output, "\n[%s]" % data_sip_trunk['name']

        for k, v in data_sip_trunk.iteritems():
            if k in ('id', 'name', 'protocol', 'category', 'commented', 'disallow') or v in (None, ''):
                continue

            if isinstance(v, unicode):
                v = v.encode('utf8')

            if v == 'allow':
                print >> output, "disallow = all"
                for c in v.split(','):
                    print >> output, "allow = " + str(c)
            else:
                print >> output, k, '=', v
        return output.getvalue()

    def gen_sip_user(self, user, pickups):
        sipUnusedValues = ('id', 'name', 'protocol',
                       'category', 'commented', 'initialized',
                       'disallow', 'regseconds', 'lastms',
                       'name', 'fullcontact', 'ipaddr',)
        output = StringIO()
        print >> output, "\n[%s]" % user['name']

        for key, value in user.iteritems():
            if key in sipUnusedValues or value in (None, ''):
                continue

            if key not in ('allow', 'subscribemwi'):
                print >> output, self._gen_value_line(key, value)

            if key == 'allow' :
                print >> output, self._gen_value_line('disallow', 'all')
                for codec in value.split(','):
                    print >> output, self._gen_value_line("allow", codec)

            if key == 'subscribemwi' :
                value = 'no' if value == 0 else 'yes'
                print >> output, self._gen_value_line('subscribemwi', value)

        if user['name'] in pickups:
            p = pickups[user['name']]
            #WARNING: 
            # pickupgroup: trappable calls  (xivo members)
            # callgroup  : can pickup calls (xivo pickups)
            if 'member' in p:
                print >> output, "pickupgroup = " + ','.join(frozenset(p['member']))
            if 'pickup' in p:
                print >> output, "callgroup = " + ','.join(frozenset(p['pickup']))
        return output.getvalue()

    def _gen_value_line(self, key, value):
        return u'%s = %s' % (key, self._unicodify_string(value))

    def _get_is_not_none(self, data, key):
        if key in data:
            value = data[key]
            return '' if value is None else self._unicodify_string(value)
        else:
            return ''

    def _unicodify_string(self, str):
        try:
            return unicode(str)
        except UnicodeDecodeError:
            return unicode(str.decode('utf8'))

    def iax_conf(self):
        output = StringIO()

        ## section::general
        print >> output, self._gen_iax_general(self.backend.iax.all(commented=False))

        ## section::authentication
        items = self.backend.iaxcalllimits.all()
        if len(items) > 0:
            print >> output, '\n[callnumberlimits]'
            for auth in items:
                print >> output, "%s/%s = %s" % (auth['destination'], auth['netmask'], auth['calllimits'])

        # section::trunks
        for trunk in self.backend.iaxtrunks.all(commented=False):
            print >> output, self._gen_iax_trunk(trunk)

        # section::users
        print >> output, self._gen_iax_users(self.backend.iaxusers.all(commented=False))

        return output.getvalue()

    def _gen_iax_general(self, data_iax_general):
        output = StringIO()

        print >> output, '[general]'
        for item in data_iax_general:
            if item['var_val'] is None:
                continue

            if item['var_name'] == 'register':
                print >> output, item['var_name'], "=>", item['var_val']

            elif item['var_name'] not in ['allow', 'disallow']:
                print >> output, "%s = %s" % (item['var_name'], item['var_val'])

            elif item['var_name'] == 'allow':
                print >> output, 'disallow = all'
                for c in item['var_val'].split(','):
                    print >> output, 'allow = %s' % c

        return output.getvalue()

    def _gen_iax_users(self, data_iax_users):
        output = StringIO()

        for user in data_iax_users:
            print >> output, "\n[%s]" % user['name']

            for k, v in user.iteritems():
                if k in ('id', 'name', 'protocol', 'category', 'commented', 'initialized', 'disallow') or\
                     v in (None, ''):
                    continue

                if isinstance(v, unicode):
                    v = v.encode('utf8')

                if k == 'allow' and v != None:
                    print >> output, "disallow = all"
                    for c in v.split(','):
                        print >> output, "allow = " + str(c)
                else:
                    print >> output, k, "=", str(v)

        return output.getvalue()

    def _gen_iax_trunk(self, trunk):
        output = StringIO()

        print >> output, "\n[%s]" % trunk['name']

        for k, v in trunk.iteritems():
            if k in ('id', 'name', 'protocol', 'category', 'commented', 'disallow') or v in (None, ''):
                continue

            if isinstance(v, unicode):
                v = v.encode('utf8')

            if k == 'allow' and v != None:
                print >> output, "disallow = all"
                for c in v.split(','):
                    print >> output, "allow = " + str(c)
            else:
                print >> output, k + " = ", v

        return output.getvalue()

    def voicemail_conf(self):
        # XXX there might be a bit too much boilerplate
        output = StringIO()
        voicemail_conf = VoicemailConf.new_from_backend(self.backend)
        voicemail_conf.generate(output)
        return output.getvalue()

    def queues_conf(self):
        options = StringIO()

        penalties = dict([(itm['id'], itm['name']) for itm in self.backend.queuepenalty.all(commented=False)])

        print >> options, '\n[general]'
        for item in self.backend.queue.all(commented=False, category='general'):
            print >> options, "%s = %s" % (item['var_name'], item['var_val'])

        for q in self.backend.queues.all(commented=False, order='name'):
            print >> options, '\n[%s]' % q['name']

            for k, v in q.iteritems():
                if k in ('name', 'category', 'commented') or v is None or \
                        (isinstance(v, (str, unicode)) and len(v) == 0):
                    continue

                if k == 'defaultrule':
                    if not int(v) in penalties:
                        continue
                    v = penalties[int(v)]

                print >> options, k, '=', v

            for m in self.backend.queuemembers.all(commented=False, queue_name=q['name']):
                options.write("member => %s" % m['interface'])
                if m['penalty'] > 0:
                    options.write(",%d" % m['penalty'])
                options.write('\n')

        return options.getvalue()

    def agents_conf(self):
        options = StringIO()

        print >> options, '\n[general]'
        for c in self.backend.agent.all(commented=False, category='general'):
            print >> options, "%s = %s" % (c['var_name'], c['var_val'])

        print >> options, '\n[agents]'
        for c in self.backend.agent.all(commented=False, category='agents'):
            if c['var_val'] is None or c['var_name'] == 'agent':
                continue

            print >> options, "%s = %s" % (c['var_name'], c['var_val'])

        print >> options, ''
        for a in self.backend.agentusers.all(commented=False):
            for k, v in a.items():
                if k == 'var_val':
                    continue

                print >> options, "%s = %s" % (k, v)

            print >> options, "agent =>", a['var_val'], "\n"

        return options.getvalue()

    def meetme_conf(self):
        options = StringIO()

        print >> options, '\n[general]'
        for c in self.backend.meetme.all(commented=False, category='general'):
            print >> options, "%s = %s" % (c['var_name'], c['var_val'])

        print >> options, '\n[rooms]'
        for r in self.backend.meetme.all(commented=False, category='rooms'):
            print >> options, "%s = %s" % (r['var_name'], r['var_val'])

        return options.getvalue()

    def musiconhold_conf(self):
        options = StringIO()

        cat = None
        for m in self.backend.musiconhold.all(commented=False, order='category'):
            if m['var_val'] is None:
                continue

            if m['category'] != cat:
                cat = m['category']; print >> options, '\n[%s]' % cat

            print >> options, "%s = %s" % (m['var_name'], m['var_val'])

        return options.getvalue()

    def features_conf(self):
        options = StringIO()

        print >> options, '\n[general]'
        for f in self.backend.features.all(commented=False, category='general'):
            print >> options, "%s = %s" % (f['var_name'], f['var_val'])

        # parkinglots
        for f in self.backend.parkinglot.all(commented=False):
            print >> options, "\n[parkinglot_%s]" % f['name']
            print >> options, "context => %s" % f['context']
            print >> options, "parkext => %s" % f['extension']
            print >> options, "parkpos => %d-%d" % (int(f['extension']) + 1, int(f['extension']) + f['positions'])
            if f['next'] == 1:
                print >> options, "findslot => next"

            mmap = {
                'duration'     : 'parkingtime',
                'calltransfers': 'parkedcalltransfers',
                'callreparking': 'parkedcallreparking',
                'callhangup'   : 'parkedcallhangup',
                'callreparking': 'parkedcallreparking',
                'musicclass'   : 'parkedmusicclass',
                'hints'        : 'parkinghints',
            }
            for k, v in mmap.iteritems():
                if f[k] is not None:
                    print >> options, "%s => %s" % (v, str(f[k]))

        print >> options, '\n[featuremap]'
        for f in self.backend.features.all(commented=False, category='featuremap'):
            print >> options, "%s = %s" % (f['var_name'], f['var_val'])

        return options.getvalue()

    def queueskills_conf(self):
        """Generate queueskills.conf asterisk configuration file
        """
        options = StringIO()

        userid = None
        for sk in self.backend.userqueueskills.all():
            if userid != sk['id']:
                print >> options, "\n[user-%d]" % sk['id']
                userid = sk['id']

            print >> options, "%s = %s" % (sk['name'], sk['weight'])

        agentid = None
        for sk in self.backend.agentqueueskills.all():
            if agentid != sk['id']:
                print >> options, "\n[agent-%d]" % sk['id']
                agentid = sk['id']

            print >> options, "%s = %s" % (sk['name'], sk['weight'])

        return options.getvalue()

    def queueskillrules_conf(self):
        """Generate queueskillrules.conf asterisk configuration file
        """
        options = StringIO()

        for r in self.backend.queueskillrules.all():
            print >> options, "\n[%s]" % r['name']

            if 'rule' in r and r['rule'] is not None:
                for rule in r['rule'].split(';'):
                    print >> options, "rule = %s" % rule

        return options.getvalue()

    def extensions_conf(self):
        output = StringIO()
        print self.contextsconf
        extension_conf = ExtensionsConf.new_from_backend(self.backend,self.contextsconf)
        extension_conf.generate(output)
        return output.getvalue()
    
    def queuerules_conf(self):
        options = StringIO()

        rule = None
        for m in self.backend.queuepenalties.all():
            if m['name'] != rule:
                rule = m['name']; print >> options, "\n[%s]" % rule

            print >> options, "penaltychange => %d," % m['seconds'],
            if m['maxp_sign'] is not None and m['maxp_value'] is not None:
                sign = '' if m['maxp_sign'] == '=' else m['maxp_sign']
                print >> options, "%w%d" % (sign, m['maxp_value']),

            if m['minp_sign'] is not None and m['minp_value'] is not None:
                sign = '' if m['minp_sign'] == '=' else m['minp_sign']
                print >> options, ",%s%d" % (sign, m['minp_value']),

            print >> options

        return options.getvalue()

    def dundi_conf(self):
        options = StringIO()

        print >> options, "[general]"
        general = self.backend.dundi.get(id=1)
        for k, v in general.iteritems():
            if v is None or k == 'id':
                continue

            if isinstance(v, unicode):
                v = v.encode('utf8')
            print >> options, k, "=", v

        trunks = dict([(t['id'], t) for t in self.backend.trunks.all()])

        print >> options, "\n[mappings]"
        for m in self.backend.dundimapping.all(commented=False):
            #dundi_context => local_context,weight,tech,dest[,options]]
            _t = trunks.get(m.trunk, {})
            _m = "%s => %s,%s,%s,%s:%s@%s/%s" % \
                    (m['name'], m['context'], m['weight'],
                    _t.get('protocol', '').upper(), _t.get('username', ''), _t.get('', 'secret'),
                    _t['host']  if _t.get('host', 'dynamic') != 'dynamic' else '${IPADDR}',
                    m['number'] if m['number'] is not None else '${NUMBER}',
            )

            for k in ('nounsolicited', 'nocomunsolicit', 'residential', 'commercial', 'mobile', 'nopartial'):
                if m[k] == 1:
                    _m += ',' + k

            print >> options, _m

        # peers
        for p in self.backend.dundipeer.all(commented=False):
            print >> options, "\n[%s]" % p['macaddr']

            for k, v in p.iteritems():
                if k in ('id', 'macaddr', 'description', 'commented') or v is None:
                    continue

                print >> options, "%s = %s" % (k, v)

        return options.getvalue()

    def chan_dahdi_conf(self):
        options = StringIO()

        print >> options, "[channels]"
        for k, v in self.backend.dahdi.get(id=1).iteritems():
            if v is None or k == 'id':
                continue

            if isinstance(v, unicode):
                v = v.encode('utf8')
            print >> options, k, "=", v

        print >> options
        for group in self.backend.dahdigroup.all(commented=False):
            print >> options, "\ngroup=%d" % group['groupno']

            for k in ('context', 'switchtype', 'signalling', 'callerid', 'mailbox'):
                if group[k] is not None:
                    print >> options, k, "=", group[k]

            print >> options, "channel => %s" % group['channels']

        return options.getvalue()

