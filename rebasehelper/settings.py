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

REBASE_HELPER_SUFFIX = "-rebase"
REBASE_HELPER_PREFIX = "rebase-helper-"

REBASE_HELPER_RESULTS_DIR = REBASE_HELPER_PREFIX + "results"
REBASE_HELPER_WORKSPACE_DIR = REBASE_HELPER_PREFIX + "workspace"

OLD_SOURCES = 'old_sources'
NEW_SOURCES = 'new_sources'
OLD_SOURCES_DIR = os.path.join(REBASE_HELPER_WORKSPACE_DIR, OLD_SOURCES)
NEW_SOURCES_DIR = os.path.join(REBASE_HELPER_WORKSPACE_DIR, NEW_SOURCES)

# The variable for access to full information about patches
FULL_PATCHES = 'patches_full'

REBASE_HELPER_LOG = 'rebase-helper.log'