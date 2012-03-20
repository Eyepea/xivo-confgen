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

import os
import StringIO
import unittest
import mock
from xivo_confgen.generators.sccp import SccpConf, _SccpGeneralConf, _SccpLineConf, _SccpDeviceConf
from xivo_confgen.generators.tests.util import parse_ast_config


class TestSccpConf(unittest.TestCase):
    def setUp(self):
        self._output = StringIO.StringIO()

    def _parse_ast_cfg(self):
        self._output.seek(os.SEEK_SET)
        return parse_ast_config(self._output)

    def assertConfigEqual(self, configExpected, configResult):
        self.assertEqual(configExpected.replace(' ',''), configResult.replace(' ',''))

    def test_empty_sections(self):
        sccp_conf = SccpConf([], [], [])
        sccp_conf.generate(self._output)

        result = self._parse_ast_cfg()
        expected = { u'general': [], u'devices': [], u'lines': []}

        self.assertEqual(expected, result)

    def test_one_element_general_section(self):
        sccpgeneral = [{'category': u'general',
                        'option_name': u'foo',
                        'value': u'bar'}]

        sccp_conf = _SccpGeneralConf()
        sccp_conf.generate(sccpgeneral, self._output)

        expected = """\
                    [general]
                    foo=bar

                   """
        self.assertConfigEqual(expected, self._output.getvalue())

    def test_one_element_lines_section(self):
        sccpline = [{'category': u'lines',
                     'name': u'100',
                     'cid_name': u'jimmy',
                     'cid_num': u'100'}]

        sccp_conf = _SccpLineConf()
        sccp_conf.generate(sccpline, self._output)


        expected = """\
                    [lines]
                    [100]
                    cid_name=jimmy
                    cid_num=100

                   """

        self.assertConfigEqual(expected, self._output.getvalue())

    def test_one_element_device_section(self):
        sccpdevice = [{'category': u'devices',
                       'name': u'SEPACA016FDF235',
                       'device': u'SEPACA016FDF235',
                       'line': u'103',
                       'voicemail': u'103'}]

        sccp_conf = _SccpDeviceConf()
        sccp_conf.generate(sccpdevice, self._output)

        expected = """\
                    [devices]
                    [SEPACA016FDF235]
                    device=SEPACA016FDF235
                    line=103
                    voicemail=103

                   """
        self.assertConfigEqual(expected, self._output.getvalue())
   
    def test_general_section(self):
        sccp = [{'category': u'general',
                 'option_name': u'bindaddr',
                 'value': u'0.0.0.0'},
                {'category': u'general',
                 'option_name': u'dateformat',
                 'value': u'D.M.Y'},
                {'category': u'general',
                 'option_name': u'keepalive',
                 'value': u'10'},
                {'category': u'general',
                 'option_name': u'authtimeout',
                 'value': u'10'}]

        sccp_conf = SccpConf(sccp, [], [])
        sccp_conf.generate(self._output)

        result = self._parse_ast_cfg()
        expected = {u'general': [u'bindaddr = 0.0.0.0',
                                 u'dateformat = D.M.Y',
                                 u'keepalive = 10',
                                 u'authtimeout = 10'],
                    u'lines': [],
                    u'devices': []}

        self.assertEqual(expected, result)

    def test_new_from_backend(self):
        backend = mock.Mock()
        SccpConf.new_from_backend(backend)
        backend.sccpgeneral.all.assert_called_once_with()
        backend.sccpline.all.assert_called_once_with()
        backend.sccpdevice.all.assert_called_once_with()
