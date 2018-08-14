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
import shutil
import os
import tngsdk.package as tngpkg


class TngSdkPackagePythonApiTest(unittest.TestCase):
    """
    Test case to check that the tool can be
    used from external Python code, e.g.,
    by directly calling its run method.
    """

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_pyapi_unpackage(self):
        tempdir = tempfile.mkdtemp()
        # set arguments using a list
        args = [
            "--unpackage", "misc/5gtango-ns-package-example.tgo",
            "--output", tempdir,
            "--store-backend", "TangoProjectFilesystemBackend"
        ]
        r = tngpkg.run(args)
        self.assertIsNone(r.error)
        self.assertTrue(os.path.exists(
            os.path.join(tempdir, "5gtango-ns-package-example/project.yml")))
        shutil.rmtree(tempdir)

    def test_pyapi_package_auto_name(self):
        # specify output dir. but not file name.
        pkg_path = tempfile.mkdtemp()
        args = [
            "--package", "misc/5gtango_ns_project_example1/",
            "--output", pkg_path
        ]
        r = tngpkg.run(args)
        self.assertIsNone(r.error)
        self.assertTrue(
            os.path.exists(pkg_path))
        shutil.rmtree(pkg_path)
