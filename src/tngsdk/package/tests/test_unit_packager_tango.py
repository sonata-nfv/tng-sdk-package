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


ETSI_MF = """ns_product_name: ns-package-example-etsi
ns_provider_id: eu.5gtango
ns_package_version: 0.1
ns_release_date_time: 2009-01-01T10:01:02Z

Source: Definitions/mynsd.yaml
Algorithm: SHA-256
Hash: f3a6484ea45b1605a2142cf29066d57d84dbeb58fd7ae2e06b729bcaf19b1701

Source: Definitions/myvnfd.yaml
Algorithm: SHA-256
Hash: 3fefae6c2402f14a0ae4af8eeb5cd4d6e2c77d4ddcbdeb173c04de0e41a719f5

Source: Icons/upb_logo.png
Algorithm: SHA-256
Hash: 3598ce6f965b2481fe26316c06b30950c46ac7f8e7229f104aa78f579997668d

Source: Images/somecloudimage.ref
Algorithm: SHA-256
Hash: 4bb0d5728545737558a159e7bcdfa087baec5b0d7494ad175185f2b4a370c3f1

Source: Scripts/cloud.init
Algorithm: SHA-256
Hash: 45149c9a7fb7addd14809694f4671629577a169ccc6d217fc362a90c4510ce3e
"""  # noqa: E501


NAPD_YAML = """---
descriptor_schema: "https://raw.githubusercontent.com/sonata-nfv/tng-schema/master/package-specification/napd-schema.yml"

vendor: "eu.5gtango"
name: "ns-package-example-tango"
version: "0.2"
package_type: "application/vnd.5gtango.package.nsp"  # MIME type of package, e.g., nsp, vnfp, tdp, trp
maintainer: "Manuel Peuster, Paderborn University"
release_date_time: "2009-01-01T14:01:02-04:00"          # IETF RFC3339
description: "This is an example 5GTANGO network service package."
logo: "Icons/upb_logo.png"                           # (optional) path to logo file (PNG or JPEG)

package_content:
  - source: "Definitions/mynsd.yaml"
    algorithm: "SHA-256"
    hash: "f3a6484ea45b1605a2142cf29066d57d84dbeb58fd7ae2e06b729bcaf19b1701"
    content-type: "application/vnd.5gtango.nsd"
    tags:  # (optional)
      - "eu.5gtango"
  - source: "Definitions/myvnfd.yaml"
    algorithm: "SHA-256"
    hash: "3fefae6c2402f14a0ae4af8eeb5cd4d6e2c77d4ddcbdeb173c04de0e41a719f5"
    content-type: "application/vnd.5gtango.vnfd"
    tags:  # (optional)
      - "eu.5gtango"
  - source: "Icons/upb_logo.png"
    algorithm: "SHA-256"
    hash: "3598ce6f965b2481fe26316c06b30950c46ac7f8e7229f104aa78f579997668d"
    content-type: "image/png"
  - source: "Images/mycloudimage.ref"
    algorithm: "SHA-256"
    hash: "5dd49f783fc40107e538904772e96ce7d13d324d8973288ca4836f7c06d430e7"
    content-type: "application/vnd.5gtango.ref"
  - source: "Licenses/LICENSE"
    algorithm: "SHA-256"
    hash: "256114aa091db22bd799f756d4501a979e5235e3e02bc7319995d97a9ff43925"
    content-type: "text/plain"
  - source: "Scripts/cloud.init"
    algorithm: "SHA-256"
    hash: "45149c9a7fb7addd14809694f4671629577a169ccc6d217fc362a90c4510ce3e"
    content-type: "text/x-shellscript"
"""  # noqa: E501

NAPD_YAML_BAD = """---
descriptor_schema: "https://raw.githubusercontent.com/sonata-nfv/tng-schema/master/package-specification/napd-schema.yml"

vendor_bad: "eu.5gtango"
name: "ns-package-example"
version: "0.1"
package_type: "application/vnd.5gtango.package.nsp"  # MIME type of package, e.g., nsp, vnfp, tdp, trp
maintainer: "Manuel Peuster, Paderborn University"
release_date_time: "2009-01-01T14:01:02-04:00"          # IETF RFC3339
description: "This is an example 5GTANGO network service package."
logo: "Icons/upb_logo.png"                           # (optional) path to logo file (PNG or JPEG)
"""  # noqa: E501

