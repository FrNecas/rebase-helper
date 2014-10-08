# -*- coding: utf-8 -*-
#
# This tool helps you to rebase package to the latest version
# Copyright (C) 2013-2014 Red Hat, Inc.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# he Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
# Authors: Petr Hracek <phracek@redhat.com>
#          Tomas Hozza <thozza@redhat.com>

import six
from .base_test import BaseTest
from rebasehelper.checker import PkgDiffTool


class TestPkgDiff(BaseTest):

    FILE_XML = "files.xml"
    TEST_FILES = [
        FILE_XML,
    ]

    def test_pkgdiff_dictionary(self):
        expected_dict = {'added': ['/usr/sbin/test',
                                   '/usr/lib64/libtest.so',
                                   '/usr/lib64/libtest.so.1'],
                         'removed': ['/usr/sbin/my_test',
                                     '/usr/lib64/libtest2.so',
                                     '/usr/lib64/libtest2.so.1'],
                         'changed': ['/usr/share/test.man'],
                         'moved': ['/usr/local/test.sh'],
                         'renamed': ['/usr/lib/libtest3.so.3',
                                     '/usr/lib/libtest3.so']}
        pkgdiff_tool = PkgDiffTool()
        pkgdiff_tool.results_dir = self.TESTS_DIR
        res_dict = pkgdiff_tool.process_xml_results()
        assert res_dict == expected_dict
