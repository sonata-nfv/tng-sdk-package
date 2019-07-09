import unittest
import tempfile
import os
import tarfile
from tngsdk.package.tests.fixtures import misc_file
from tngsdk.package.packager import PM
from tngsdk.package.packager.packager import NapdRecord
from tngsdk.package.packager.exeptions import NoOSMFilesFound
from tngsdk.package.packager.osm_packager import OsmPackager, OsmPackagesSet,\
    OsmPackage
from tngsdk.package.cli import parse_args


class TngSdkPackageOSMPackager(unittest.TestCase):

    def setUp(self):
        self.tmp_files = []

    def reset_tmp_files(self):
        self.tmp_files = []

    def test_do_package(self):
        # prepare test
        project = misc_file("mixed-ns-project")
        output = tempfile.mkdtemp()
        args = parse_args(["--format", "eu.etsi.osm",
                           "-p", project,
                           "-o", output])
        p = PM.new_packager(args, pkg_format=args.pkg_format)

        # execute
        napdr = p._do_package()

        # checks
        self.assertIsNone(napdr.error)
        packages = os.listdir(output)
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
            with tarfile.open(os.path.join(output, package)) as f:
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

    def test_create_temp_dir(self):
        # prepare test
        args = parse_args(["--format", "eu.etsi.osm"])
        p = PM.new_packager(args, pkg_format=args.pkg_format)
        tmp_descriptor = tempfile.NamedTemporaryFile()
        kwargs = {
            "subdir_name": "name",
            "descriptor": tmp_descriptor.name,
            "hash": "hash_value",
            "folders": OsmPackager.folders_nsd,
            "project_path": "",
            "checks_filename": "checksums.txt"
        }

        # execute
        temp = p.create_temp_dir(**kwargs)

        # check results
        self.assertIsInstance(temp, str)  # got path
        self.assertTrue(os.path.exists(temp))  # created directory exists
        for folder in OsmPackager.folders_nsd+[tmp_descriptor.name]:
            # folders created ?
            self.assertTrue(os.path.exists(
                os.path.join(temp, folder)),
                msg=os.path.join(temp, folder)
            )
        # new descriptor file for next test
        tmp_descriptor.close()
        del tmp_descriptor
        tmp_descriptor = tempfile.NamedTemporaryFile()

        kwargs["descriptor"] = tmp_descriptor.name
        kwargs["folders"] = OsmPackager.folders_vnf  # vnf dir-tree this time

        # execute
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
        # prepare test
        args = parse_args(["--format", "eu.etsi.osm"])
        args.package = ""
        p = PM.new_packager(args, pkg_format=args.pkg_format)

        project_name = "test"
        tmp_descriptor = tempfile.NamedTemporaryFile()
        package_set = OsmPackagesSet(NapdRecord())
        # ns descriptor
        package_set.nsd = OsmPackage({
            "_project_source": tmp_descriptor.name,
            "hash": "hash_value",
            "filename": tmp_descriptor.name
        }, project_name=project_name, folders=OsmPackagesSet.folders_nsd)
        # 5 vnf descriptors
        vnf_num = 5
        tmps = [tempfile.NamedTemporaryFile() for i in range(vnf_num)]
        package_set.vnfds = {
            tmp_descriptor.name:
                OsmPackage({
                    "_project_source": tmp_descriptor.name,
                    "hash": "hash_value"+str(i),
                    "filename": tmp_descriptor.name
                }, project_name=project_name,
                    folders=OsmPackagesSet.folders_vnf)
            for i, tmp_descriptor in zip(range(vnf_num), tmps)}

        # execute
        p.create_temp_dirs(package_set, project_path="")

        # check if directories created
        for package in package_set.packages():
            self.assertTrue(os.path.exists(package.temp_dir),
                            msg=str(package))

    def _create_tmp_file(self):
        self.tmp_files.append(tempfile.NamedTemporaryFile())
        return self.tmp_files[-1].name

    def create_test_OsmPackage(self, project_name, folders):
        package = OsmPackage({"filename": self._create_tmp_file()},
                             project_name=project_name, folders=folders)
        package.temp_dir = tempfile.mkdtemp()
        package.package_content = []
        for i in range(12):
            name = self._create_tmp_file()
            package.package_content.append(
                {"source": folders[i % len(folders)],
                 "_project_source": name,
                 "filename": name,
                 "hash": "hash_value_{}".format(str(i))}
            )
        return package

    def create_test_OsmPackageSet(self, project_name):
        package_set = OsmPackagesSet(NapdRecord())
        package_set.nsd = self.create_test_OsmPackage(
            project_name, OsmPackagesSet.folders_nsd
        )
        package_set.vnfds = {
            "vnf{}".format(i):
                self.create_test_OsmPackage(
                    project_name, OsmPackagesSet.folders_vnf)
            for i in range(12)
        }
        return package_set

    def test_attach_files(self):
        args = parse_args(["--format", "eu.etsi.osm"])
        args.package = ""
        p = PM.new_packager(args, pkg_format=args.pkg_format)
        project_name = "project"

        self.reset_tmp_files()
        package_set = self.create_test_OsmPackageSet(project_name)

        p.attach_files(package_set)

        for package in package_set.packages():
            for file in package.package_content:
                self.assertTrue(
                    os.path.exists(os.path.join(
                        package.temp_dir, file["source"], file["filename"]
                    ))
                )

    def test_pack_packages(self):
        # prepare test
        args = parse_args(["--format", "eu.etsi.osm"])
        args.package = ""
        p = PM.new_packager(args, pkg_format=args.pkg_format)

        project_name = "project"
        wd = tempfile.mkdtemp()

        self.reset_tmp_files()
        package_set = self.create_test_OsmPackageSet(project_name)
        p.attach_files(package_set)

        p.pack_packages(wd, package_set)

        for package in package_set.packages():
            package_path = os.path.join(
                wd, "{}.tar.gz".format(package.package_name))
            self.assertTrue(os.path.exists(package_path),
                            msg=str((package_path, os.listdir(wd))))

        for vnf in package_set.vnfds.values():
            package_path = os.path.join(
                wd, "{}.tar.gz".format(vnf.package_name))
            with tarfile.open(package_path) as f:
                member_names = list(
                    map(lambda member: member.name, f.getmembers())
                )
                for i, folder in enumerate(OsmPackagesSet.folders_vnf):
                    member = os.path.join(vnf._subdir, folder)
                    self.assertIn(member, member_names)

                file_members = list(
                    map(lambda member: os.path.basename(member), member_names)
                )
                for file in vnf.package_content:
                    filename = os.path.basename(file["filename"])
                    self.assertIn(filename, file_members)

    def test_do_package_subfolder(self):
        # prepare test
        project = misc_file("mixed-ns-project-subfolder-test")
        output = tempfile.mkdtemp()
        args = parse_args(["--format", "eu.etsi.osm",
                           "-p", project,
                           "-o", output])
        p = PM.new_packager(args, pkg_format=args.pkg_format)

        # execute
        napdr = p._do_package()

        self.assertIsNone(napdr.error)

        packages = os.listdir(output)
        subfolder_files = os.listdir(os.path.join(project, "subfolder"))
        for package in packages:
            with tarfile.open(os.path.join(output, package)) as f:
                member_names = list(
                    map(lambda member: os.path.basename(member.name),
                        f.getmembers()))
                for file in subfolder_files:
                    self.assertIn(file, member_names)


