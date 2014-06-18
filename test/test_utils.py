# -*- coding: utf-8 -*-
from cgitb import enable

import os
import tempfile
import shutil
import random
import string
from rebasehelper.utils import ProcessHelper
from rebasehelper.utils import PathHelper


class TestProcessHelper(object):
    """ ProcessHelper tests """

    class TestRunSubprocess(object):
        """ ProcessHelper - run_subprocess() tests """
        TEMP_FILE = "temp_file"
        TEMP_DIR = "temp_dir"
        OUT_FILE = "output_file"
        IN_FILE = "input_file"
        PHRASE = "hello world"
        ECHO_COMMAND = ["echo", PHRASE]
        TOUCH_COMMAND = ["touch", TEMP_FILE]
        LS_COMMAND = ["ls"]
        CAT_COMMAND = ["cat"]
        WORKING_DIR = tempfile.gettempdir()

        def setup(self):
            self.WORKING_DIR = tempfile.mkdtemp(prefix="rebase-helper-test-")
            os.chdir(self.WORKING_DIR)

        def teardown(self):
            os.chdir(tempfile.gettempdir())
            shutil.rmtree(self.WORKING_DIR)
            self.WORKING_DIR = tempfile.gettempdir()

        def test_simple_cmd(self):
            ret = ProcessHelper.run_subprocess(self.TOUCH_COMMAND)
            assert ret == 0
            assert os.path.exists(self.TEMP_FILE)

        def test_simple_cmd_with_redirected_output(self):
            ret = ProcessHelper.run_subprocess(self.ECHO_COMMAND,
                                               output=self.OUT_FILE)
            assert ret == 0
            assert os.path.exists(self.OUT_FILE)
            assert open(self.OUT_FILE).readline().strip('\n') == self.PHRASE

        def test_simple_cmd_with_input_and_redirected_output(self):
            with open(self.IN_FILE, 'w') as f:
                f.write(self.PHRASE)

            assert os.path.exists(self.IN_FILE)
            assert open(self.IN_FILE).readline().strip('\n') == self.PHRASE

            ret = ProcessHelper.run_subprocess(self.CAT_COMMAND,
                                               input=self.IN_FILE,
                                               output=self.OUT_FILE)
            assert ret == 0
            assert os.path.exists(self.OUT_FILE)
            assert open(self.OUT_FILE).readline().strip('\n') == self.PHRASE


    class TestRunSubprocessCwd(object):
        """ ProcessHelper - run_subprocess_cwd() tests """
        TEMP_FILE = "temp_file"
        TEMP_DIR = "temp_dir"
        OUT_FILE = "output_file"
        PHRASE = "hello world"
        ECHO_COMMAND = ["echo", PHRASE]
        TOUCH_COMMAND = ["touch", TEMP_FILE]
        LS_COMMAND = ["ls"]
        WORKING_DIR = tempfile.gettempdir()

        def setup(self):
            self.WORKING_DIR = tempfile.mkdtemp(prefix="rebase-helper-test-")
            os.chdir(self.WORKING_DIR)

        def teardown(self):
            os.chdir(tempfile.gettempdir())
            shutil.rmtree(self.WORKING_DIR)
            self.WORKING_DIR = tempfile.gettempdir()

        def test_simple_cmd_changed_work_dir(self):
            os.mkdir(self.TEMP_DIR)
            ret = ProcessHelper.run_subprocess_cwd(self.TOUCH_COMMAND,
                                                   self.TEMP_DIR)
            assert ret == 0
            assert os.path.exists(os.path.join(self.TEMP_DIR, self.TEMP_FILE))

        def test_simple_cmd_changed_work_dir_with_redirected_output(self):
            # create temp_file in temp_dir
            self.test_simple_cmd_changed_work_dir()
            ret = ProcessHelper.run_subprocess_cwd(self.LS_COMMAND,
                                                   self.TEMP_DIR,
                                                   output=self.OUT_FILE)
            assert ret == 0
            assert os.path.exists(os.path.join(self.TEMP_DIR, self.TEMP_FILE))
            assert os.path.exists(self.OUT_FILE)
            assert open(self.OUT_FILE).readline().strip("\n") == self.TEMP_FILE


    class TestRunSubprocessCwdEnv(object):
        """ ProcessHelper - run_subprocess_cwd_env() tests """
        OUT_FILE = "output_file"
        PHRASE = "hello world"
        WORKING_DIR = tempfile.gettempdir()

        def setup(self):
            self.WORKING_DIR = tempfile.mkdtemp(prefix="rebase-helper-test-")
            os.chdir(self.WORKING_DIR)

        def teardown(self):
            os.chdir(tempfile.gettempdir())
            shutil.rmtree(self.WORKING_DIR)
            self.WORKING_DIR = tempfile.gettempdir()

        def test_setting_new_env(self):
            # make copy of existing environment
            en_variables = os.environ.copy().keys()

            # pick up non-existing name
            while True:
                rand_name = ''.join(random.choice(string.ascii_letters) for _ in range(6)).upper()
                if rand_name not in en_variables:
                    break

            cmd = 'echo "$' + rand_name + '"'
            ret = ProcessHelper.run_subprocess_cwd_env(cmd,
                                                       env={rand_name: self.PHRASE},
                                                       output=self.OUT_FILE,
                                                       shell=True)
            assert ret == 0
            assert os.path.exists(self.OUT_FILE)
            assert open(self.OUT_FILE).readline().strip("\n") == self.PHRASE

        def test_setting_existing_env(self):
            # make copy of existing environment
            en_variables = os.environ.copy().keys()

            # there are no variables set on the system -> nothing to test
            if not en_variables:
                pass

            assert os.environ.get(en_variables[0]) != self.PHRASE

            cmd = 'echo "$' + en_variables[0] + '"'
            ret = ProcessHelper.run_subprocess_cwd_env(cmd,
                                                       env={en_variables[0]: self.PHRASE},
                                                       output=self.OUT_FILE,
                                                       shell=True)
            assert ret == 0
            assert os.path.exists(self.OUT_FILE)
            assert open(self.OUT_FILE).readline().strip("\n") == self.PHRASE


