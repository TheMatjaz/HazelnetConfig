#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright © 2020-2022, Matjaž Guštin <dev@matjaz.it>
# <https://matjaz.it>. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 3. Neither the name of nor the names of its contributors may be used to
#    endorse or promote products derived from this software without specific
#    prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER AND CONTRIBUTORS “AS IS”
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import unittest

import hzlconfig

THIS_FILE_DIR = os.path.dirname(__file__)
EXAMPLE_FILE_PATH = os.path.join(THIS_FILE_DIR, '..', 'example.json')
OBTAINED_DIR = os.path.join(THIS_FILE_DIR, 'generated')
EXPECTED_DIR = os.path.join(THIS_FILE_DIR, 'expected')


class TestBinaryFileGeneration(unittest.TestCase):
    @staticmethod
    def binary_files_equal(file_name_a: str, file_name_b: str) -> bool:
        with open(file_name_a, 'rb') as file_a, \
            open(file_name_b, 'rb') as file_b:
            content_a = file_a.read()
            content_b = file_b.read()
            return content_a == content_b

    def test_example_matches_expected(self):
        hzlconfig.compile_json_file(EXAMPLE_FILE_PATH,
                                    output_dir_name=OBTAINED_DIR)
        self.assertTrue(self.binary_files_equal(
            os.path.join(EXPECTED_DIR, 'Alice.hzl'),
            os.path.join(OBTAINED_DIR, 'hzl_HardcodedConfigAlice.hzl'),
        ))
        self.assertTrue(self.binary_files_equal(
            os.path.join(EXPECTED_DIR, 'Bob.hzl'),
            os.path.join(OBTAINED_DIR, 'hzl_HardcodedConfigBob.hzl'),
        ))
        self.assertTrue(self.binary_files_equal(
            os.path.join(EXPECTED_DIR, 'Charlie.hzl'),
            os.path.join(OBTAINED_DIR, 'hzl_HardcodedConfigCharlie.hzl'),
        ))
        self.assertTrue(self.binary_files_equal(
            os.path.join(EXPECTED_DIR, 'Server.hzl'),
            os.path.join(OBTAINED_DIR, 'hzl_HardcodedConfigServer.hzl'),
        ))


if __name__ == '__main__':
    unittest.main()
