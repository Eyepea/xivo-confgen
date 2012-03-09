#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
    name='xivo-confgen',
    version='0.1',
    description='XIVO Configurations Generator',
    author='Avencall',
    author_email='xivo-dev@lists.proformatique.com',
    url='http://wiki.xivo.fr/',
    license='GPLv3',
    packages=['xivo_confgen',
              'xivo_confgen.generators',
              'xivo_confgen.backends'],
    scripts=['bin/xivo-confgen', 'bin/xivo-confgend'],
    data_files=[('/etc/pf-xivo', ['etc/xivo-confgen.conf', 'etc/xivo-confgend.conf']),
                ('/etc/pf-xivo/xivo-confgend/asterisk', ['etc/asterisk/contexts.conf'])],
)
