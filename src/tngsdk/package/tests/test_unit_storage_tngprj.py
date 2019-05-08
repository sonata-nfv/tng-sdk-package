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
import shutil
from tngsdk.package.cli import parse_args
from tngsdk.package.packager import PM
from tngsdk.package.storage.tngprj import TangoProjectFilesystemBackend
from tngsdk.package.tests.fixtures import misc_file


class TngSdkPackageStorageTngPrjTest(unittest.TestCase):

    def setUp(self):
        # we need a packager to setup a environment to work on
        self.default_args = parse_args(["-o", tempfile.mkdtemp()])
        self.default_args.unpackage = misc_file(
            "5gtango-ns-package-example.tgo")
        self.p = PM.new_packager(
            self.default_args,
            pkg_format="eu.5gtango",
            storage_backend=None
        )

    def test_init(self):
        tpb = TangoProjectFilesystemBackend(self.default_args)
        self.assertIsNotNone(tpb)

    def test_store(self):
        # instantiate storage backend
        tpb = TangoProjectFilesystemBackend(self.default_args)
        self.assertIsNotNone(tpb)
        # unpack package and keep active working dir.
        napdr = self.p._do_unpackage()
        wd = napdr.metadata.get("_napd_path").replace(
            "/TOSCA-Metadata/NAPD.yaml", "")
        # call store using active working dir
        new_napdr = tpb.store(
            napdr, wd, self.default_args.unpackage)
        # check result
        self.assertIsNotNone(new_napdr.metadata.get("_storage_location"))
        sl = new_napdr.metadata.get("_storage_location")
        # check created project
        pd = self.default_args.output
        self.assertTrue(os.path.exists(pd))
        self.assertTrue(os.path.exists(
            os.path.join(pd, "5gtango-ns-package-example/project.yml")))
        self.assertTrue(os.path.exists(
            os.path.join(sl, "project.yml")))
        self.assertTrue(os.path.exists(
            os.path.join(sl, "sources/")))
        self.assertTrue(os.path.exists(
            os.path.join(
                sl, "sources/nsd/nsd-sample.yml")))
        self.assertTrue(os.path.exists(
            os.path.join(
                sl, "sources/vnfd/vnfd-sample.yml")))
        shutil.rmtree(pd)

    def test_store_idempotent(self):
        self.default_args = parse_args(["-o", tempfile.mkdtemp()])
        self.default_args.unpackage = misc_file(
            "eu.5gtango.idempotency_test.0.1.tgo")
        self.p = PM.new_packager(
            self.default_args,
            pkg_format="eu.5gtango",
            storage_backend=None
        )
        tpb = TangoProjectFilesystemBackend(self.default_args)

        napdr = self.p._do_unpackage()
        wd = napdr.metadata.get("_napd_path").replace(
            "/TOSCA-Metadata/NAPD.yaml", "")
        # call store using active working dir
        new_napdr = tpb.store(
            napdr, wd, self.default_args.unpackage)
        # check result
        self.assertIsNotNone(new_napdr.metadata.get("_storage_location"))
        sl = new_napdr.metadata.get("_storage_location")
        # check created project
        pd = self.default_args.output
        self.assertTrue(os.path.exists(pd))
        self.assertTrue(os.path.exists(
            os.path.join(pd, "eu.5gtango.idempotency_test.0.1/project.yml")))
        self.assertTrue(os.path.exists(
            os.path.join(sl, "project.yml")))
        # files in root dir
        self.assertTrue(os.path.exists(
            os.path.join(sl, "vnfd-a10-3.yml")))
        self.assertTrue(os.path.exists(
            os.path.join(sl, "vnfd-nginx-3.yml")))
        # files in sources/
        self.assertTrue(os.path.exists(
            os.path.join(sl, "sources/")))
        self.assertTrue(os.path.exists(
            os.path.join(sl, "sources/vnfd-a10-4.yml")))
        self.assertTrue(os.path.exists(
            os.path.join(sl, "sources/vnfd-nginx-4.yml")))
        # files in sources/[...]/
        self.assertTrue(os.path.exists(
            os.path.join(
                sl, "sources/nsd/nsd.yml")))
        self.assertTrue(os.path.exists(
            os.path.join(
                sl, "sources/vnfd/vnfd-a10.yml")))
        self.assertTrue(os.path.exists(
            os.path.join(
                sl, "sources/vnfd/vnfd-nginx.yml")))
        # files in other folders of root dir
        self.assertTrue(os.path.exists(
            os.path.join(sl, "Definitions/")))
        self.assertTrue(os.path.exists(
            os.path.join(sl, "Definitions/vnfd-a10-2.yml")))
        self.assertTrue(os.path.exists(
            os.path.join(sl, "Definitions/vnfd-nginx-2.yml")))
        shutil.rmtree(pd)