class TestPathHelper(object):
    """ PathHelper tests """

    class TestPathHelperFindBase(object):
        """ Base class for find methods """
        WORKING_DIR = tempfile.gettempdir()
        dirs = ["dir1",
                "dir1/foo",
                "dir1/faa",
                "dir1/foo/bar",
                "dir1/foo/baz",
                "dir1/bar",
                "dir1/baz",
                "dir1/baz/bar"]
        files = ["file",
                 "ffile",
                 "ppythooon",
                 "dir1/fileee",
                 "dir1/faa/pythooon",
                 "dir1/foo/pythooon",
                 "dir1/foo/bar/file",
                 "dir1/foo/baz/file",
                 "dir1/baz/ffile",
                 "dir1/bar/file",
                 "dir1/baz/bar/ffile"]

        def setup(self):
            self.WORKING_DIR = tempfile.mkdtemp(prefix="rebase-helper-test-")
            os.chdir(self.WORKING_DIR)
            for d in self.dirs:
                os.mkdir(d)
            for f in self.files:
                with open(f, "w") as fd:
                    fd.write(f)

        def teardown(self):
            os.chdir(tempfile.gettempdir())
            shutil.rmtree(self.WORKING_DIR)
            self.WORKING_DIR = tempfile.gettempdir()

    class TestFindFirstDirWithFile(TestPathHelperFindBase):
        """ PathHelper - find_first_dir_with_file() tests """
        def test_find_file(self):
            assert PathHelper.find_first_dir_with_file(
                "dir1", "file") == os.path.abspath(
                os.path.dirname(self.files[9]))
            assert PathHelper.find_first_dir_with_file(
                ".", "file") == os.path.abspath(os.path.dirname(self.files[0]))
            assert PathHelper.find_first_dir_with_file(
                "dir1/baz", "file") is None

        def test_find_ffile(self):
            assert PathHelper.find_first_dir_with_file(
                "dir1", "*le") == os.path.abspath(
                os.path.dirname(self.files[8]))
            assert PathHelper.find_first_dir_with_file(
                "dir1", "ff*") == os.path.abspath(
                os.path.dirname(self.files[8]))
            assert PathHelper.find_first_dir_with_file(
                "dir1/foo", "ff*") is None

        def test_find_pythoon(self):
            assert PathHelper.find_first_dir_with_file(
                "dir1", "pythooon") == os.path.abspath(
                os.path.dirname(self.files[4]))
            assert PathHelper.find_first_dir_with_file(
                ".", "py*n") == os.path.abspath(os.path.dirname(self.files[4]))
            assert PathHelper.find_first_dir_with_file(
                "dir1/bar", "pythooon") is None

    class TestFindFirstFile(TestPathHelperFindBase):
        """ PathHelper - find_first_file() tests """
        def test_find_file(self):
            assert PathHelper.find_first_file(
                "dir1", "file") == os.path.abspath(self.files[9])
            assert PathHelper.find_first_file(
                ".", "file") == os.path.abspath(self.files[0])
            assert PathHelper.find_first_file("dir1/baz", "file") is None

        def test_find_ffile(self):
            assert PathHelper.find_first_file(
                "dir1", "*le") == os.path.abspath(self.files[8])
            assert PathHelper.find_first_file(
                "dir1", "ff*") == os.path.abspath(self.files[8])
            assert PathHelper.find_first_file("dir1/foo", "ff*") is None

        def test_find_pythoon(self):
            assert PathHelper.find_first_file(
                "dir1", "pythooon") == os.path.abspath(self.files[4])
            assert PathHelper.find_first_file(
                ".", "py*n") == os.path.abspath(self.files[4])
            assert PathHelper.find_first_file("dir1/bar", "pythooon") is None
