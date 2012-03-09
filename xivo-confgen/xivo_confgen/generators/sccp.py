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

from xivo_confgen.generators.util import format_ast_section, \
    format_ast_option


class SccpConf(object):
    def __init__(self, sccpgeneral, sccpline, sccpdevice):
        self._sccpgeneral = sccpgeneral
        self._sccpline = sccpline
        self._sccpdevice = sccpdevice

    def generate(self, output):
        sccp_general_conf = _SccpGeneralConf();
        sccp_general_conf.generate(self._sccpgeneral, output)

        sccp_line_conf = _SccpLineConf();
        sccp_line_conf.generate(self._sccpline, output)

        sccp_device_conf = _SccpDeviceConf();
        sccp_device_conf.generate(self._sccpdevice, output)

    @classmethod
    def new_from_backend(cls, backend):
        sccpgeneral = backend.sccpgeneral.all()
        sccpline = backend.sccpline.all()
        sccpdevice = backend.sccpdevice.all()
        return cls(sccpgeneral, sccpline, sccpdevice)


class _SccpGeneralConf(object):
    def generate(self, sccpgeneral, output):
        print >> output, u'[general]'
        for item in sccpgeneral:
            print >> output, format_ast_option(item['option_name'], item['value'])
        print >> output


class _SccpLineConf(object):
    def generate(self, sccpline, output):
        print >> output, u'[line]'
        for item in sccpline:
            print >> output, format_ast_section(item['name'])
            print >> output, format_ast_option('cid_name', item['cid_name'])
            print >> output, format_ast_option('cid_num', item['cid_num'])
            print >> output


class _SccpDeviceConf(object):
    def generate(self, sccpdevice, output):
        print >> output, u'[device]'
        for item in sccpdevice:
            print >> output, format_ast_section(item['name'])
            print >> output, format_ast_option('device', item['device'])
            print >> output, format_ast_option('line', item['line'])
            print >> output
