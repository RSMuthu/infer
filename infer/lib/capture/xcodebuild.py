# Copyright (c) 2015 - present Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the BSD style license found in the
# LICENSE file in the root directory of this source tree. An additional grant
# of patent rights can be found in the PATENTS file in the same directory.

import os
import subprocess
import traceback
import logging
import util

MODULE_NAME = __name__
MODULE_DESCRIPTION = '''Run analysis of code built with a command like:
xcodebuild [options]

Analysis examples:
infer -- xcodebuild -target HelloWorldApp -sdk iphonesimulator
infer -- xcodebuild -workspace HelloWorld.xcworkspace -scheme HelloWorld'''

SCRIPT_DIR = os.path.dirname(__file__)
INFER_ROOT = os.path.join(SCRIPT_DIR, '..', '..', '..')
FCP_ROOT = os.path.join(INFER_ROOT, '..', 'facebook-clang-plugin')
CLANG_WRAPPER = os.path.join(
    SCRIPT_DIR, 'clang',
)
CLANGPLUSPLUS_WRAPPER = os.path.join(
    SCRIPT_DIR, 'clang++',
)


def gen_instance(*args):
    return XcodebuildCapture(*args)

create_argparser = \
    util.clang_frontend_argparser(MODULE_DESCRIPTION, MODULE_NAME)


class XcodebuildCapture:
    def __init__(self, args, cmd):
        self.args = args
        self.apple_clang_path = \
            subprocess.check_output(['xcrun', '--find', 'clang']).strip()

        xcode_version = util.run_cmd_ignore_fail(['xcodebuild', '-version'])
        apple_clang_version = util.run_cmd_ignore_fail([self.apple_clang_path,
                                                        '--version'])
        logging.info('Xcode version:\n%s', xcode_version)

        logging.info('clang version:\n%s', apple_clang_version)

        self.cmd = cmd

    def get_envvars(self):
        env_vars = dict(os.environ)

        env_vars['FCP_APPLE_CLANG'] = self.apple_clang_path

        frontend_env_vars = \
            util.get_clang_frontend_envvars(self.args)
        env_vars.update(frontend_env_vars)
        return env_vars

    def capture(self):
        # these settings will instruct xcodebuild on which clang to use
        self.cmd += ['CC={wrapper}'.format(wrapper=CLANG_WRAPPER)]
        self.cmd += ['CPLUSPLUS={wrapper}'.format(wrapper=CLANGPLUSPLUS_WRAPPER)]

        # skip the ProcessPCH phase to fix the "newer/older" incompatibility
        # error for the pch files generated by apple's clang and
        # the open-source one
        self.cmd += ['GCC_PRECOMPILE_PREFIX_HEADER=NO']

        try:
            subprocess.check_call(self.cmd, env=self.get_envvars())
            return os.EX_OK
        except subprocess.CalledProcessError as exc:
            if self.args.debug:
                traceback.print_exc()
            print(exc.output)
            return exc.returncode
