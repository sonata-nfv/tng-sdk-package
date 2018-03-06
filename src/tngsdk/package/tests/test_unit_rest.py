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
from tngsdk.package.rest import app


class TngSdkRestTest(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

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
                                   "rb"),
                              "5gtango-ns-package-example.tgo")})
        self.assertEqual(r.status_code, 200)
        rd = json.loads(r.get_data(as_text=True))
        self.assertIn("package_process_uuid", rd)