class TngSdkPackageOSMPackageSet(unittest.TestCase):

    def test_sort_files(self):
        package_set = OsmPackagesSet(NapdRecord())
        package_set.project_name = "project"

        error_catched = False
        try:
            # execute
            package_set._sort_files()
        except NoOSMFilesFound:
            error_catched = True
        finally:
            # first test - should throw Exception without files
            self.assertTrue(error_catched)

        nsd = {"content-type": "application/vnd.osm.nsd", "tags": [],
               "filename": "nsd_file"}
        package_set.package_content.append(nsd)
        package_set._sort_files()
        self.assertIs(package_set.nsd.descriptor_file, nsd)
        vnfd = {"content-type": "application/vnd.osm.vnfd", "tags": [],
                "filename": "vnfd_file"}
        package_set.package_content.append(vnfd)
        package_set._sort_files()
        self.assertIs(package_set.nsd.descriptor_file, nsd)
        self.assertIn(vnfd["filename"], package_set.vnfds)
        self.assertIs(
            vnfd, package_set.vnfds[vnfd["filename"]].descriptor_file)
        package_set.package_content.pop(0)
        package_set._sort_files()
        self.assertIn(vnfd["filename"], package_set.vnfds)
        self.assertIs(
            vnfd, package_set.vnfds[vnfd["filename"]].descriptor_file)
        package_set.package_content.append(nsd)
        vnfd2 = {"content-type": "application/vnd.osm.vnfd", "tags": [],
                 "filename": "vnfd_file2"}
        package_set.package_content.append(vnfd2)
        files = [
            {"content-type": "text/plain", "tags": ["etsi.osm"],
             "filename": "file1"},
            {"content-type": "text/plain", "tags": [], "filename": "file2"},
            {"content-type": "text/plain", "tags": ["etsi.osm.ns"],
             "filename": "file3"},
            {"content-type": "text/plain", "tags": ["etsi.osm.vnf"],
             "filename": "file4"},
            {"content-type": "text/plain", "filename": "file5",
             "tags": ["etsi.osm.vnf.vnfd_file"]},
            {"content-type": "text/plain", "filename": "file6",
             "tags": ["etsi.osm.vnf.vnfd_file2"]},
            {"content-type": "text/plain", "filename": "file7",
             "tags": ["etsi.osm.vnf.vnfd_file2"]}]
        package_set.package_content.extend(files)
        package_set._sort_files()
        self.assertIs(package_set.nsd.descriptor_file, nsd)
        self.assertIn(vnfd["filename"], package_set.vnfds)
        self.assertIn(vnfd2["filename"], package_set.vnfds)
        self.assertIs(
            vnfd, package_set.vnfds[vnfd["filename"]].descriptor_file)
        self.assertIs(
            vnfd2, package_set.vnfds[vnfd2["filename"]].descriptor_file)
        for package in package_set.packages():
            self.assertIn(files[0], package.package_content)
        self.assertIn(files[2], package_set.nsd.package_content)
        for package in package_set.vnfds.values():
            self.assertIn(files[3], package.package_content)
        self.assertIn(files[4],
                      package_set.vnfds["vnfd_file"].package_content)
        self.assertIn(files[5],
                      package_set.vnfds["vnfd_file2"].package_content)
        self.assertIn(files[6],
                      package_set.vnfds["vnfd_file2"].package_content)
