# -*- coding: utf8 -*-

__license__ = """
    Copyright (C) 2010-2012  Avencall

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

import os.path


class Cache(object):
    def get(self, key):
        raise NotImplementedError()

    def put(self, key, value):
        raise NotImplementedError()


class FileCache(Cache):
    def __init__(self, basedir):
        super(FileCache, self).__init__()
        self.basedir = basedir

    def get(self, key):
        path = self._get_path_from_key(key)
        if not os.path.exists(path):
            return None
        with open(path) as f:
            content = f.read()
        return content

    def _get_path_from_key(self, key):
        return os.path.join(self.basedir, key)

    def put(self, key, value):
        path = self._get_path_from_key(key)
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
            try:
                os.makedirs(dir)
            except Exception:
                return False
        with open(path, 'w') as f:
            f.write(value)
        return True
