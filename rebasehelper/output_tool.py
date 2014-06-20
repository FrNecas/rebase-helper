# -*- coding: utf-8 -*-

import sys
import os

from rebasehelper.base_output_tool import BaseOutputTool
from rebasehelper.logger import logger
from rebasehelper import settings

output_tools = {}


def register_build_tool(output_tool):
    output_tools[output_tool.PRINT] = output_tool
    return output_tool


def check_output_argument(output_tool):
    """
    Function checks whether pkgdifftool argument is allowed
    """
    if output_tool not in output_tools.keys():
        logger.error('You have to specify one of these printint output tools {0}'.format(output_tools.keys()))
        sys.exit(0)


class BaseOutputTool(object):
    """ Class used for testing and other future stuff, ...
        Each method should overwrite method like run_check
    """

    def print_summary(self, **kwargs):
        """ Return list of files which has been changed against old version
        This will be used by checkers
        """
        raise NotImplementedError()


@register_build_tool
class TextOutputTool(BaseOutputTool):
    """ Text output tool. """
    PRINT = "text"

    @classmethod
    def match(cls, cmd=None):
        if cmd == cls.PRINT:
            return True
        else:
            return False

    @classmethod
    def print_message_and_separator(cls, message="", separator='='):
        logger.info(message)
        logger.info(separator * len(message))

    @classmethod
    def print_patches(cls, patches, summary):
        logger.info("Patches:")
        if not patches:
            logger.info("Patches were neither modified nor deleted.")
            return
        for key, value in patches.items():
            patch_name = os.path.basename(value[0])
            for status, patches in summary.items():
                found = [x for x in patches if patch_name in x]
                if not found:
                    continue
                logger.info("Patch{0} {1} [{2}]".format(key, patch_name, status))
                break
    @classmethod
    def print_rpms(cls, rpms, version):
        pkgs = ['srpm', 'rpm']
        if not rpms.get('srpm', None):
            return
        message = '{0} (S)RPM packages:'.format(version)
        cls.print_message_and_separator(message=message, separator='-')
        for type_rpm in pkgs:
            srpm = rpms.get(type_rpm, None)
            if not srpm:
                continue
            logger.info("{0} package(s):".format(type_rpm.upper()))
            if isinstance(srpm, str):
                logger.info("- {0}".format(srpm))
            else:
                for pkg in srpm:
                    logger.info("- {0}".format(pkg))

    @classmethod
    def print_summary(cls, **kwargs):
        """
        Function is used for printing summary informations
        :return:
        """
        cls.print_message_and_separator(message="Summary information:")
        summary = kwargs['summary_info']
        old = kwargs.get('old')
        new = kwargs.get('new')
        cls.print_patches(old.get(settings.FULL_PATCHES, None), summary)

        cls.print_rpms(old, 'Old')
        cls.print_rpms(new, 'New')


class OutputTool(object):
    """
    Class representing a process of building binaries from sources.
    """

    def __init__(self, output_tool=None):
        if output_tool is None:
            raise TypeError("Expected argument 'tool' (pos 1) is missing")
        self._output_tool_name = output_tool
        self._tool = None

        for output in output_tools.values():
            if output.match(self._output_tool_name):
                self._tool = output

        if self._tool is None:
            raise NotImplementedError("Unsupported build tool")

    def print_information(self, **kwargs):
        """ Build sources. """
        logger.debug("OutputTool: Printing information using '{0}'".format(self._output_tool_name))
        return self._tool.print_summary(**kwargs)
