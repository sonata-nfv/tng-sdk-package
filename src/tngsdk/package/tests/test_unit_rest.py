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
import json
import time
from mock import patch
from requests.exceptions import RequestException
from tngsdk.package.rest import app, on_unpackaging_done, on_packaging_done
from tngsdk.package.packager import PM
from tngsdk.package.cli import parse_args
from tngsdk.package.tests.fixtures import misc_file
from werkzeug.datastructures import FileStorage


class MockArgs(object):
    def __init__(self):
        self.package = None
        self.unpackage = None
        self.callback_url = "https://test.local:8000/cb"

    def __contains__(self, key):
        return key in self.__dict__

    def get(self, key):
        return self.__dict__.get(key)


class MockResponse(object):
    pass


def mock_requests_post(url, json):
    if url != "https://test.local:8000/cb":
        raise RequestException("bad url")
    if "event_name" not in json:
        raise RequestException("bad request")
    if "package_id" not in json:
        raise RequestException("bad request")
    if "package_location" not in json:
        raise RequestException("bad request")
    if "package_metadata" not in json:
        raise RequestException("bad request")
    if "package_process_uuid" not in json:
        raise RequestException("bad request")
    mr = MockResponse()
    mr.status_code = 200
    return mr


class TngSdkPackageRestTest(unittest.TestCase):

    def setUp(self):
        # configure mocks
        self.patcher = patch("requests.post", mock_requests_post)
        self.patcher.start()
        # configure flask
        app.config['TESTING'] = True
        app.cliargs = parse_args([])
        self.app = app.test_client()

    def tearDown(self):
        self.patcher.stop()

    def test_project_v1_endpoint(self):
        # do a malformed post
        r = self.app.post("/api/v1/projects",
                          content_type="multipart/form-data",
                          data={"project": (None,
                                            "5gtango-ns-project-example.zip"),
                                "callback_url": "https://test.local:8000/cb",
                                "skip_store": True})
        self.assertEqual(r.status_code, 500)
        # do a acceptable post
        f = open(misc_file("5gtango_ns_a10_nginx_zipped_project_example.tgo"),
                 "rb")
        project = FileStorage(f)
        r = self.app.post("/api/v1/projects",
                          content_type="multipart/form-data",
                          data={"project": project,
                                "callback_url": "https://test.local:8000/cb",
                                "skip_store": True})
        self.assertEqual(r.status_code, 200)
        f.close()

    def test_project_project_download_v1_get_endpoints(self):
        r = self.app.get("api/v1/projects")
        self.assertEqual(r.status_code, 200)
        r = json.loads(r.get_data(as_text=True))
        self.assertIsInstance(r, list)
        self.assertIsInstance(r[0], dict)
        self.assertIn("package_name", r[0])
        self.assertIn("package_download_link", r[0])
        r = self.app.get(r[0]["package_download_link"])
        self.assertEqual(r.status_code, 200)
        r = r.response
        r = FileStorage(r)
        self.assertIsInstance(r, FileStorage)

    def test_package_v1_endpoint(self):
        # do a malformed post
        r = self.app.post("/api/v1/packages")
        self.assertEqual(r.status_code, 400)
        # do a post with a real package
        r = self.app.post("/api/v1/packages",
                          content_type="multipart/form-data",
                          data={"package": (
                              open("misc/5gtango-ns-package-example.tgo",
                                   "rb"), "5gtango-ns-package-example.tgo"),
                                "skip_store": True})
        self.assertEqual(r.status_code, 200)
        rd = json.loads(r.get_data(as_text=True))
        self.assertIn("package_process_uuid", rd)
        # do a post with a real package and callback_url
        r = self.app.post("/api/v1/packages",
                          content_type="multipart/form-data",
                          data={"package": (
                              open("misc/5gtango-ns-package-example.tgo",
                                   "rb"), "5gtango-ns-package-example.tgo"),
                                "callback_url": "https://test.local:8000/cb",
                                "skip_store": True})  # skip store step in test
        self.assertEqual(r.status_code, 200)
        rd = json.loads(r.get_data(as_text=True))
        self.assertIn("package_process_uuid", rd)

    def test_package_v1_endpoint_with_username(self):
        # do a malformed post
        r = self.app.post("/api/v1/packages")
        self.assertEqual(r.status_code, 400)
        # do a post with a real package
        r = self.app.post("/api/v1/packages",
                          content_type="multipart/form-data",
                          data={"package": (
                              open("misc/5gtango-ns-package-example.tgo",
                                   "rb"), "5gtango-ns-package-example.tgo"),
                                "skip_store": True,
                                "username": "test_user1"})
        self.assertEqual(r.status_code, 200)
        rd = json.loads(r.get_data(as_text=True))
        self.assertIn("package_process_uuid", rd)

    def test_packager_v1_status_endpoint(self):
        # do a post with a real package
        r = self.app.post("/api/v1/packages",
                          content_type="multipart/form-data",
                          data={"package": (
                              open("misc/5gtango-ns-package-example.tgo",
                                   "rb"), "5gtango-ns-package-example.tgo"),
                                "skip_store": True})
        self.assertEqual(r.status_code, 200)
        rd = json.loads(r.get_data(as_text=True))
        self.assertIn("package_process_uuid", rd)
        # do a call to the status endpoint
        r2 = self.app.get(
            "/api/v1/packages/status/{}".format(
                rd.get("package_process_uuid")))
        self.assertEqual(r2.status_code, 200)
        rd2 = json.loads(r2.get_data(as_text=True))
        self.assertIn("package_process_uuid", rd2)
        self.assertEqual(rd2.get("status"), "running")
        # wait a bit so that packager can finalize
        # needs to be much more because the validator seems to be quite
        # slow from time to time
        time.sleep(30)
        r2 = self.app.get(
            "/api/v1/packages/status/{}".format(
                rd.get("package_process_uuid")))
        self.assertEqual(r2.status_code, 200)
        rd2 = json.loads(r2.get_data(as_text=True))
        self.assertIn("package_process_uuid", rd2)
        self.assertEqual(rd2.get("status"), "success")
        # do a call to a non existing packager status
        r2 = self.app.get(
            "/api/v1/packages/status/{}".format("foo-bar"))
        self.assertEqual(r2.status_code, 404)

    def test_on_packaging_done(self):
        args = MockArgs()
        p = PM.new_packager(args)
        p.result.metadata["_storage_location"] = "testdir/test.tgo"
        print(p.__dict__)
        with app.test_request_context():
            s = on_packaging_done(p)
        self.assertEqual(s, 200)

    def test_on_unpackaging_done(self):
        args = MockArgs()
        p = PM.new_packager(args)
        s = on_unpackaging_done(p)
        self.assertEqual(s, 200)

    def test_ping_v1_endpoint(self):
        # do a call to the ping endpoint
        r1 = self.app.get("/api/v1/pings")
        self.assertEqual(r1.status_code, 200)
        rd1 = json.loads(r1.get_data(as_text=True))
        self.assertIn("alive_since", rd1)
