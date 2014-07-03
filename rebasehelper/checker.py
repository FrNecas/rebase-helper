# -*- coding: utf-8 -*-

# This tool helps you to rebase package to the latest version
# Copyright (C) 2013 Petr Hracek
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


import os
from rebasehelper.utils import ProcessHelper
from rebasehelper.utils import write_to_file
from rebasehelper.logger import logger

check_tools = {}


def register_check_tool(check_tool):
    check_tools[check_tool.CMD] = check_tool
    return check_tool


class BaseChecker(object):
    """ Base class used for testing tool run on final pkgs. """

    @classmethod
    def match(cls, *args, **kwargs):
        """
        Checks if the tool name match the class implementation. If yes, returns
        True, otherwise returns False.
        """
        raise NotImplementedError()

    @classmethod
    def run_check(cls, *args, **kwargs):
        """
        Perform the check itself and return results.
        """
        raise NotImplementedError()


@register_check_tool
class PkgDiffTool(BaseChecker):
    """ Pkgdiff compare tool. """
    CMD = "pkgdiff"
    pkgdiff_results_filename = 'pkgdiff_reports.html'
    pkgdiff_results_path = pkgdiff_results_filename
    results_dir = ''
    workspace_dir = ''

    @classmethod
    def match(cls, cmd=None):
        if cmd == cls.CMD:
            return True
        else:
            return False

    @classmethod
    def _create_xml(cls, name, input_structure={}):
        file_name = os.path.join(cls.workspace_dir, name + ".xml")
        tags = {'version': input_structure.get('version', ""),
                'group': input_structure.get('name', ''),
                'packages': input_structure.get('rpm', [])}
        lines = []
        for key, value in tags.items():
            new_value = value if isinstance(value, str) else '\n'.join(value)
            lines.append('<{0}>\n{1}\n</{0}>\n'.format(key, new_value))
        write_to_file(file_name, "w", lines)
        return file_name

    @classmethod
    def run_check(cls, **kwargs):
        """ Compares  old and new RPMs using pkgdiff """
        cls.results_dir = kwargs.get('results_dir', '')
        cls.workspace_dir = os.path.join(kwargs.get('workspace_dir', ''), cls.CMD)
        cls.pkgdiff_results_path = os.path.join(cls.results_dir, cls.pkgdiff_results_filename)
        # create the workspace directory
        os.makedirs(cls.workspace_dir)

        versions = ['old', 'new']
        cmd = [cls.CMD]
        for version in versions:
            old = kwargs.get(version, None)
            if old:
                file_name = cls._create_xml(version, input_structure=old)
                cmd.append(file_name)
        cmd.append('-report-path')
        cmd.append(cls.pkgdiff_results_path)
        # TODO Should we return a value??
        ProcessHelper.run_subprocess(cmd, output=ProcessHelper.DEV_NULL)
        return cls.pkgdiff_results_path


class Checker(object):
    """
    Class representing a process of checking final packages.
    """

    def __init__(self, tool=None):
        if tool is None:
            raise TypeError("Expected argument 'tool' (pos 1) is missing")
        self._tool_name = tool
        self._tool = None

        for check_tool in check_tools.values():
            if check_tool.match(self._tool_name):
                self._tool = check_tool

        if self._tool is None:
            raise NotImplementedError("Unsupported checking tool")

    def __str__(self):
        return "<Checker tool_name='{_tool_name}' tool={_tool}>".format(**vars(self))

    def run_check(self, **kwargs):
        """ Run the check """
        logger.debug("Checker: Running tests on packages using '%s'" % self._tool_name)
        return self._tool.run_check(**kwargs)

    @classmethod
    def get_supported_tools(cls):
        """ Return list of supported tools """
        return check_tools.keys()