NAPD_YAML_BAD_CHECKSUM = """---
descriptor_schema: "https://raw.githubusercontent.com/sonata-nfv/tng-schema/master/package-specification/napd-schema.yml"

vendor: "eu.5gtango"
name: "ns-package-example-tango"
version: "0.2"
package_type: "application/vnd.5gtango.package.nsp"  # MIME type of package, e.g., nsp, vnfp, tdp, trp
maintainer: "Manuel Peuster, Paderborn University"
release_date_time: "2009-01-01T14:01:02-04:00"          # IETF RFC3339
description: "This is an example 5GTANGO network service package."
logo: "Icons/upb_logo.png"                           # (optional) path to logo file (PNG or JPEG)

package_content:
  - source: "Definitions/mynsd.yaml"
    algorithm: "SHA-256"
    hash: "f3a6484ea45b1605a2142cf29066d57d84dbeb58fd7ae2e06b729bcaf19b1701"
    content-type: "application/vnd.5gtango.nsd"
    tags:  # (optional)
      - "eu.5gtango"
  - source: "Definitions/myvnfd.yaml"
    algorithm: "SHA-256"
    hash: "3fefae6c2402f14a0ae4af8eeb5cd4d6e2c77d4ddcbdeb173c04de0e41a719f5"
    content-type: "application/vnd.5gtango.vnfd"
    tags:  # (optional)
      - "eu.5gtango"
  - source: "Icons/upb_logo.png"
    algorithm: "SHA-256"
    hash: "3598ce6f965b2481fe26316c06b30950c46ac7f8e7229f104aa78f579997668d"
    content-type: "image/png"
  - source: "Images/mycloudimage.ref"
    algorithm: "SHA-256"
    hash: "5dd49f783fc40107e538904772e96ce7d13d324d8973288ca4836f7c06d430e7X"
    content-type: "application/vnd.5gtango.ref"
  - source: "Licenses/LICENSE"
    algorithm: "SHA-256"
    hash: "256114aa091db22bd799f756d4501a979e5235e3e02bc7319995d97a9ff43925"
    content-type: "text/plain"
  - source: "Scripts/cloud.init"
    algorithm: "SHA-256"
    hash: "45149c9a7fb7addd14809694f4671629577a169ccc6d217fc362a90c4510ce3e"
    content-type: "text/x-shellscript"
"""  # noqa: E501


