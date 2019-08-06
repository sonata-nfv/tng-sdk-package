import unittest
import tempfile
import os
import zipfile
import yaml
from tngsdk.package.tests.fixtures import misc_file
from tngsdk.package.packager import PM
from tngsdk.package.packager.packager import NapdRecord
from tngsdk.package.packager.onap_packager import OnapPackager, OnapPackage,\
    OnapPackageSet
from tngsdk.package.cli import parse_args


class TngSdkPackageOnapPackager(unittest.TestCase):

    def setUp(self):
        self.tmp_files = []

    def reset_tmp_files(self):
        self.tmp_files = []

    def substring_in_list(self, substr, L):
        for element in L:
            if substr in element:
                return True
        return False

    def test_do_package(self):
        # prepare test
        project = misc_file("mixed-ns-project")
        output = tempfile.mkdtemp()
        args = parse_args(["--format", "eu.lf.onap",
                           "-p", project,
                           "-o", output])
        p = PM.new_packager(args, pkg_format=args.pkg_format)

        # execute
        p._do_package()

        packages = os.listdir(output)
        self.assertEqual(len(packages), 2)
        for package in packages:
            self.assertEqual(os.path.splitext(package)[1], ".csar")
        self.assertTrue(self.substring_in_list("onap_nsd", packages),
                        msg="onap_nsd not as substr in {}".format(packages))
        self.assertTrue(self.substring_in_list("onap_vnfd", packages),
                        msg="onap_vnfd not as substr in {}".format(packages))

        with open(os.path.join(project, "project.yml")) as f:
            pd = yaml.load(f)
        files = pd["files"]
        files = [os.path.basename(file["path"]) for file in files
                 if "onap" in file["type"] or "lf.onap" in file["tags"]]
        nsd = None
        vnfd = None
        for file in files:
            if "nsd" in file:
                nsd = file
            if "vnfd" in file:
                vnfd = file
        files.remove(nsd)
        files.remove(vnfd)
        for package in packages:
            with zipfile.ZipFile(os.path.join(output, package)) as zf:
                names = zf.namelist()
                for file in files:
                    self.assertTrue(self.substring_in_list(file, names),
                                    msg="{} not in {}".format(file, names))
                if "nsd" in package:
                    self.assertIn(nsd, names)
                    self.assertIn(os.path.splitext(nsd)[0]+".mf", names)
                if "vnfd" in package:
                    self.assertIn(vnfd, names)
                    self.assertIn(os.path.splitext(vnfd)[0]+".mf", names)

                self.assertIn(os.path.join("TOSCA-Metadata", "TOSCA.meta"),
                              names)

    def test_pack_package_source_path(self):
        inputs = [{"tags": []},
                  {"tags": ["lf.onap"]},
                  {"tags": ["lf.onap", "onap-target:new"]},
                  {"tags": ["lf.onap", "onap-target:new/bla/here"]}]
        outputs = ["", "Artifacts", "new", "new/bla/here"]

        args = parse_args([])
        p = OnapPackager(args)

        for inp, out in zip(inputs, outputs):
            self.assertEqual(p._pack_package_source_path(inp), out)

    def _create_tmp_file(self):
        self.tmp_files.append(tempfile.NamedTemporaryFile())
        return self.tmp_files[-1].name

    def create_test_OnapPackage(self, project_name, folders):
        package = OnapPackage({"filename": self._create_tmp_file()},
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

    def create_test_OnapPackageSet(self, project_name):
        package_set = OnapPackageSet(NapdRecord())
        package_set.nsd = self.create_test_OnapPackage(
            project_name, OnapPackageSet.folders
        )
        package_set.vnfds = {
            "vnf{}".format(i):
                self.create_test_OnapPackage(
                    project_name, OnapPackageSet.folders)
            for i in range(12)
        }
        return package_set

    def test_pack_packages(self):
        # prepare test
        args = parse_args(["--format", "eu.lf.onap"])
        args.package = ""
        p = PM.new_packager(args, pkg_format=args.pkg_format)

        project_name = "project"
        wd = tempfile.mkdtemp()

        self.reset_tmp_files()
        package_set = self.create_test_OnapPackageSet(project_name)
        p.attach_files(package_set)

        p.pack_packages(wd, package_set)

        for package in package_set.packages():
            package_path = os.path.join(
                wd, "{}.csar".format(package.package_name))
            self.assertTrue(os.path.exists(package_path),
                            msg=str((package_path, os.listdir(wd))))

        for vnf in package_set.vnfds.values():
            package_path = os.path.join(
                wd, "{}.csar".format(vnf.package_name))
            with zipfile.ZipFile(package_path) as f:
                member_names = f.namelist()
                for folder in OnapPackageSet.folders:
                    self.assertTrue(
                        self.substring_in_list(folder, member_names))

                file_members = list(
                    map(lambda member: os.path.basename(member), member_names)
                )
                for file in vnf.package_content:
                    filename = os.path.basename(file["filename"])
                    self.assertIn(filename, file_members)

    def test_generate_tosca_generate_etsi_mf(self):
        args = parse_args([])
        p = OnapPackager(args)
        package = OnapPackage({"filename": "test_file",
                               "content-type": "application/vnd.onap.nsd",
                               "source": "testdir",
                               "algorithm": "SHA-256",
                               "hash": "value1"})
        for i in range(12):
            package.package_content.append(
                {"filename": "test_file_pc" + str(i),
                 "source": "testdir_pc" + str(i),
                 "algorithm": "SHA-256",
                 "hash": "value" + str(i)}
            )
        package_set = OnapPackageSet(NapdRecord())

        tosca = p.generate_tosca(package, package_set)
        self.assertEqual(tosca[0], {"TOSCA-Meta-Version": "1.0",
                                    "CSAR-Version": "1.0",
                                    "Created-By": None,
                                    "Entry-Definitions": "test_file"})
        etsi_mf = p.generate_etsi_mf(package, package_set)
        self.assertEqual(etsi_mf[0], {"ns_product_name": None,
                                      "ns_provider_id": None,
                                      "ns_package_version": None,
                                      "ns_release_date_time": None})

        package.descriptor_file["content-type"] = "application/vnd.onap.vnfd"
        etsi_mf = p.generate_etsi_mf(package, package_set)
        self.assertEqual(etsi_mf[0], {"vnf_product_name": None,
                                      "vnf_provider_id": None,
                                      "vnf_package_version": None,
                                      "vnf_release_date_time": None})

        package.descriptor_file["content-type"] = "application/vnd.onap.pnfd"
        etsi_mf = p.generate_etsi_mf(package, package_set)
        self.assertEqual(etsi_mf[0], {"pnfd_name": None,
                                      "pnfd_provider": None,
                                      "pnfd_archive_version": None,
                                      "pnfd_release_date_time": None})

        package.descriptor_file["content-type"] = "application/vnd.onap.nsd"
        maintainer = "maintainer"
        name = "name"
        vendor = "vendor"
        version = "1.1"
        release_date_time = "2018_08_01"
        package_set.maintainer = maintainer
        package_set.name = name
        package_set.vendor = vendor
        package_set.version = version
        package_set.release_date_time = release_date_time

        tosca = p.generate_tosca(package, package_set)
        self.assertEqual(tosca[0], {"TOSCA-Meta-Version": "1.0",
                                    "CSAR-Version": "1.0",
                                    "Created-By": maintainer,
                                    "Entry-Definitions": "test_file"})
        etsi_mf = p.generate_etsi_mf(package, package_set)
        self.assertEqual(etsi_mf[0], {"ns_product_name": name,
                                      "ns_provider_id": vendor,
                                      "ns_package_version": version,
                                      "ns_release_date_time":
                                          release_date_time})

        package.descriptor_file["content-type"] = "application/vnd.onap.vnfd"
        etsi_mf = p.generate_etsi_mf(package, package_set)
        self.assertEqual(etsi_mf[0], {"vnf_product_name": name,
                                      "vnf_provider_id": vendor,
                                      "vnf_package_version": version,
                                      "vnf_release_date_time":
                                          release_date_time})

        package.descriptor_file["content-type"] = "application/vnd.onap.pnfd"
        etsi_mf = p.generate_etsi_mf(package, package_set)
        self.assertEqual(etsi_mf[0], {"pnfd_name": name,
                                      "pnfd_provider": vendor,
                                      "pnfd_archive_version": version,
                                      "pnfd_release_date_time":
                                          release_date_time})
        for i, pc in enumerate(etsi_mf[2:]):
            self.assertEqual(pc, {"Source": "testdir_pc" + str(i) +
                                            "/test_file_pc" + str(i),
                                  "Algorithm": "SHA-256",
                                  "Hash": "value" + str(i)})
