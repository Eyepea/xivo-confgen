# -*- coding: utf8 -*-

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


class AsteriskFrontend(Frontend):
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
        o = StringIO()

        penalties = dict([(itm['id'], itm['name']) for itm in self.backend.queuepenalty.all(commented=False)])

        print >> o, '\n[general]'
        for item in self.backend.queue.all(commented=False, category='general'):
            print >> o, "%s = %s" % (item['var_name'], item['var_val'])

        for q in self.backend.queues.all(commented=False, order='name'):
            print >> o, '\n[%s]' % q['name']

            for k, v in q.iteritems():
                if k in ('name', 'category', 'commented') or v is None or \
                        (isinstance(v, (str, unicode)) and len(v) == 0):
                    continue

                if k == 'defaultrule':
                    if not int(v) in penalties:
                        continue
                    v = penalties[int(v)]

                print >> o, k, '=', v

            for m in self.backend.queuemembers.all(commented=False, queue_name=q['name']):
                o.write("member => %s" % m['interface'])
                if m['penalty'] > 0:
                    o.write(",%d" % m['penalty'])
                o.write('\n')

        return o.getvalue()

    def agents_conf(self):
        o = StringIO()

        print >> o, '\n[general]'
        for c in self.backend.agent.all(commented=False, category='general'):
            print >> o, "%s = %s" % (c['var_name'], c['var_val'])

        print >> o, '\n[agents]'
        for c in self.backend.agent.all(commented=False, category='agents'):
            if c['var_val'] is None or c['var_name'] == 'agent':
                continue

            print >> o, "%s = %s" % (c['var_name'], c['var_val'])

        print >> o, ''
        for a in self.backend.agentusers.all(commented=False):
            for k, v in a.items():
                if k == 'var_val':
                    continue

                print >> o, "%s = %s" % (k, v)

            print >> o, "agent =>", a['var_val'], "\n"

        return o.getvalue()

    def meetme_conf(self):
        o = StringIO()

        print >> o, '\n[general]'
        for c in self.backend.meetme.all(commented=False, category='general'):
            print >> o, "%s = %s" % (c['var_name'], c['var_val'])

        print >> o, '\n[rooms]'
        for r in self.backend.meetme.all(commented=False, category='rooms'):
            print >> o, "%s = %s" % (r['var_name'], r['var_val'])

        return o.getvalue()

    def musiconhold_conf(self):
        o = StringIO()

        cat = None
        for m in self.backend.musiconhold.all(commented=False, order='category'):
            if m['var_val'] is None:
                continue

            if m['category'] != cat:
                cat = m['category']; print >> o, '\n[%s]' % cat

            print >> o, "%s = %s" % (m['var_name'], m['var_val'])

        return o.getvalue()

    def features_conf(self):
        o = StringIO()

        print >> o, '\n[general]'
        for f in self.backend.features.all(commented=False, category='general'):
            print >> o, "%s = %s" % (f['var_name'], f['var_val'])

        # parkinglots
        for f in self.backend.parkinglot.all(commented=False):
            print >> o, "\n[parkinglot_%s]" % f['name']
            print >> o, "context => %s" % f['context']
            print >> o, "parkext => %s" % f['extension']
            print >> o, "parkpos => %d-%d" % (int(f['extension']) + 1, int(f['extension']) + f['positions'])
            if f['next'] == 1:
                print >> o, "findslot => next"

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
                    print >> o, "%s => %s" % (v, str(f[k]))

        print >> o, '\n[featuremap]'
        for f in self.backend.features.all(commented=False, category='featuremap'):
            print >> o, "%s = %s" % (f['var_name'], f['var_val'])

        return o.getvalue()

    def queueskills_conf(self):
        """Generate queueskills.conf asterisk configuration file
        """
        o = StringIO()

        userid = None
        for sk in self.backend.userqueueskills.all():
            if userid != sk['id']:
                print >> o, "\n[user-%d]" % sk['id']
                userid = sk['id']

            print >> o, "%s = %s" % (sk['name'], sk['weight'])

        agentid = None
        for sk in self.backend.agentqueueskills.all():
            if agentid != sk['id']:
                print >> o, "\n[agent-%d]" % sk['id']
                agentid = sk['id']

            print >> o, "%s = %s" % (sk['name'], sk['weight'])

        return o.getvalue()

    def queueskillrules_conf(self):
        """Generate queueskillrules.conf asterisk configuration file
        """
        o = StringIO()

        for r in self.backend.queueskillrules.all():
            print >> o, "\n[%s]" % r['name']

            if 'rule' in r and r['rule'] is not None:
                for rule in r['rule'].split(';'):
                    print >> o, "rule = %s" % rule

        return o.getvalue()

    def extensions_conf(self):
        """Generate extensions.conf asterisk configuration file
        """
        o = StringIO()
        conf = None

        # load context templates
        if hasattr(self, 'contextsconf'):
            conf = OrderedConf.OrderedRawConf(filename=self.contextsconf)
            if conf.has_conflicting_section_names():
                raise ValueError, self.contextsconf + " has conflicting section names"
            if not conf.has_section('template'):
                raise ValueError, "Template section doesn't exist"

        # hints & features (init)
        xfeatures = {
            'bsfilter':            {},
            'callgroup':           {},
            'callmeetme':          {},
            'callqueue':           {},
            'calluser':            {},
            'fwdbusy':             {},
            'fwdrna':              {},
            'fwdunc':              {},
            'phoneprogfunckey':    {},
            'vmusermsg':           {}}

        extenumbers = self.backend.extenumbers.all(features=xfeatures.keys())
        xfeatures.update(dict([x['typeval'], {'exten': x['exten'], 'commented': x['commented']}] for x in extenumbers))

        # voicemenus
        for vm_context in self.backend.voicemenus.all(commented=0, order='name'):
            print >> o, "[voicemenu-%s]" % vm_context['name']

            for act in self.backend.extensions.all(context='voicemenu-' + vm_context['name'], commented=0):
                print >> o, "exten = %s,%s,%s(%s)" % \
                        (act['exten'], act['priority'], act['app'], act['appdata'].replace('|', ','))

        # foreach active context
        for ctx in self.backend.contexts.all(commented=False, order='name', asc=False):
            # context name preceded with '!' is ignored
            if conf.has_section('!' + ctx['name']):
                continue

            print >> o, "\n[%s]" % ctx['name']
            # context includes
            for row in self.backend.contextincludes.all(context=ctx['name'], order='priority'):
                print >> o, "include = %s" % row['include']

            if conf.has_section(ctx['name']):
                section = ctx['name']
            elif conf.has_section('type:%s' % ctx['contexttype']):
                section = 'type:%s' % ctx['contexttype']
            else:
                section = 'template'

            tmpl = []
            for option in conf.iter_options(section):
                if option.get_name() == 'objtpl':
                    tmpl.append(option.get_value()); continue

                print >> o, "%s = %s" % (option.get_name(), option.get_value().replace('%%CONTEXT%%', ctx['name']))
            print >> o

            # test if we are in DUNDi active/active mode
            dundi_aa = self.backend.general.get(id=1)['dundi'] == 1

            # objects extensions (user, group, ...)
            for exten in self.backend.extensions.all(context=ctx['name'], commented=False, order='context'):
                app = exten['app']
                appdata = list(exten['appdata'].replace('|', ',').split(','))

                # active/active mode
                if dundi_aa and appdata[0] == 'user':
                    exten['priority'] += 1

                if app == 'Macro':
                    app = 'Gosub'
                    appdata = (appdata[0], 's', '1(' + ','.join(appdata[1:]) + ')')

                exten['action'] = "%s(%s)" % (app, ','.join(appdata))
                print >> o, self.gen_dialplan_from_template(tmpl, exten)

            # phone (user) hints
            hints = self.backend.hints.all(context=ctx['name'])
            if len(hints) > 0:
                print >> o, "; phones hints"

            for hint in hints:
                xid = hint['id']
                number = hint['number']
                name = hint['name']
                proto = hint['protocol'].upper()
                if proto == 'IAX':
                    proto = 'IAX2'

                if number:
                    print >> o, "exten = %s,hint,%s/%s" % (number, proto, name)

                if not xfeatures['calluser'].get('commented', 1):
                    #TODO: fkey_extension need to be reviewed (see hexanol)
                    print >> o, "exten = %s,hint,%s/%s" % (xivo_helpers.fkey_extension(
                        xfeatures['calluser']['exten'], (xid,)),
                        proto, name)

                if not xfeatures['vmusermsg'].get('commented', 1) and int(hint['enablevoicemail']) \
                     and hint['uniqueid']:
                    print >> o, "exten = %s%s,hint,%s/%s" % (xfeatures['vmusermsg']['exten'], number, proto, name)


            # objects(user,group,...) supervision
            phonesfk = self.backend.phonefunckeys.all(context=ctx['name'])
            if len(phonesfk) > 0:
                print >> o, "\n; phones supervision"

            xset = set()
            for pkey in phonesfk:
                xtype = pkey['typeextenumbersright']
                calltype = "call%s" % xtype

                if pkey['exten'] is not None:
                    exten = xivo_helpers.clean_extension(pkey['exten'])
                elif xfeatures.has_key(calltype) and not xfeatures[calltype].get('commented', 1):
                    exten = xivo_helpers.fkey_extension(
                        xfeatures[calltype]['exten'],
                        (pkey['typevalextenumbersright'],))
                else:
                    continue

                xset.add((exten, ("MeetMe:%s" if xtype == 'meetme' else "Custom:%s") % exten))

            for hint in xset:
                print >> o, "exten = %s,hint,%s" % hint


            # BS filters supervision 
            bsfilters = self.backend.bsfilterhints.all(context=ctx['name'])

            extens = set(xivo_helpers.speed_dial_key_extension(xfeatures['bsfilter'].get('exten'),
                r['exten'], None, r['number'], True) for r in bsfilters)

            if len(extens) > 0:
                print >> o, "\n; BS filters supervision"
            for exten in extens:
                print >> o, "exten = %s,hint,Custom:%s" % (exten, exten)


            # prog funckeys supervision
            progfunckeys = self.backend.progfunckeys.all(context=ctx['name'])

            extens = set()
            for k in progfunckeys:
                exten = k['exten']

                if exten is None and k['typevalextenumbersright'] is not None:
                    exten = "*%s" % k['typevalextenumbersright']

                extens.add(xivo_helpers.fkey_extension(xfeatures['phoneprogfunckey'].get('exten'),
                    (k['iduserfeatures'], k['leftexten'], exten)))

            if len(extens) > 0:
                print >> o, "\n; prog funckeys supervision"
            for exten in extens:
                print >> o, "exten = %s,hint,Custom:%s" % (exten, exten)
        print >> o, self._extensions_features(conf, xfeatures)
        return o.getvalue()

            # -- end per-context --
    def _extensions_features(self, conf, xfeatures):
        o = StringIO()
        # XiVO features
        context = 'xivo-features'
        cfeatures = []
        tmpl = []

        print >> o, "\n[%s]" % context
        for option in conf.iter_options(context):
            if option.get_name() == 'objtpl':
                tmpl.append(option.get_value()); continue

            print >> o, "%s = %s" % (option.get_name(), option.get_value().replace('%%CONTEXT%%', context))
            print >> o

        for exten in self.backend.extensions.all(context='xivo-features', commented=False):
            app = exten['app']
            appdata = list(exten['appdata'].replace('|', ',').split(','))
            exten['action'] = "%s(%s)" % (app, ','.join(appdata))
            print >> o, self.gen_dialplan_from_template(tmpl, exten)

        for x in ('busy', 'rna', 'unc'):
            fwdtype = "fwd%s" % x
            if not xfeatures[fwdtype].get('commented', 1):
                exten = xivo_helpers.clean_extension(xfeatures[fwdtype]['exten'])
                cfeatures.extend([
                    "%s,1,Set(XIVO_BASE_CONTEXT=${CONTEXT})" % exten,
                    "%s,n,Set(XIVO_BASE_EXTEN=${EXTEN})" % exten,
                    "%s,n,Gosub(feature_forward,s,1(%s))\n" % (exten, x),
                ])

        if cfeatures:
            print >> o, "exten = " + "\nexten = ".join(cfeatures)

        return o.getvalue()

    def queuerules_conf(self):
        o = StringIO()

        rule = None
        for m in self.backend.queuepenalties.all():
            if m['name'] != rule:
                rule = m['name']; print >> o, "\n[%s]" % rule

            print >> o, "penaltychange => %d," % m['seconds'],
            if m['maxp_sign'] is not None and m['maxp_value'] is not None:
                sign = '' if m['maxp_sign'] == '=' else m['maxp_sign']
                print >> o, "%w%d" % (sign, m['maxp_value']),

            if m['minp_sign'] is not None and m['minp_value'] is not None:
                sign = '' if m['minp_sign'] == '=' else m['minp_sign']
                print >> o, ",%s%d" % (sign, m['minp_value']),

            print >> o

        return o.getvalue()

    def dundi_conf(self):
        o = StringIO()

        print >> o, "[general]"
        general = self.backend.dundi.get(id=1)
        for k, v in general.iteritems():
            if v is None or k == 'id':
                continue

            if isinstance(v, unicode):
                v = v.encode('utf8')
            print >> o, k, "=", v

        trunks = dict([(t['id'], t) for t in self.backend.trunks.all()])

        print >> o, "\n[mappings]"
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

            print >> o, _m

        # peers
        for p in self.backend.dundipeer.all(commented=False):
            print >> o, "\n[%s]" % p['macaddr']

            for k, v in p.iteritems():
                if k in ('id', 'macaddr', 'description', 'commented') or v is None:
                    continue

                print >> o, "%s = %s" % (k, v)

        return o.getvalue()

    def chan_dahdi_conf(self):
        o = StringIO()

        print >> o, "[channels]"
        for k, v in self.backend.dahdi.get(id=1).iteritems():
            if v is None or k == 'id':
                continue

            if isinstance(v, unicode):
                v = v.encode('utf8')
            print >> o, k, "=", v

        print >> o
        for group in self.backend.dahdigroup.all(commented=False):
            print >> o, "\ngroup=%d" % group['groupno']

            for k in ('context', 'switchtype', 'signalling', 'callerid', 'mailbox'):
                if group[k] is not None:
                    print >> o, k, "=", group[k]

            print >> o, "channel => %s" % group['channels']

        return o.getvalue()

    def gen_dialplan_from_template(self, template, exten):
        o = StringIO()
        for line in template:
            prefix = 'exten =' if line.startswith('%%EXTEN%%') else 'same  =    '
            def varset(matchObject):
                return str(exten.get(matchObject.group(1).lower(), ''))
            line = re.sub('%%([^%]+)%%', varset, line)
            print >> o, prefix, line
        return o.getvalue()