class TngSdkPackageTangoPackagerTest(unittest.TestCase):

    def _create_wd(self,
                   tosca_meta_path="TOSCA-Metadata/TOSCA.meta",
                   etsi_mf_path="mynsd.mf",
                   napd_path="TOSCA-Metadata/NAPD.yaml",
                   tosca_meta_data=TOSCA_META,
                   etsi_mf_data=ETSI_MF,
                   napd_data=NAPD_YAML):
        """
        Creates temp. working directory.
        return: wd path
        """
        # create temp folder
        wd = tempfile.mkdtemp()
        # create folder structure
        os.mkdir(os.path.join(wd, "TOSCA-Metadata"))
        os.mkdir(os.path.join(wd, "Definitions"))
        os.mkdir(os.path.join(wd, "Icons"))
        os.mkdir(os.path.join(wd, "Images"))
        os.mkdir(os.path.join(wd, "Scripts"))
        os.mkdir(os.path.join(wd, "Licenses"))
        # write TOSCA-Metadata file
        if tosca_meta_path is not None:
            self._create_file(wd, tosca_meta_path, tosca_meta_data)
        # write ETSI manifest file
        if etsi_mf_path is not None:
            self._create_file(wd, etsi_mf_path, etsi_mf_data)
        # write NAPD
        if napd_path is not None:
            self._create_file(wd, napd_path, napd_data)
        # create additional files
        self._create_file(wd, "Definitions/mynsd.yaml", "mynsd")
        self._create_file(wd, "Definitions/myvnfd.yaml", "myvnfd")
        self._create_file(wd, "Icons/upb_logo.png", "logo")
        self._create_file(wd, "Images/somecloudimage.ref", "somecloudimage")
        self._create_file(wd, "Scripts/cloud.init", "cloudinit")
        self._create_file(wd, "Images/mycloudimage.ref", "mycloudimage")
        self._create_file(wd, "Licenses/LICENSE", "licsens")
        return wd

    def _create_file(self, wd, path, data):
        with open(os.path.join(wd, path), "w") as f:
                f.write(data)

    def findConentEntry(self, napdr, source):
        for c in napdr.package_content:
            if not isinstance(c, dict):
                return None
            if c.get("source") == source:
                return c
        self.assertIsNotNone(None,
                             msg="CE: {} not found.".format(source))
        return None

    def assertContentEntry(self, c, content_type=None):
        self.assertIsNotNone(c)
        self.assertTrue(isinstance(c, dict))
        self.assertIn("source", c)
        self.assertIn("algorithm", c)
        self.assertIn("hash", c)
        self.assertIn("content-type", c)
        if content_type is not None:
            self.assertEqual(c.get("content-type"), content_type)

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
        self.assertEqual(len(etsi_mf), 6)
        napd, npath = self.p._read_napd(wd, tosca_meta)
        self.assertIn("descriptor_schema", napd)

    def test_read_missing_metadata(self):
        # create malformed work environment
        wd = self._create_wd(None, None, None)
        # read metadata
        tosca_meta = self.p._read_tosca_meta(wd)
        self.assertEqual(tosca_meta, [{}])
        etsi_mf = self.p._read_etsi_manifest(wd, tosca_meta)
        self.assertEqual(etsi_mf, [{}])
        napd, npath = self.p._read_napd(wd, tosca_meta)
        self.assertNotIn("descriptor_schema", napd)

    def test_read_malformed_metadata(self):
        # create malformed work environment
        wd = self._create_wd(napd_data=NAPD_YAML_BAD)
        # read metadata
        tosca_meta = self.p._read_tosca_meta(wd)
        self.assertEqual(len(tosca_meta), 2)
        etsi_mf = self.p._read_etsi_manifest(wd, tosca_meta)
        self.assertEqual(len(etsi_mf), 6)
        msg = None
        try:
            self.p._read_napd(wd, tosca_meta)
        except BaseException as e:
            msg = str(e)
        self.assertIsNotNone(msg)
        self.assertIn("Validation of", msg)
        self.assertIn("failed", msg)

    def test_collect_metadata_csar(self):
        """
        Check NAPDR based on CSAR data.
        """
        # create environment
        wd = self._create_wd(etsi_mf_path=None,
                             napd_path=None)
        # collect available metadata
        napdr = self.p.collect_metadata(wd)
        # check packager assertion methods
        self.assertTrue(self.p._assert_usable_tango_package(napdr))
        # check content checksums
        self.p._validate_package_content_checksums(wd, napdr)
        # check collected metadata
        self.assertIsNotNone(napdr)
        self.assertEqual(napdr.vendor, "Manuel-Peuster-Paderborn-University")
        self.assertEqual(len(napdr.name), 8)
        self.assertEqual(napdr.version, "1.0")
        self.assertEqual(napdr.package_type, "application/vnd.tosca.package")
        self.assertEqual(napdr.maintainer,
                         "Manuel Peuster (Paderborn University)")
        self.assertEqual(len(napdr.release_date_time), 20)
        self.assertEqual(len(napdr.metadata), 3)

    def test_collect_metadata_etsi(self):
        """
        Check NAPDR based on CSAR and ETSI data.
        """
        # create environment
        wd = self._create_wd(napd_path=None)
        # collect available metadata
        napdr = self.p.collect_metadata(wd)
        # check packager assertion methods
        self.assertTrue(self.p._assert_usable_tango_package(napdr))
        # check content checksums
        self.p._validate_package_content_checksums(wd, napdr)
        # check collected metadata
        self.assertIsNotNone(napdr)
        self.assertEqual(napdr.vendor, "eu.5gtango")
        self.assertEqual(napdr.name, "ns-package-example-etsi")
        self.assertEqual(napdr.version, "0.1")
        self.assertEqual(napdr.package_type,
                         "application/vnd.etsi.package.nsp")
        self.assertEqual(napdr.maintainer,
                         "Manuel Peuster (Paderborn University)")
        self.assertEqual(len(napdr.release_date_time), 20)
        self.assertEqual(len(napdr.metadata), 3)
        self.assertEqual(len(napdr.package_content), 5)
        print(napdr.package_content)
        self.assertContentEntry(
            self.findConentEntry(napdr, "Definitions/mynsd.yaml"))
        self.assertContentEntry(
            self.findConentEntry(napdr, "Definitions/myvnfd.yaml"))
        self.assertContentEntry(
            self.findConentEntry(napdr, "Icons/upb_logo.png"))
        self.assertContentEntry(
            self.findConentEntry(napdr, "Images/somecloudimage.ref"))
        self.assertContentEntry(
            self.findConentEntry(napdr, "Scripts/cloud.init"))

    def test_collect_metadata_tango(self):
        """
        Check NAPDR based on CSAR, ETSI, and NAPD data.
        """
        # create environment
        wd = self._create_wd()
        # collect available metadata
        napdr = self.p.collect_metadata(wd)
        # check packager assertion methods
        self.assertTrue(self.p._assert_usable_tango_package(napdr))
        # check content checksums
        self.p._validate_package_content_checksums(wd, napdr)
        # check collected metadata
        self.assertIsNotNone(napdr)
        self.assertEqual(napdr.vendor, "eu.5gtango")
        self.assertEqual(napdr.name, "ns-package-example-tango")
        self.assertEqual(napdr.version, "0.2")
        self.assertEqual(napdr.package_type,
                         "application/vnd.5gtango.package.nsp")
        self.assertEqual(napdr.maintainer,
                         "Manuel Peuster, Paderborn University")
        self.assertEqual(len(napdr.release_date_time), 25)
        self.assertEqual(len(napdr.metadata), 3)
        self.assertEqual(len(napdr.package_content), 7)
        self.assertContentEntry(
            self.findConentEntry(napdr, "Definitions/mynsd.yaml"),
            content_type="application/vnd.5gtango.nsd")
        self.assertContentEntry(
            self.findConentEntry(napdr, "Definitions/myvnfd.yaml"),
            content_type="application/vnd.5gtango.vnfd")
        self.assertContentEntry(
            self.findConentEntry(napdr, "Icons/upb_logo.png"),
            content_type="image/png")
        self.assertContentEntry(
            self.findConentEntry(napdr, "Licenses/LICENSE"),
            content_type="text/plain")
        self.assertContentEntry(
            self.findConentEntry(napdr, "Images/somecloudimage.ref"),
            content_type=None)
        self.assertContentEntry(
            self.findConentEntry(napdr, "Images/mycloudimage.ref"),
            content_type="application/vnd.5gtango.ref")
        self.assertContentEntry(
            self.findConentEntry(napdr, "Scripts/cloud.init"),
            content_type="text/x-shellscript")

    def test_do_unpackage_good_package(self):
        wd = self._create_wd()
        r = self.p._do_unpackage(wd=wd)
        self.assertIsNone(r.error)

    def test_do_unpackage_bad_checksum(self):
        wd = self._create_wd(napd_data=NAPD_YAML_BAD_CHECKSUM)
        r = self.p._do_unpackage(wd=wd)
        self.assertIsNotNone(r.error)
        self.assertIn("Checksum mismatch!", r.error)

    def test_do_unpackage_bad_metadata(self):
        wd = self._create_wd(napd_data=NAPD_YAML_BAD)
        r = self.p._do_unpackage(wd=wd)
        self.assertIsNotNone(r.error)
        self.assertIn("failed", r.error)

    def test_do_unpackage_missing_file(self):
        wd = self._create_wd(tosca_meta_path=None)
        r = self.p._do_unpackage(wd=wd)
        self.assertIsNotNone(r.error)
        self.assertIn("Package metadata vailidation failed.", r.error)

    def test_do_package(self):
        pass
