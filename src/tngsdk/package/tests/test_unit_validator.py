#  Copyright (c) 2015 SONATA-NFV, 5GTANGO, UBIWHERE, Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, 5GTANGO, UBIWHERE, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
#
# This work has also been performed in the framework of the 5GTANGO project,
# funded by the European Commission under Grant number 761493 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.5gtango.eu).

import unittest
import tempfile
import os
from tngsdk.package.cli import parse_args
from tngsdk.package.packager import PM
from tngsdk.package.tests.fixtures import misc_file


class TngSdkPackageValidatorTest(unittest.TestCase):
    """
    Test if externel tng-sdk-validate works.
    """

    def test_do_unpackage_good_package(self):
        self.default_args = parse_args([])
        self.default_args.unpackage = misc_file(
            "5gtango-ns-package-example.tgo")
        self.p = PM.new_packager(
           self.default_args, pkg_format="eu.5gtango")
        r = self.p._do_unpackage()
        self.assertIsNone(r.error)

    def test_do_unpackage_bad_package(self):
        self.default_args = parse_args([])
        self.default_args.unpackage = misc_file(
            "5gtango-ns-package-example-bad.tgo")
        self.p = PM.new_packager(
           self.default_args, pkg_format="eu.5gtango")
        r = self.p._do_unpackage()
        self.assertIsNotNone(r.error)
        self.assertIn("tng-validate error", r.error)
        # self.assertIn("Failed to read service function descriptors", r.error)

    def test_do_package_good_project(self):
        self.default_args = parse_args([])
        self.default_args.package = misc_file(
            "5gtango_ns_project_example1")
        self.default_args.output = os.path.join(tempfile.mkdtemp(),
                                                "test.tgo")
        p = PM.new_packager(self.default_args, pkg_format="eu.5gtango")
        r = p._do_package()
        self.assertIsNone(r.error)
        # check *.tgo file
        self.assertTrue(os.path.exists(self.default_args.output))

    def test_do_package_bad_project(self):
        self.default_args = parse_args([])
        self.default_args.package = misc_file(
            "5gtango_ns_project_example1_bad")
        self.default_args.output = os.path.join(tempfile.mkdtemp(),
                                                "test.tgo")
        p = PM.new_packager(self.default_args, pkg_format="eu.5gtango")
        r = p._do_package()
        self.assertIsNotNone(r.error)
        self.assertIn("tng-validate error", r.error)
        # self.assertIn("Failed to read service function descriptors", r.error)
        # check *.tgo file
        self.assertFalse(os.path.exists(self.default_args.output))
