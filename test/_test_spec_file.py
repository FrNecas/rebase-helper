# -*- coding: utf-8 -*-

import os
from rebasehelper import specfile


class TestSpecHelper(object):
    """ SpecHelper tests """
    specfile = os.path.join(os.path.dirname(__file__),"test.spec")
    CONFIG_SECTION='--build=x86_64-redhat-linux-gnu --host=x86_64-redhat-linux-gnu'
    MAKE=['TEST']
    MAKE_INSTALL=['DESTDIR=$RPM_BUILD_ROOT','install']
        
    def test_spec_file(self):
        assert os.path.exists(self.specfile)
        
    def test_config_section(self):
        spec = specfile.Specfile(self.specfile)
        assert spec.get_config_options()
        
    def test_make_section(self):
        spec = specfile.Specfile(self.specfile)
        assert spec.get_make_options() == self.MAKE

    def test_make_install_section(self):
        spec = specfile.Specfile(self.specfile)
        assert spec.get_make_install_options() == self.MAKE_INSTALL
