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
        app.cliargs = None
        self.app = app.test_client()

    def tearDown(self):
        self.patcher.stop()

    def test_project_v1_endpoint(self):
        # do a malformed post
        r = self.app.post("/api/v1/projects")
        self.assertEqual(r.status_code, 501)

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
        time.sleep(1)  # wait a bit so that packager can finalize
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
        p = PM.new_packager({"callback_url": "https://test.local:8000/cb"})
        s = on_packaging_done(p)
        self.assertEqual(s, 200)

    def test_on_unpackaging_done(self):
        p = PM.new_packager({"callback_url": "https://test.local:8000/cb"})
        s = on_unpackaging_done(p)
        self.assertEqual(s, 200)
