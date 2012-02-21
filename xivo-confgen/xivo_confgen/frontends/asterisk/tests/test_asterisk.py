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

import unittest
import sys

from xivo_confgen.frontends.asterisk.util import *
from xivo_confgen.frontends.asterisk import AsteriskFrontend


class Test(unittest.TestCase):
    def setUp(self):
        self.asteriskFrontEnd = AsteriskFrontend(None)

    def tearDown(self):
        pass

    def test_encoding(self):
        charset = ("ascii", "US-ASCII",)
        self.assertTrue(sys.getdefaultencoding() in charset, "Test should be run in ascii, in eclipse change run configuration common tab")

    def test_get_line(self):
        result = gen_value_line('emailbody', 'pépè')
        self.assertEqual(result, u'emailbody = pépè')

    def test_unicodify_string(self):
            self.assertEqual(u'pépé', unicodify_string(u'pépé'))
            self.assertEqual(u'pépé', unicodify_string(u'pépé'.encode('utf8')))
            self.assertEqual(u'pépé', unicodify_string('pépé'))
            self.assertEqual(u'8', unicodify_string(8))

    def test_get_not_none(self):
        d = {'one': u'pépè',
             'two': u'pépè'.encode('utf8'),
             'three': None}
        self.assertEqual(u'pépè', get_is_not_none(d, 'one'))
        self.assertEqual(u'pépè', get_is_not_none(d, 'two'))
        self.assertEqual(u'', get_is_not_none(d, 'three'))

    def test_gen_queues(self):
        """
        [general]
        shared_lastcall = no
        updatecdr = no
        monitor-type = no
        autofill = no
        persistentmembers = yes
        """
        pass

    def test_gen_iax_trunk(self):
        trunk = {'id': 1, 'name': u'xivo_devel_51', 'type': u'friend', 'username': u'xivo_devel_51',
                  'secret': u'xivo_devel_51', 'dbsecret': u'', 'context': u'default', 'language': u'fr_FR',
                  'accountcode': None, 'amaflags': None, 'mailbox': None, 'callerid': None, 'fullname': None,
                  'cid_number': None, 'trunk': 0, 'auth': u'plaintext,md5', 'encryption': None,
                  'forceencryption': None, 'maxauthreq': None, 'inkeys': None, 'outkey': None, 'adsi': None,
                  'transfer': None, 'codecpriority': None, 'jitterbuffer': None, 'forcejitterbuffer': None,
                  'sendani': 0, 'qualify': u'no', 'qualifysmoothing': 0, 'qualifyfreqok': 60000,
                  'qualifyfreqnotok': 10000, 'timezone': None, 'disallow': None, 'allow': None,
                  'mohinterpret': None, 'mohsuggest': None, 'deny': None, 'permit': None, 'defaultip': None,
                  'sourceaddress': None, 'setvar': u'', 'host': u'192.168.32.253', 'port': 4569, 'mask': None,
                  'regexten': None, 'peercontext': None, 'ipaddr': u'', 'regseconds': 0, 'immediate': None,
                  'parkinglot': None, 'protocol': u'iax', 'category': u'trunk', 'commented': 0,
                  'requirecalltoken': u'auto'}
        result = self.asteriskFrontEnd._gen_iax_trunk(trunk)
        self.assertTrue(u'[xivo_devel_51]' in result)
        self.assertTrue(u'regseconds =  0' in result)
        self.assertTrue(u'qualifysmoothing =  0' in result)
        self.assertTrue(u'secret =  xivo_devel_51' in result)
        self.assertTrue(u'type =  friend' in result)
        self.assertTrue(u'username =  xivo_devel_51' in result)
        self.assertTrue(u'auth =  plaintext,md5' in result)
        self.assertTrue(u'qualifyfreqnotok =  10000' in result)
        self.assertTrue(u'requirecalltoken =  auto' in result)
        self.assertTrue(u'port =  4569' in result)
        self.assertTrue(u'context =  default' in result)
        self.assertTrue(u'sendani =  0' in result)
        self.assertTrue(u'qualify =  no' in result)
        self.assertTrue(u'trunk =  0' in result)
        self.assertTrue(u'language =  fr_FR' in result)
        self.assertTrue(u'host =  192.168.32.253' in result)
        self.assertTrue(u'qualifyfreqok =  60000' in result)

    def test_gen_iax_conf_general(self):
        staticiax = [{'filename': u'iax.conf', 'category': u'general', 'var_name': u'bindport', 'var_val': u'4569'},
                    {'filename': u'iax.conf', 'category': u'general', 'var_name': u'bindaddr', 'var_val': u'0.0.0.0'},
                    {'filename': u'iax.conf', 'category': u'general', 'var_name': u'iaxcompat', 'var_val': u'no'},
                    {'filename': u'iax.conf', 'category': u'general', 'var_name': u'authdebug', 'var_val': u'yes'},
                    {'filename': u'iax.conf', 'category': u'general', 'var_name': u'srvlookup', 'var_val': None},
                    {'filename': u'iax.conf', 'category': u'general', 'var_name': u'shrinkcallerid', 'var_val': None},
                    {'filename': u'iax.conf', 'category': u'general', 'var_name': u'language', 'var_val': u'fr_FR'}]
        result = self.asteriskFrontEnd._gen_iax_general(staticiax)
        self.assertTrue(u'[general]' in result)
        self.assertTrue(u'bindport = 4569' in result)
        self.assertTrue(u'bindaddr = 0.0.0.0' in result)
        self.assertTrue(u'iaxcompat = no' in result)
        self.assertTrue(u'authdebug = yes' in result)
        self.assertTrue(u'language = fr_FR' in result)

    def test_gen_iax_conf_users(self):
        useriax = [{'id': 2, 'name': u'6rh29c', 'type': u'friend', 'username': None, 'secret': u'DC8HTI',
                    'dbsecret': u'', 'context': u'default', 'language': None, 'accountcode': None,
                    'amaflags': None, 'mailbox': None, 'callerid': u'"hq"', 'fullname': None,
                    'cid_number': None, 'trunk': 0, 'auth': u'plaintext,md5', 'encryption': None,
                    'forceencryption': None, 'maxauthreq': None, 'inkeys': None, 'outkey': None,
                    'adsi': None, 'transfer': None, 'codecpriority': None, 'jitterbuffer': None,
                    'forcejitterbuffer': None, 'sendani': 0, 'qualify': u'no', 'qualifysmoothing': 0,
                    'qualifyfreqok': 60000, 'qualifyfreqnotok': 10000, 'timezone': None, 'disallow': None,
                    'allow': None, 'mohinterpret': None, 'mohsuggest': u'default', 'deny': None,
                    'permit': None, 'defaultip': None, 'sourceaddress': None, 'setvar': u'',
                    'host': u'dynamic', 'port': None, 'mask': None, 'regexten': None, 'peercontext': None,
                    'ipaddr': u'', 'regseconds': 0, 'immediate': None, 'parkinglot': None, 'protocol': u'iax',
                    'category': u'user', 'commented': 0, 'requirecalltoken': u''}]
        result = self.asteriskFrontEnd._gen_iax_users(useriax)
        self.assertTrue(u'[6rh29c]' in result)
        self.assertTrue(u'regseconds = 0' in result)
        self.assertTrue(u'callerid = "hq"' in result)
        self.assertTrue(u'qualifysmoothing = 0' in result)
        self.assertTrue(u'secret = DC8HTI' in result)
        self.assertTrue(u'type = friend' in result)
        self.assertTrue(u'auth = plaintext,md5' in result)
        self.assertTrue(u'qualifyfreqnotok = 10000' in result)
        self.assertTrue(u'mohsuggest = default' in result)
        self.assertTrue(u'context = default' in result)
        self.assertTrue(u'sendani = 0' in result)
        self.assertTrue(u'qualify = no' in result)
        self.assertTrue(u'trunk = 0' in result)
        self.assertTrue(u'host = dynamic' in result)
        self.assertTrue(u'qualifyfreqok = 60000' in result)

