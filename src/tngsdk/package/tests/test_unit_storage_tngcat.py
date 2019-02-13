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
from mock import patch
from requests.exceptions import RequestException
from requests import get as real_get
from tngsdk.package.cli import parse_args
from tngsdk.package.packager import PM
from tngsdk.package.storage.tngcat import TangoCatalogBackend
from tngsdk.package.storage.tngcat import mime_to_pltfrm
from tngsdk.package.tests.fixtures import misc_file


class MockResponsePost(object):

    def __init__(self):
        self.status_code = 201
        self.text = "uuid: 1111"

    def json(self):
        return {"uuid": "2222"}


class MockResponseGet(object):

    def __init__(self):
        self.status_code = 200
        self.text = "[]"

    def json(self):
        return []


class MockArgs(object):

    def __init__(self):
        self.cat_url = "http://tng-cat:4011/catalogues/api/v2/"

    def __contains__(self, key):
        return key in self.__dict__

    def get(self, key):
        return self.__dict__.get(key)


def mock_requests_post(url, **kwargs):
    if ("http://127.0.0.1:4011/catalogues/api/v2/" not in url
            and "http://tng-cat:4011/catalogues/api/v2/" not in url):
        raise RequestException("bad url received in mock")
    assert(kwargs.get("data") is not None)
    assert(kwargs.get("headers") is not None)
    mr = MockResponsePost()
    return mr


def mock_requests_get(url, **kwargs):
    if ("http://127.0.0.1:4011/catalogues/api/v2/" not in url
            and "http://tng-cat:4011/catalogues/api/v2/" not in url):
        # do real request if no cat url
        return real_get(url)
    assert(kwargs.get("headers") is not None)
    mr = MockResponseGet()
    return mr


class TngSdkPackageStorageTngCatTest(unittest.TestCase):

    def setUp(self):
        # configure mocks
        self.patcher = patch("requests.post", mock_requests_post)
        self.patcher2 = patch("requests.get", mock_requests_get)
        # we need a packager to setup a environment to work on
        self.default_args = parse_args([])
        self.default_args.unpackage = misc_file(
            "eu.5gtango.mixed-ns-package-example.0.1.tgo")
        self.p = PM.new_packager(
            self.default_args,
            pkg_format="eu.5gtango",
            storage_backend=None
        )
        # patch the requests lib to not do real requests
        self.patcher.start()
        self.patcher2.start()

    def tearDown(self):
        self.patcher.stop()
        self.patcher2.stop()

    def test_init(self):
        tcb = TangoCatalogBackend(MockArgs())
        self.assertIsNotNone(tcb)

    def test_store(self):
        # instantiate storage backend
        tcb = TangoCatalogBackend(MockArgs())
        self.assertIsNotNone(tcb)
        # unpack package and keep active working dir.
        napdr = self.p._do_unpackage()
        wd = napdr.metadata.get("_napd_path").replace(
            "/TOSCA-Metadata/NAPD.yaml", "")
        # call store using active working dir
        new_napdr = tcb.store(
            napdr, wd, self.default_args.unpackage)
        self.assertEqual(new_napdr.package_file_name,
                         "eu.5gtango.mixed-ns-package-example.0.1.tgo")
        self.assertEqual(new_napdr.package_file_uuid, "2222")
        self.assertEqual(new_napdr.metadata.get("_storage_uuid"), "1111")
        self.assertIsNotNone(new_napdr.metadata.get("_storage_location"))

    def test_file_match(self):
        tcb = TangoCatalogBackend(MockArgs())
        self.assertIsNotNone(tcb)
        # unpack package and keep active working dir.
        napdr = self.p._do_unpackage()
        wd = napdr.metadata.get("_napd_path").replace(
            "/TOSCA-Metadata/NAPD.yaml", "")
        # tests:
        # ---
        files = tcb._get_package_content_of_type(
            napdr, wd, "application/vnd.5gtango.nsd")
        print(files)
        [self.assertIn("5gtango_nsd.yaml", item)
            for (mime, item) in files]
        # ---
        files = tcb._get_package_content_of_type(
            napdr, wd, "application/vnd.*.nsd")
        print(files)
        self.assertEqual(len(files), 3)
        [self.assertIn("_nsd.yaml", item) for (mime, item) in files]
        # ---
        files = tcb._get_package_content_of_type(
            napdr, wd, "application/vnd.osm*")
        print(files)
        self.assertEqual(len(files), 2)

    def test_file_not_match(self):
        tcb = TangoCatalogBackend(MockArgs())
        self.assertIsNotNone(tcb)
        # unpack package and keep active working dir.
        napdr = self.p._do_unpackage()
        wd = napdr.metadata.get("_napd_path").replace(
            "/TOSCA-Metadata/NAPD.yaml", "")
        # tests:
        # ---
        files = tcb._get_package_content_not_of_type(
            napdr, wd, "application/vnd.5gtango.nsd")
        self.assertEqual(len(files), 9)
        # ---
        files = tcb._get_package_content_not_of_type(
            napdr, wd, "application/vnd.*.nsd")
        print(files)
        self.assertEqual(len(files), 7)
        [self.assertNotIn("_nsd.yaml", item) for (mime, item) in files]

    def test_mime_to_pltfrm(self):
        self.assertEqual(
            mime_to_pltfrm(
                "application/vnd.5gtango.nsd"), "5gtango")
        self.assertEqual(
            mime_to_pltfrm(
                "application/vnd.osm.nsd"), "osm")
        self.assertEqual(
            mime_to_pltfrm(
                "application/vnd.onap.nsd"), "onap")
        self.assertEqual(
            mime_to_pltfrm(
                "jdhadhkadhajskdhaslk"), None)
