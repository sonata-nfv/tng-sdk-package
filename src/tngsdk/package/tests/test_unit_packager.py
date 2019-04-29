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
import threading
from tngsdk.package.cli import parse_args
from tngsdk.package.packager import PM, parse_block_based_meta_file


class TngSdkPackagePackagerHelperTest(unittest.TestCase):

    def setUp(self):
        # list can manually define CLI arguments
        self.default_args = parse_args([])

    def tearDown(self):
        pass

    # @unittest.skip("skip")
    def test_parse_block_based_meta_file(self):
        # test case
        i = """
            Key1: Value1
            """
        b = parse_block_based_meta_file(i)
        self.assertEqual(len(b), 1)
        # test case
        i = """
            Key1: Value1
            Key2: Value2: Value
            """
        b = parse_block_based_meta_file(i)
        self.assertEqual(len(b), 1)
        self.assertEqual(b[0], {"Key1": "Value1", "Key2": "Value2: Value"})
        # test case
        i = """

            Key1: Value1
            Key1: Value1
            Key1: Value1

            Key1: Value1

            Key1: Value1

            Key1: Value1
            """
        b = parse_block_based_meta_file(i)
        self.assertEqual(len(b), 4)


class TngSdkPackagePackagerTest(unittest.TestCase):

    def setUp(self):
        # list can manually define CLI arguments
        self.default_args = parse_args([])

    def tearDown(self):
        pass

    def test_instantiation_default(self):
        p = PM.new_packager(self.default_args)
        self.assertIn("TangoPackager", str(type(p)))
        del p

    def test_instantiation_tango(self):
        p = PM.new_packager(self.default_args, pkg_format="eu.5gtango")
        self.assertIn("TangoPackager", str(type(p)))
        del p

    def test_instantiation_etsi(self):
        p = PM.new_packager(self.default_args, pkg_format="eu.etsi")
        self.assertIn("EtsiPackager", str(type(p)))
        del p

    def test_package_sync(self):
        p = PM.new_packager(self.default_args, pkg_format="test")
        p.package()

    def test_unpackage_sync(self):
        p = PM.new_packager(self.default_args, pkg_format="test")
        p.unpackage()

    def test_package_async(self):
        lock = threading.Semaphore()
        lock.acquire()

        def cb(args):
            lock.release()

        p = PM.new_packager(self.default_args, pkg_format="test")
        p.package(callback_func=cb)
        self.assertTrue(lock.acquire(timeout=3.0),
                        msg="callback was not called before timeout")

    def test_unpackage_async(self):
        lock = threading.Semaphore()
        lock.acquire()

        def cb(args):
            lock.release()

        p = PM.new_packager(self.default_args, pkg_format="test")
        p.unpackage(callback_func=cb)
        self.assertTrue(lock.acquire(timeout=3.0),
                        msg="callback was not called before timeout")

    def test_autoversion(self):
        p = PM.new_packager(self.default_args, pkg_format="test")
        project_descriptors = [{"package": {"version": "1.0"}},
                               {"package": {"version": "1.0.3"}},
                               {"package": {"version": 1.5}}]
        project_descriptor_results = [{"package": {"version": "1.0.1"}},
                                      {"package": {"version": "1.0.4"}},
                                      {"package": {"version": "1.5.1"}}]
        for desc, result in zip(project_descriptors,
                                project_descriptor_results):
            self.assertEqual(p.autoversion(desc),
                             result)

        project_descriptors_invalid = [{"package": {"version": "1"}},
                                       {"package": {"version": "1.0.1.9"}},
                                       {"package": {"version": "1.0"}},
                                       {"package": {"version": "1."}},
                                       {"package": {"version": "1.0."}},
                                       {"package": {"version": "text"}},
                                       {"package": {"version": ".1.0.2"}}]

        for desc in project_descriptors_invalid:
            project_descriptor = p.autoversion(desc)
            self.assertEqual(project_descriptor, desc)
