import unittest
import tempfile
import os
import yaml
import tarfile
from tngsdk.package.tests.fixtures import misc_file
from tngsdk.package.packager import PM
from tngsdk.package.cli import parse_args


class TngSdkPackageOSM(unittest.TestCase):

    def test_do_package(self):
        project = misc_file("mixed-ns-project")
        output = tempfile.mkdtemp()
        args = parse_args(["--format", "eu.etsi.osm",
                           "-p", project,
                           "-o", output])
        p = PM.new_packager(args, pkg_format=args.pkg_format)
        napdr = p._do_package()
        self.assertIsNone(napdr.error)
        packages = os.listdir(napdr._project_wd)
        self.assertTrue(
            all([os.path.exists(os.path.join(napdr._project_wd, package))
                 for package in packages]))
        basename = os.path.basename(output)
        basename_ns = "_".join([basename, "osm_nsd"])
        basename_vnf = "_".join([basename, "osm_vnfd"])
        filename_ns = basename_ns + ".tar.gz"
        filename_vnf = basename_vnf + ".tar.gz"
        self.assertIn(filename_ns, packages)
        self.assertIn(filename_vnf, packages)
        ns = ["osm_nsd.yaml",
              "checksums.txt",
              "icons/upb_logo.png",
              "vnf_config",
              "scripts",
              "ns_config",
              "icons"]
        vnf = ["osm_vnfd.yaml",
               "checksums.txt",
               "scripts",
               "images",
               "icons",
               "cloud_init",
               "charms",
               "icons/upb_logo.png",
               "cloud_init/cloud.init",
               "images/mycloudimage.ref"]
        for package in packages:
            with tarfile.open(os.path.join(napdr._project_wd, package)) as f:
                member_names = list(
                    map(lambda member: member.name, f.getmembers()))
                if "ns" in package:
                    for member in ns:
                        self.assertIn(os.path.join(basename_ns, member),
                                      member_names)
                elif "vnf" in package:
                    for member in vnf:
                        self.assertIn(os.path.join(basename_vnf, member),
                                      member_names)
