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

import os

import pytest

from rebasehelper.archive import Archive


class TestArchive(object):
    TAR_GZ = 'archive.tar.gz'
    TGZ = 'archive.tgz'
    TAR_XZ = 'archive.tar.xz'
    TAR_BZ2 = 'archive.tar.bz2'
    ZIP = 'archive.zip'
    BZ2 = 'file.txt.bz2'

    ARCHIVED_FILE = 'file.txt'
    ARCHIVED_FILE_CONTENT = 'simple testing file'

    #  These files located in TEST_FILES_DIR will be copied into the testing environment
    TEST_FILES = [
        TAR_GZ,
        TGZ,
        TAR_XZ,
        TAR_BZ2,
        BZ2,
        ZIP
    ]

    @pytest.fixture
    def extracted_archive(self, archive, workdir):
        a = Archive(archive)
        d = os.path.join(workdir, 'dir')
        a.extract_archive(d)
        return d

    @pytest.mark.parametrize('archive', [
        TAR_GZ,
        TGZ,
        TAR_XZ,
        TAR_BZ2,
        BZ2,
        ZIP,
    ], ids=[
        'tar.gz',
        'tgz',
        'tar.xz',
        'tar.bz2',
        'bz2',
        'zip',
    ])
    def test_archive(self, extracted_archive):
        extracted_file = os.path.join(extracted_archive, self.ARCHIVED_FILE)
        #  check if the dir was created
        assert os.path.isdir(extracted_archive)
        #  check if the file was extracted
        assert os.path.isfile(extracted_file)
        #  check the content
        with open(extracted_file) as f:
            assert f.read().strip() == self.ARCHIVED_FILE_CONTENT
