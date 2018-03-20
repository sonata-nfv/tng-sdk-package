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


TOSCA_META = """TOSCA-Meta-Version: 1.0
CSAR-Version: 1.0
Created-By: Manuel Peuster (Paderborn University)
Entry-Definitions: Definitions/mynsd.yaml
Entry-Manifest: mynsd.mf
Entry-Change-Log: ChangeLog.txt
Entry-Licenses: Licenses

Name: TOSCA-Metadata/NAPD.yaml
Content-Type: application/vnd.5gtango.napd
"""  # noqa: E501


ETSI_MF = """ns_product_name: ns-package-example
ns_provider_id: eu.5gtango
ns_package_version: 0.1
ns_release_date_time: 2018.01.01T10:00+03:00

Source: Definitions/mynsd.yaml
Algorithm: SHA-256
Hash: feb97301a80166c076cf0d639a4c0f13a93f87585496a054bf3dd61f6a9a6f02

Source: Definitions/myvnfd.yaml
Algorithm: SHA-256
Hash: a8ecb3b378c5d4c40f8a8d8afb1870e6119231f10fab3e7c6e1dd96c38b87d93

Source: Icons/upb_logo.png
Algorithm: SHA-256
Hash: dd83757e632740f9f390af15eeb8bc25480a0c412c7ea9ac9abbb0e5e025e508

Source: Images/mycloudinamge.ref
Algorithm: SHA-256
Hash: 54cb482d72b9f454aec9197c91310273f1406ed7b62c938ebe1cf1c271b7f522

Source: Licenses/LICENSE
Algorithm: SHA-256
Hash: 179f180ea1630016d585ff32321037b18972d389be0518c0192021286c4898ca

Source: Scripts/cloud.init
Algorithm: SHA-256
Hash: e16360cc3518bde752ac2d506e6bdb6bcb6638a0f94df9ea06975ae910204277
"""  # noqa: E501


NAPD_YAML = """---
descriptor_schema: "https://raw.githubusercontent.com/sonata-nfv/tng-schema/master/package-specification/napd-schema.yml"

vendor: "eu.5gtango"
name: "ns-package-example"
version: "0.1"
package_type: "application/vnd.5gtango.package.nsp"  # MIME type of package, e.g., nsp, vnfp, tdp, trp
maintainer: "Manuel Peuster, Paderborn University"
release_date_time: "2018.01.01T10:00+03:00"          # IETF RFC3339
description: "This is an example 5GTANGO network service package."
logo: "Icons/upb_logo.png"                           # (optional) path to logo file (PNG or JPEG)

package_content:
  - source: "Definitions/mynsd.yaml"
    algorithm: "SHA-256"
    hash: "feb97301a80166c076cf0d639a4c0f13a93f87585496a054bf3dd61f6a9a6f02"
    content-type: "application/vnd.5gtango.nsd"
    tags:  # (optional)
      - "eu.5gtango"
  - source: "Definitions/myvnfd.yaml"
    algorithm: "SHA-256"
    hash: "a8ecb3b378c5d4c40f8a8d8afb1870e6119231f10fab3e7c6e1dd96c38b87d93"
    content-type: "application/vnd.5gtango.vnfd"
    tags:  # (optional)
      - "eu.5gtango"
  - source: "Icons/upb_logo.png"
    algorithm: "SHA-256"
    hash: "dd83757e632740f9f390af15eeb8bc25480a0c412c7ea9ac9abbb0e5e025e508"
    content-type: "image/png"
  - source: "Images/mycloudimage.ref"
    algorithm: "SHA-256"
    hash: "54cb482d72b9f454aec9197c91310273f1406ed7b62c938ebe1cf1c271b7f522"
    content-type: "application/vnd.5gtango.ref"
  - source: "Licenses/LICENSE"
    algorithm: "SHA-256"
    hash: "179f180ea1630016d585ff32321037b18972d389be0518c0192021286c4898ca"
    content-type: "text/plain"
  - source: "Scripts/cloud.init"
    algorithm: "SHA-256"
    hash: "e16360cc3518bde752ac2d506e6bdb6bcb6638a0f94df9ea06975ae910204277"
    content-type: "text/x-shellscript"
"""  # noqa: E501


class TngSdkPackageTangoPackagerTest(unittest.TestCase):

    def _create_wd(self,
                   tosca_meta_path="TOSCA-Metadata/TOSCA.meta",
                   etsi_mf_path="mynsd.mf",
                   napd_path="TOSCA-Metadata/NAPD.yaml"):
        """
        Creates temp. working directory.
        return: wd path
        """
        # create temp folder
        wd = tempfile.mkdtemp()
        # create folder structure
        os.mkdir(os.path.join(wd, "TOSCA-Metadata"))
        os.mkdir(os.path.join(wd, "Definitions"))
        # write TOSCA-Metadata file
        if tosca_meta_path is not None:
            with open(os.path.join(wd, tosca_meta_path), "w") as f:
                f.write(TOSCA_META)
        # write ETSI manifest file
        if etsi_mf_path is not None:
            with open(os.path.join(wd, etsi_mf_path), "w") as f:
                f.write(ETSI_MF)
        # write NAPD
        if napd_path is not None:
            with open(os.path.join(wd, napd_path), "w") as f:
                f.write(NAPD_YAML)
        return wd

    def setUp(self):
        # list can manually define CLI arguments
        self.default_args = parse_args([])
        self.p = PM.new_packager(self.default_args, pkg_format="eu.5gtango")
        self.assertIn("TangoPackager", str(type(self.p)))

    def tearDown(self):
        pass

    def test_read_correct_metadata(self):
        # create correct work environment
        wd = self._create_wd()
        # read metadata
        tosca_meta = self.p._read_tosca_meta(wd)
        self.assertEqual(len(tosca_meta), 2)
        etsi_mf = self.p._read_etsi_manifest(wd, tosca_meta)
        self.assertEqual(len(etsi_mf), 7)
        # TODO napd = self.p._read_napd(wd)

    def test_read_missing_metadata(self):
        # create malformed work environment
        wd = self._create_wd(None, None, None)
        # read metadata
        tosca_meta = self.p._read_tosca_meta(wd)
        self.assertEqual(tosca_meta, [{}])
        etsi_mf = self.p._read_etsi_manifest(wd, tosca_meta)
        self.assertEqual(etsi_mf, [{}])
        # TODO napd = self.p._read_napd(wd)

    def test_collect_metadata(self):
        pass

    def test_do_unpackage(self):
        pass

    def test_do_package(self):
        pass
