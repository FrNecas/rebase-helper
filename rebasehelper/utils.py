# -*- coding: utf-8 -*-

import subprocess

class ProcessHelper(object):
    
    @staticmethod
    def run_subprocess(cmd, output=None):
        if output is not None:
            out_file = open(output, "w")
        else:
            out_file = None
        sp = subprocess.Popen(cmd,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT,
                              shell=False)
        for line in sp.stdout:
            if out_file is not None:
                out_file.write(line)
            else:
                print line.rstrip("\n")
        sp.wait()
        return sp.returncode
