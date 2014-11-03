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
import sys

from rebasehelper.logger import logger
from rebasehelper.utils import get_message
from rebasehelper.utils import ProcessHelper

diff_tools = {}


def register_diff_tool(diff_tool):
    diff_tools[diff_tool.CMD] = diff_tool
    return diff_tool


class DiffBase(object):
    """ Class used for testing and other future stuff, ...
        Each method should overwrite method like run_check
    """
    @classmethod
    def match(cls, cmd):
        """
        Checks if diff name matches
        """
        raise NotImplementedError()

    @classmethod
    def run_diff(self, old, new):
        """
            Method for showing difference between two files
        """
        return NotImplementedError()

    @classmethod
    def run_mergetool(self, **kwargs):
        """
            Start a tool for resolving merge conflicts
        """
        return NotImplementedError()


#@register_diff_tool
class VimDiffTool(DiffBase):
    """
    The class is used for diff between two directories or sources
    """
    CMD = 'vimdiff'


    @classmethod
    def match(cls, diff=None):
        if diff == cls.CMD:
            return True
        else:
            return False

    @classmethod
    def run_diff(cls, **kwargs):
        raise NotImplementedError()

    @classmethod
    def run_mergetool(cls, **kwargs):
        raise NotImplementedError()


@register_diff_tool
class MeldDiffTool(DiffBase):
    """
    The class is used for diff between two directory sources
    """
    CMD = 'meld'
    @classmethod
    def match(cls, diff=None):
        if diff == cls.CMD:
            return True
        else:
            return False

    @classmethod
    def run_diff(cls, old, new):
        if not old:
            raise TypeError("MeldDiffTool:run_diff: missing old")
        if not new:
            raise TypeError("MeldDiffTool:run_diff: missing new")

        logger.debug("MeldDiffTool: running diff")

        cmd = [cls.CMD, '--diff', old, new]
        return ProcessHelper.run_subprocess(cmd, output=ProcessHelper.DEV_NULL)

    @classmethod
    def run_mergetool(cls, old_dir, new_dir, suffix, failed_files):
        suffix = "." + suffix

        logger.debug("MeldDiffTool: running merge")

        for index, fname in enumerate(failed_files):
            base = os.path.join(old_dir, fname + suffix)
            remote = os.path.join(old_dir, fname)
            local = os.path.join(new_dir, fname + suffix)
            merged = os.path.join(new_dir, fname)

            # http://stackoverflow.com/questions/11133290/git-merging-using-meld
            cmd = [cls.CMD, '--diff', base, local, '--diff', base, remote, '--auto-merge', local, base, remote, '--output', merged]

            ProcessHelper.run_subprocess(cmd, output=ProcessHelper.DEV_NULL)

            if len(failed_files) > 1 and index < len(failed_files) - 1:
                accept = ['y', 'yes']
                var = get_message(message="Do you want to merge another file? (y/n)")
                if var not in accept:
                    sys.exit(0)


class Differ(object):
    """
    Class represents a processes for differences between sources
    """

    def __init__(self, tool=None):
        if tool is None:
            raise TypeError("Expected argument 'tool' is missing.")
        self._tool_name = tool
        self._tool = None

        for diff_tool in diff_tools.values():
            if diff_tool.match(self._tool_name):
                self._tool = diff_tool

        if self._tool is None:
            raise NotImplementedError("Unsupported diff tool")

    def __str__(self):
        return "<Differ tool_name='{_tool_name}' tool='{_tool}'>".format(**vars(self))

    def diff(self, old, new):
        """
        Diff between two files
        """
        logger.debug("Diff: Diff between files {0} and {1}".format(old, new))
        return self._tool.run_diff(old, new)

    def merge(self, old_dir, new_dir, suffix, failed_files):
        """
        Tool for resolving merge conflicts
        """
        self._tool.run_mergetool(old_dir, new_dir, suffix, failed_files)
