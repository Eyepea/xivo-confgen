import StringIO
from xivo import OrderedConf, xivo_helpers


class ExtensionsConf(object):

    def extensions_conf(self):
            """Generate extensions.conf asterisk configuration file
            """
            options = StringIO()
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
                print >> options, "[voicemenu-%s]" % vm_context['name']
    
                for act in self.backend.extensions.all(context='voicemenu-' + vm_context['name'], commented=0):
                    print >> options, "exten = %s,%s,%s(%s)" % \
                            (act['exten'], act['priority'], act['app'], act['appdata'].replace('|', ','))
    
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
                    print >> options, self.gen_dialplan_from_template(tmpl, exten)
    
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
    
                    if number:
                        print >> options, "exten = %s,hint,%s/%s" % (number, proto, name)
    
                    if not xfeatures['calluser'].get('commented', 1):
                        #TODO: fkey_extension need to be reviewed (see hexanol)
                        print >> options, "exten = %s,hint,%s/%s" % (xivo_helpers.fkey_extension(
                            xfeatures['calluser']['exten'], (xid,)),
                            proto, name)
    
                    if not xfeatures['vmusermsg'].get('commented', 1) and int(hint['enablevoicemail']) \
                         and hint['uniqueid']:
                        print >> options, "exten = %s%s,hint,%s/%s" % (xfeatures['vmusermsg']['exten'], number, proto, name)
    
    
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
            print >> options, self.gen_dialplan_from_template(tmpl, exten)

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
