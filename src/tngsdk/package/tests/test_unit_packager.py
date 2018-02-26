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
from tngsdk.package.packager import PM


class TngSdkPackagerTest(unittest.TestCase):

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
        p = PM.new_packager(self.default_args)
        p.package()

    def test_unpackage_sync(self):
        p = PM.new_packager(self.default_args)
        p.unpackage()

    def test_package_async(self):
        lock = threading.Semaphore()
        lock.acquire()

        def cb(args):
            lock.release()

        p = PM.new_packager(self.default_args)
        p.package(callback_func=cb)
        self.assertTrue(lock.acquire(timeout=3.0),
                        msg="callback was not called before timeout")

    def test_unpackage_async(self):
        lock = threading.Semaphore()
        lock.acquire()

        def cb(args):
            lock.release()

        p = PM.new_packager(self.default_args)
        p.unpackage(callback_func=cb)
        self.assertTrue(lock.acquire(timeout=3.0),
                        msg="callback was not called before timeout")
