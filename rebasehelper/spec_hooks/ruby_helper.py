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
import re

import rpm

from six.moves import urllib

from rebasehelper.specfile import BaseSpecHook
from rebasehelper.utils import TemporaryEnvironment, ProcessHelper
from rebasehelper.logger import logger


class RubyHelperHook(BaseSpecHook):

    NAME = 'Ruby Helper'
    CATEGORIES = ['ruby']

    @classmethod
    def get_name(cls):
        return cls.NAME

    @classmethod
    def get_categories(cls):
        return cls.CATEGORIES

    @classmethod
    def _get_instructions(cls, comments, old_version, new_version):
        """Extract instructions from comments, update version if necessary"""
        instructions = []
        for comment in comments:
            comment = rpm.expandMacro(rpm.expandMacro(comment))
            comment = re.sub(r'^#\s*', '', comment)
            comment = comment.replace(old_version, new_version)
            instructions.append(comment)
        return instructions

    @classmethod
    def _build_source_from_instructions(cls, instructions, source, logfile):
        """Run instructions to create source archive"""
        logger.info("Attempting to create source '%s' using instructions in comments", source)
        with TemporaryEnvironment() as tmp:
            script = os.path.join(tmp.path(), 'script.sh')
            with open(script, 'w') as f:
                f.write('#!/bin/sh -x\n')
                f.write(''.join(instructions))
                f.write('cp "{}" "{}"\n'.format(source, os.getcwd()))
            os.chmod(script, 0o755)
            result = ProcessHelper.run_subprocess_cwd(script, tmp.path(), output=logfile, shell=True)
        if result == 0 and os.path.isfile(source):
            logger.info('Source creation succeeded.')
        else:
            logger.info('Source creation failed.')

    @classmethod
    def run(cls, spec_file, rebase_spec_file, **kwargs):
        # find non-existent local sources
        sources = [idx for idx, src in enumerate(rebase_spec_file.sources)
                   if not urllib.parse.urlparse(src).scheme and not os.path.isfile(src)]
        for idx in sources:
            if spec_file.sources[idx] == rebase_spec_file.sources[idx]:
                # skip sources that stayed unchanged
                continue
            source = rebase_spec_file.sources[idx]
            logger.info("Found non-existent source '%s'", source)
            source_re = re.compile(r'^Source0?:' if idx == 0 else r'^Source{}:'.format(idx))
            comment_re = re.compile(r'^#')
            comments = None
            # find matching Source line in the SPEC file
            for i in range(len(rebase_spec_file.spec_content)):
                if source_re.match(rebase_spec_file.spec_content[i]):
                    # get all comments above this line
                    for j in range(i - 1, 0, -1):
                        if not comment_re.match(rebase_spec_file.spec_content[j]):
                            comments = rebase_spec_file.spec_content[j+1:i]
                            break
                    break
            # update data so that RPM macros are populated correctly
            rebase_spec_file._update_data()
            instructions = cls._get_instructions(comments,
                                                 spec_file.get_version(),
                                                 rebase_spec_file.get_version())
            logfile = os.path.join(kwargs['workspace_dir'], '{}.log'.format(source))
            cls._build_source_from_instructions(instructions, source, logfile)
