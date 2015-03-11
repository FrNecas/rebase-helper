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
import six
from rebasehelper.logger import logger
from rebasehelper.utils import ConsoleHelper
from rebasehelper.utils import GitHelper, GitRebaseError
from rebasehelper.diff_helper import GenericDiff
from rebasehelper.exceptions import RebaseHelperError

#from git import Repo
#import git

patch_tools = {}


def register_patch_tool(patch_tool):
    patch_tools[patch_tool.CMD] = patch_tool
    return patch_tool


class PatchBase(object):
    """ Class used for using several patching command tools, ...
        Each method should overwrite method like run_check
    """

    helpers = {}

    @classmethod
    def match(cls, cmd):
        """
            Method checks whether it is usefull patch method
        """
        return NotImplementedError()

    @classmethod
    def run_patch(cls, *args, **kwargs):
        """
            Method will check all patches in relevant package
        """
        return NotImplementedError()

@register_patch_tool
class GitPatchTool(PatchBase):
    """
    Class for git command used for patching old and new
    sources
    """
    CMD = 'git'
    source_dir = ""
    old_sources = ""
    new_sources = ""
    diff_cls = None
    output_data = []
    old_repo = None
    new_repo = None
    git_helper = None

    @classmethod
    def match(cls, cmd):
        if cls.CMD == cmd:
            return True
        else:
            return False

    @staticmethod
    def apply_patch(git_helper, patch_name):
        logger.debug('Applying patch with am')

        ret_code = git_helper.command_am(input_file=patch_name)
        if int(ret_code) != 0:
            ret_code = git_helper.command_am(parameters='--abort', input_file=patch_name)
            logger.debug('Applying patch with git am failed.')
            ret_code = git_helper.command_apply(input_file=patch_name)
            GitPatchTool.commit_patch(git_helper, patch_name)
        return ret_code

    @classmethod
    def _prepare_git(cls, upstream_name):
        ret_code = cls.git_helper.command_remote_add(upstream_name, cls.new_sources)
        ret_code = cls.git_helper.command_fetch(upstream_name)
        cls.output_data = cls.git_helper.command_log(parameters='--pretty=oneline')
        last_hash = GitHelper.get_commit_hash_log(cls.output_data, number=0)
        init_hash = GitHelper.get_commit_hash_log(cls.output_data, len(cls.output_data)-1)
        return init_hash, last_hash

    @classmethod
    def _git_rebase(cls):
        # in old_sources do.
        # 1) git remote add new_sources <path_to_new_sources>
        # 2) git fetch new_sources
        # 3 git rebase -i --onto new_sources/master <oldest_commit_old_source> <the_latest_commit_old_sourcese>
        if not cls.cont:
            logger.info('Git-rebase operation to {0} is ongoing...'.format(os.path.basename(cls.new_sources)))
            upstream = 'new_upstream'
            init_hash, last_hash = cls._prepare_git(upstream)
            ret_code, cls.output_data = cls.git_helper.command_rebase(parameters='--onto',
                                                                      upstream_name=upstream,
                                                                      first_hash=init_hash,
                                                                      last_hash=last_hash)
        else:
            logger.info('Git-rebase operation continues...')
            ret_code, cls.output_data = cls.git_helper.command_rebase(parameters='--skip')
            logger.debug(cls.output_data)
        patch_name = ""
        modified_patches = []
        deleted_patches = []
        while True:
            if int(ret_code) != 0:
                patch_name = cls.git_helper.get_unapplied_patch(cls.output_data)
                ret_code = cls.git_helper.command_mergetool()
                modified_files = cls.git_helper.command_diff_status()
                ret_code = cls.git_helper.command_add_files(parameters=modified_files)
                base_name = os.path.join(cls.kwargs['results_dir'], patch_name)
                ret_code = cls.git_helper.command_diff('HEAD', output_file=base_name)
                with open(base_name, "r") as f:
                    cls.output_data = f.readlines()
                if not cls.output_data:
                    deleted_patches.append(base_name)
                else:
                    logger.info('Some files were not modified')
                    ret_code = cls.git_helper.command_commit(message=patch_name)
                    ret_code, cls.output_data = cls.git_helper.command_diff('HEAD~1', output_file=base_name)
                    modified_patches.append(base_name)
                if not ConsoleHelper.get_message('Do you want to continue with another patch'):
                    raise KeyboardInterrupt
                ret_code, cls.output_data = cls.git_helper.command_rebase('--skip')
            else:
                break

        #TODO correct settings for merge tool in ~/.gitconfig
        # currently now meld is not started
        return {'modified': modified_patches, 'deleted': deleted_patches}

    @staticmethod
    def commit_patch(git_helper, patch_name):
        logger.debug('Commit patch')
        ret_code = git_helper.command_add_files(parameters=['--all'])
        if int(ret_code) != 0:
            raise GitRebaseError('We are not able to add changed files to local git repository.')
        ret_code = git_helper.command_commit(message='Patch: {0}'.format(os.path.basename(patch_name)))
        return ret_code

    @classmethod
    def apply_old_patches(cls, patches):
        """
        Function applies a patch to a old/new sources
        """
        for patch in patches:
            patch_path = patch.get_path()
            logger.info("Applying patch '{0}' to '{1}'".format(os.path.basename(patch_path),
                                                               os.path.basename(cls.source_dir)))
            ret_code = GitPatchTool.apply_patch(cls.git_helper, patch_path)
            # unexpected
            if int(ret_code) != 0:
                if cls.source_dir == cls.old_sources:
                    raise RuntimeError('Failed to patch old sources')

    @classmethod
    def init_git(cls, directory):
        gh = GitHelper(directory)
        ret_code = gh.command_init(directory)
        gh.command_add_files('.')
        gh.command_commit(message='Initial Commit')

    @classmethod
    def run_patch(cls, old_dir, new_dir, patches, **kwargs):
        """
        The function can be used for patching one
        directory against another
        """
        cls.kwargs = kwargs
        cls.old_sources = old_dir
        cls.new_sources = new_dir
        cls.output_data = []
        cls.cont = cls.kwargs['continue']
        cls.git_helper = GitHelper(cls.old_sources)
        if not os.path.isdir(os.path.join(cls.old_sources, '.git')):
            cls.init_git(old_dir)
            cls.init_git(new_dir)
            cls.source_dir = cls.old_sources
            cls.apply_old_patches(patches)
            cls.cont = False

        return cls._git_rebase()


class Patcher(object):
    """
    Class representing a process of applying and generating rebased patch using specific tool.
    """

    def __init__(self, tool=None):
        """
        Constructor

        :param tool: tool to be used. If not supported, raises NotImplementedError
        :return: None
        """
        if tool is None:
            raise TypeError("Expected argument 'tool' (pos 1) is missing")
        self._path_tool_name = tool
        self._tool = None

        for patch_tool in patch_tools.values():
            if patch_tool.match(self._path_tool_name):
                self._tool = patch_tool

        if self._tool is None:
            raise NotImplementedError("Unsupported patch tool")

    def patch(self, old_dir, new_dir, patches, **kwargs):
        """
        Apply patches and generate rebased patches if needed

        :param old_dir: path to dir with old patches
        :param new_dir: path to dir with new patches
        :param patches: old patches
        :param rebased_patches: rebased patches
        :param kwargs: --
        :return:
        """
        logger.debug("Patching source by patch tool {0}".format(self._path_tool_name))
        return self._tool.run_patch(old_dir, new_dir, patches, **kwargs)




