import unittest
import tempfile
import os
import tarfile
from tngsdk.package.tests.fixtures import misc_file
from tngsdk.package.packager import PM
from tngsdk.package.packager.packager import NapdRecord
from tngsdk.package.packager.exeptions import NoOSMFilesFound
from tngsdk.package.packager.osm_packager import OsmPackager
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

    def test_sort_files(self):
        args = parse_args(["--format", "eu.etsi.osm"])
        p = PM.new_packager(args, pkg_format=args.pkg_format)
        p.project_name = "project"
        napdr = NapdRecord()
        error_catched = False
        try:
            napdr = p._sort_files(napdr)
        except NoOSMFilesFound:
            error_catched = True
        finally:
            self.assertTrue(error_catched)
        nsd = {"content-type": "application/vnd.osm.nsd", "tags": []}
        napdr.package_content.append(nsd)
        p._sort_files(napdr)
        self.assertIs(p.nsd, nsd)
        vnfd = {"content-type": "application/vnd.osm.vnfd", "tags": []}
        napdr.package_content.append(vnfd)
        p._sort_files(napdr)
        self.assertIs(p.nsd, nsd)
        self.assertIn(vnfd, p.vnfds)
        napdr.package_content.pop(0)
        p._sort_files(napdr)
        self.assertIn(vnfd, p.vnfds)
        self.assertIsNone(p.nsd)
        napdr.package_content.append(nsd)
        files = [
            {"content-type": "text/plain", "tags": ["etsi.osm"]},
            {"content-type": "text/plain", "tags": []},
            {"content-type": "text/plain", "tags": ["etsi.osm.ns"]},
            {"content-type": "text/plain", "tags": ["etsi.osm.vnf"]},
            {"content-type": "text/plain", "tags": ["etsi.osm.vnf.name"]},
            {"content-type": "text/plain", "tags": ["etsi.osm.vnf.name2"]}]
        napdr.package_content.extend(files)
        p._sort_files(napdr)
        self.assertIs(p.nsd, nsd)
        self.assertIn(vnfd, p.vnfds)
        self.assertIn(files[0], p.general_files)
        self.assertIn(files[2], p.ns_files)
        self.assertIn(files[3], p.vnf_files)
        self.assertIn((p.project_name+"_name", files[4]), p.unique_files)
        self.assertIn((p.project_name+"_name2", files[5]), p.unique_files)

    def test_create_temp_dir(self):
        args = parse_args(["--format", "eu.etsi.osm"])
        p = PM.new_packager(args, pkg_format=args.pkg_format)
        tmp_descriptor = tempfile.NamedTemporaryFile()
        p.args.package = ""
        kwargs = {
            "subdir_name": "name",
            "descriptor": tmp_descriptor.name,
            "hash": "hash_value",
            "folders": OsmPackager.folders_nsd,
            "checks_filename": "checksums.txt"
        }

        temp = p.create_temp_dir(**kwargs)
        self.assertIsInstance(temp, str)
        self.assertTrue(os.path.exists(temp))
        for folder in OsmPackager.folders_nsd+[tmp_descriptor.name]:
            self.assertTrue(os.path.exists(
                os.path.join(temp, folder)),
                msg=os.path.join(temp, folder)
            )
        tmp_descriptor.close()
        del tmp_descriptor
        tmp_descriptor = tempfile.NamedTemporaryFile()

        kwargs["descriptor"] = tmp_descriptor.name
        kwargs["folders"] = OsmPackager.folders_vnf

        temp = p.create_temp_dir(**kwargs)
        self.assertIsInstance(temp, str)
        self.assertTrue(os.path.exists(temp))
        for folder in OsmPackager.folders_vnf+[tmp_descriptor.name]:
            self.assertTrue(os.path.exists(
                os.path.join(temp, folder)),
                msg=os.path.join(temp, folder)
            )

        tmp_descriptor.close()
        del tmp_descriptor

    def test_create_temp_dirs(self):
        args = parse_args(["--format", "eu.etsi.osm"])
        args.package = ""
        p = PM.new_packager(args, pkg_format=args.pkg_format)
        tmp_descriptor = tempfile.NamedTemporaryFile()
        p.nsd = {
            "_project_source": tmp_descriptor.name,
            "hash": "hash_value",
            "filename": tmp_descriptor.name
        }
        vnf_num = 5
        tmps = [tempfile.NamedTemporaryFile() for i in range(vnf_num)]
        p.vnfds = [{
            "_project_source": tmp_descriptor.name,
            "hash": "hash_value"+str(i),
            "filename": tmp_descriptor.name
        } for i, tmp_descriptor in zip(range(vnf_num), tmps)]
        p.create_temp_dirs("project_name2")
        self.assertTrue(os.path.exists(p.ns_temp_dir), msg=str(p.ns_temp_dir))
        for tmp in p.vnf_temp_dirs.values():
            self.assertTrue(os.path.exists(tmp), msg=str(tmp))

    def test_attach_files(self):
        args = parse_args(["--format", "eu.etsi.osm"])
        args.package = ""
        p = PM.new_packager(args, pkg_format=args.pkg_format)
        p.project_name = "project"

        p.ns_temp_dir = tempfile.mkdtemp()
        p.vnf_temp_dirs = {}
        for i in range(5):
            p.vnf_temp_dirs["vnf"+str(i)] = tempfile.mkdtemp()

        tmp_general_files = [tempfile.NamedTemporaryFile() for i in range(12)]
        tmp_ns_files = [tempfile.NamedTemporaryFile() for i in range(12)]
        tmp_vnf_files = [tempfile.NamedTemporaryFile() for i in range(12)]
        tmp_unique_files = [tempfile.NamedTemporaryFile() for i in range(3)]

        p.general_files = [
            {"source": "/folder" + str(i),
             "hash": "hash_value" + str(i),
             "_project_source": tmp.name,
             "filename": tmp.name} for i, tmp in enumerate(tmp_general_files)
        ]
        p.ns_files = [
            {"source": "/folder" + str(i),
             "hash": "hash_value" + str(i),
             "_project_source": tmp.name,
             "filename": tmp.name} for i, tmp in enumerate(tmp_ns_files)]

        p.vnf_files = [
            {"source": "/folder" + str(i),
             "hash": "hash_value" + str(i),
             "_project_source": tmp.name,
             "filename": tmp.name} for i, tmp in enumerate(tmp_vnf_files)]
        p.unique_files = []
        vnf_with_unique = []
        for vnf_name, tupl in zip(p.vnf_temp_dirs.keys(),
                                  enumerate(tmp_unique_files)):
            p.unique_files.append(
                (vnf_name,
                 {"source": "/folder" + str(tupl[0]),
                  "hash": "hash_value" + str(tupl[0]),
                  "_project_source": tupl[1].name,
                  "filename": tupl[1].name})
            )
            vnf_with_unique.append(vnf_name)

        p.attach_files()

        for i, file in enumerate(p.ns_files):
            self.assertTrue(
                os.path.exists(os.path.join(
                    p.ns_temp_dir, "folder"+str(i), file["filename"])
                )
            )
        for i, file in enumerate(p.general_files):
            self.assertTrue(
                os.path.exists(
                    os.path.join(
                        p.ns_temp_dir, "folder"+str(i), file["filename"]
                    )
                )
            )
            for tmp_dir in p.vnf_temp_dirs.values():
                self.assertTrue(
                    os.path.exists(
                        os.path.join(
                            tmp_dir, "folder" + str(i), file["filename"]
                        )
                    )
                )
        for i, file in enumerate(p.vnf_files):
            for tmp_dir in p.vnf_temp_dirs.values():
                self.assertTrue(
                    os.path.exists(
                        os.path.join(
                            tmp_dir, "folder" + str(i), file["filename"]
                        )
                    )
                )
        for i, tupl in enumerate(p.unique_files):
            self.assertTrue(
                os.path.exists(
                    os.path.join(
                        p.vnf_temp_dirs[tupl[0]],
                        "folder"+str(i),
                        tupl[1]["filename"]
                    )
                )
            )

    def test_create_packages(self):
        args = parse_args(["--format", "eu.etsi.osm"])
        args.package = ""
        p = PM.new_packager(args, pkg_format=args.pkg_format)
        p.project_name = "project"
        wd = tempfile.mkdtemp()
        p.ns_temp_dir = tempfile.mkdtemp()
        p.vnf_temp_dirs = {
            "vnf_tmp"+str(i): tempfile.mkdtemp() for i in range(12)
        }
        tmp = tempfile.NamedTemporaryFile(dir=p.ns_temp_dir)
        ns_test_subdir = tempfile.mkdtemp(dir=p.ns_temp_dir)
        vnf_test_files = {}
        vnf_test_subdirs = {}
        for key, vnf in p.vnf_temp_dirs.items():
            vnf_test_files[key] = tempfile.NamedTemporaryFile(dir=vnf)
            vnf_test_subdirs[key] = tempfile.mkdtemp(dir=vnf)

        p.create_packages(wd)

        ns_package_name = os.path.basename(p.ns_temp_dir.strip(os.sep))
        ns_package_path = os.path.join(wd,
                                       "{}.tar.gz".format(ns_package_name))
        self.assertTrue(
            os.path.exists(ns_package_path)
        )
        vnf_packages = {}
        for key, vnf in p.vnf_temp_dirs.items():
            package_path = os.path.join(wd, "{}.tar.gz".format(key))
            vnf_packages[key] = package_path
            self.assertTrue(
                os.path.exists(package_path),
                msg=str((wd, os.listdir(wd), package_path))
            )

        with tarfile.open(ns_package_path) as f:
            member_names = list(
                map(lambda member: member.name, f.getmembers())
            )
            tmp_name = tmp.name.strip(os.sep)
            tmp_name = os.sep.join(tmp_name.split(os.sep)[1:])
            self.assertIn(tmp_name, member_names)
            _ns_test_subdir = ns_test_subdir.strip(os.sep)
            _ns_test_subdir = os.sep.join(_ns_test_subdir.split(os.sep)[1:])
            self.assertIn(_ns_test_subdir, member_names)

        for key, vnf in vnf_packages.items():
            with tarfile.open(vnf) as f:
                member_names = list(
                    map(lambda member: member.name, f.getmembers())
                )
                member = os.path.basename(vnf_test_files[key].name)
                member = os.path.join(key, member)
                self.assertIn(member, member_names)
                member = os.path.basename(vnf_test_subdirs[key])
                member = os.path.join(key, member)
                self.assertIn(member, member_names)
