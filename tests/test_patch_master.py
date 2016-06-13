#!/usr/bin/env python

import os
import nose
import struct
import subprocess
import logging

import patcherex
from patcherex.patch_master import PatchMaster

l = logging.getLogger("patcherex.test.test_patch_master")

bin_location = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../../binaries-private'))
qemu_location = str(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../tracer/bin/tracer-qemu-cgc"))


def test_run():
    def no_duplicate(tlist):
        return len(tlist) == len(set(tlist))

    fname = os.path.join(bin_location, "cgc_scored_event_2/cgc/0b32aa01_01")
    pm = PatchMaster(fname)
    patches = pm.run()
    nose.tools.assert_equal(len(patches) == pm.ngenerated_patches, True)

    nose.tools.assert_equal(len(patches)>1, True)
    #nose.tools.assert_equal(no_duplicate(patches), True)

    with patcherex.utils.tempdir() as td:
        for i,p in enumerate(patches):
            tmp_fname = os.path.join(td,str(i))
            fp = open(tmp_fname,"wb")
            fp.write(p)
            fp.close()
            os.chmod(tmp_fname, 0755)
            pipe = subprocess.PIPE
            p = subprocess.Popen([qemu_location, tmp_fname], stdin=pipe, stdout=pipe, stderr=pipe)
            res = p.communicate("A"*10)
            expected = "\nWelcome to Palindrome Finder\n\n\tPlease enter a possible palindrome:" 
            nose.tools.assert_equal(expected in res[0], True)


def test_cfe_trials():
    tfolder = os.path.join(bin_location, "cgc_trials/last_trial/original/")
    tests = [os.path.join(tfolder,f) for f in os.listdir(tfolder) if os.access(os.path.join(tfolder,f),os.X_OK)]
    for test in tests:
        with patcherex.utils.tempdir() as td:
            print test
            pipe = subprocess.PIPE

            p = subprocess.Popen([qemu_location, test], stdin=pipe, stdout=pipe, stderr=pipe)
            res = p.communicate("A"*50)
            expected = (res[0],res[1],p.returncode)
            print expected

            pm = PatchMaster(test)
            patches = pm.run()
            nose.tools.assert_equal(len(patches)==pm.ngenerated_patches, True)
            for i,patch in enumerate(patches):
                print i
                tmp_fname = os.path.join(td,str(i))
                fp = open(tmp_fname,"wb")
                fp.write(patch)
                fp.close()
                os.chmod(tmp_fname, 0755)
                p = subprocess.Popen([qemu_location, test], stdin=pipe, stdout=pipe, stderr=pipe)
                res = p.communicate("A"*50)
                real = (res[0],res[1],p.returncode)
                print real
                nose.tools.assert_equal(real==expected, True)


def run_all():
    functions = globals()
    all_functions = dict(filter((lambda (k, v): k.startswith('test_')), functions.items()))
    for f in sorted(all_functions.keys()):
        if hasattr(all_functions[f], '__call__'):
            l.info("testing %s" % str(f))
            all_functions[f]()


if __name__ == "__main__":
    import sys
    logging.getLogger("patcherex.test.test_patch_master").setLevel("INFO")
    if len(sys.argv) > 1:
        globals()['test_' + sys.argv[1]]()
    else:
        run_all()

# TODO double check large scale: already touched bytes, indirect jumps checker (jmp location to mov edx, ...)
