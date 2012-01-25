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

import re
from StringIO import StringIO
from xivo import OrderedConf, xivo_helpers


class ExtensionsConf(object):

    def __init__(self, backend, contextsconf):
        self.backend = backend
        self.contextsconf = contextsconf


    def generate(self, output):
        self.extensions_conf(output)

    def extensions_conf(self, output):
            """Generate extensions.conf asterisk configuration file
            """
            self.generate_voice_menus(self.backend.voicemenus.all(commented=0, order='name'), output)

            options = output
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


            # foreach active context
            for ctx in self.backend.contexts.all(commented=False, order='name', asc=False):
                # context name preceded with '!' is ignored
                if conf.has_section('!' + ctx['name']):
                    continue

                print >> options, "\n[%s]" % ctx['name']
                # context includes
                for row in self.backend.contextincludes.all(context=ctx['name'], order='priority'):
                    print >> options, "include = %s" % row['include']

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

                    print >> options, "%s = %s" % (option.get_name(), option.get_value().replace('%%CONTEXT%%', ctx['name']))
                print >> options

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
                    self.gen_dialplan_from_template(tmpl, exten, options)

                # phone (user) hints
                hints = self.backend.hints.all(context=ctx['name'])
                if len(hints) > 0:
                    print >> options, "; phones hints"

                for hint in hints:
                    xid = hint['id']
                    number = hint['number']
                    name = hint['name']
                    proto = hint['protocol'].upper()
                    if proto == 'IAX':
                        proto = 'IAX2'

                    interface = "%s/%s" % (proto, name)
                    if proto == 'CUSTOM':
                        interface = name

                    if number:
                        print >> options, "exten = %s,hint,%s" % (number, interface)

                    if not xfeatures['calluser'].get('commented', 1):
                        #TODO: fkey_extension need to be reviewed (see hexanol)
                        print >> options, "exten = %s,hint,%s" % (xivo_helpers.fkey_extension(
                            xfeatures['calluser']['exten'], (xid,)),
                            interface)

                    if not xfeatures['vmusermsg'].get('commented', 1) and int(hint['enablevoicemail']) \
                         and hint['uniqueid']:
                        if proto == 'CUSTOM':
                            print >> options, "exten = %s%s,hint,%s" % (xfeatures['vmusermsg']['exten'], number, interface)

                # objects(user,group,...) supervision
                phonesfk = self.backend.phonefunckeys.all(context=ctx['name'])
                if len(phonesfk) > 0:
                    print >> options, "\n; phones supervision"

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
                    print >> options, "exten = %s,hint,%s" % hint


                # BS filters supervision 
                bsfilters = self.backend.bsfilterhints.all(context=ctx['name'])

                extens = set(xivo_helpers.speed_dial_key_extension(xfeatures['bsfilter'].get('exten'),
                    r['exten'], None, r['number'], True) for r in bsfilters)

                if len(extens) > 0:
                    print >> options, "\n; BS filters supervision"
                for exten in extens:
                    print >> options, "exten = %s,hint,Custom:%s" % (exten, exten)


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
                    print >> options, "\n; prog funckeys supervision"
                for exten in extens:
                    print >> options, "exten = %s,hint,Custom:%s" % (exten, exten)
            print >> options, self._extensions_features(conf, xfeatures)
            return options.getvalue()

                # -- end per-context --
    def _extensions_features(self, conf, xfeatures):
        options = StringIO()
        # XiVO features
        context = 'xivo-features'
        cfeatures = []
        tmpl = []

        print >> options, "\n[%s]" % context
        for option in conf.iter_options(context):
            if option.get_name() == 'objtpl':
                tmpl.append(option.get_value()); continue

            print >> options, "%s = %s" % (option.get_name(), option.get_value().replace('%%CONTEXT%%', context))
            print >> options

        for exten in self.backend.extensions.all(context='xivo-features', commented=False):
            app = exten['app']
            appdata = list(exten['appdata'].replace('|', ',').split(','))
            exten['action'] = "%s(%s)" % (app, ','.join(appdata))
            self.gen_dialplan_from_template(tmpl, exten, options)

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
            print >> options, "exten = " + "\nexten = ".join(cfeatures)

        return options.getvalue()


    def gen_dialplan_from_template(self, template, exten, output):
        for line in template:
            prefix = 'exten =' if line.startswith('%%EXTEN%%') else 'same  =    '
            def varset(matchObject):
                return str(exten.get(matchObject.group(1).lower(), ''))
            line = re.sub('%%([^%]+)%%', varset, line)
            print >> output, prefix, line
        print >> output

    def generate_voice_menus(self, voicemenus, output):
        for vm_context in voicemenus:
            print >> output, "[voicemenu-%s]" % vm_context['name']
            for act in self.backend.extensions.all(context='voicemenu-' + vm_context['name'], commented=0):
                print >> output, "exten = %s,%s,%s(%s)" % \
                            (act['exten'], act['priority'], act['app'], act['appdata'].replace('|', ','))
            print >> output


    @classmethod
    def new_from_backend(cls, backend, contextconfs):
        return cls(backend, contextconfs)



