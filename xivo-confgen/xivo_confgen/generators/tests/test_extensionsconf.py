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
from xivo_confgen.generators.extensionsconf import ExtensionsConf
from StringIO import StringIO
from mock import Mock


class TestExtensionsConf(unittest.TestCase):

    def assertConfigEqual(self, configExpected, configResult):
        self.assertEqual(configExpected.replace(' ', ''), configResult.replace(' ', ''))

    def setUp(self):
        self.extensionsconf = ExtensionsConf(None, 'context.conf')

    def tearDown(self):
        pass

    def test_generate_dialplan_from_template(self):
        output = StringIO()
        template = ["%%EXTEN%%,%%PRIORITY%%,Set('XIVO_BASE_CONTEXT': ${CONTEXT})"]
        exten = {'exten':'*98', 'priority':1}
        self.extensionsconf.gen_dialplan_from_template(template, exten, output)

        self.assertEqual(output.getvalue(), "exten = *98,1,Set('XIVO_BASE_CONTEXT': ${CONTEXT})\n\n")

    def test_generate_voice_menus(self):
        output = StringIO()
        voicemenus = [{'name': u'menu1',
                       },
                      {'name': u'menu2',
                       }
                      ]

        self.extensionsconf.backend = Mock()
        self.extensionsconf.backend.extensions.all.return_value = \
            [{'exten':u'2300','app':u'GoSub','priority':1,'appdata':u'    endcall,s,1(hangup)'}]
        self.extensionsconf.generate_voice_menus(voicemenus, output)

        self.assertConfigEqual("""\
                                        [voicemenu-menu1]
                                        exten=2300,1,GoSub(endcall,s,1(hangup))
                                        
                                        [voicemenu-menu2]
                                        exten=2300,1,GoSub(endcall,s,1(hangup))
                                        
                                        """, output.getvalue())

    def test_bsfilter_build_extens(self):
        bs1 = {'bsfilter': 'boss',
               'exten': 1001,
               'number': 1000}
        query_result = [bs1]

        result = self.extensionsconf._build_sorted_bsfilter(query_result)

        expected = set([(1000, 1001)])

        self.assertEqual(result, expected)

    def test_bsfilter_build_extend_no_double(self):
        bs1 = {'bsfilter': 'boss',
               'exten': 1001,
               'number': 1000}
        bs2 = {'bsfilter': 'secretary',
               'exten': 1000,
               'number': 1001}
        query_result = [bs1, bs2]

        result = self.extensionsconf._build_sorted_bsfilter(query_result)

        expected = set([(1000, 1001)])

        self.assertEqual(result, expected)

    def test_bsfilter_build_extend_no_two_secretaries(self):
        bs1 = {'bsfilter': 'boss',
               'exten': 1001,
               'number': 1000}
        bs2 = {'bsfilter': 'secretary',
               'exten': 1000,
               'number': 1001}
        bs3 = {'bsfilter': 'boss',
               'exten': 1002,
               'number': 1000}
        bs4 = {'bsfilter': 'secretary',
               'exten': 1000,
               'number': 1002}
        query_result = [bs1, bs2, bs3, bs4]

        result = self.extensionsconf._build_sorted_bsfilter(query_result)

        expected = set([(1000, 1001), (1000, 1002)])

        self.assertEqual(result, expected)
