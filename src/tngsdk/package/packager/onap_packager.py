import tempfile
import os
import zipfile
import yaml
from tngsdk.package.helper import creat_zip_file_from_directory
from tngsdk.package.packager.packager import EtsiPackager, NapdRecord
from tngsdk.package.packager.tango_packager import TangoPackager
from tngsdk.package.packager.osm_packager import OsmPackage, OsmPackagesSet, \
    OsmPackager


class OnapPackage(OsmPackage):
    pass


class OnapPackageSet(OsmPackagesSet):
    folders = ["Artifacts", "TOSCA-Metadata"]

    def _sort_files(self, _type='onap', package_class=OnapPackage,
                            folders_nsd=folders, folders_vnf=folders):

        super()._sort_files(_type=_type, package_class=package_class,
                            folders_nsd=folders_nsd, folders_vnf=folders_vnf)


class OnapPackager(OsmPackager):

    def pack_packages(self, wd, package_set):
        """
        Creates .csar archives.
        Args:
            wd: path where to create archives
            package_set: of type OsmPackageSet

        Returns:
            None
        """
        for package in package_set.packages():
            package_path = (
                os.path.join(wd, "{}.csar".format(package.package_name)))
            creat_zip_file_from_directory(package.temp_dir, package_path)

    def write_tosca_metadata(self, package_set, direc="TOSCA-Metadata",
                             tosca_filename="TOSCA.meta"):
        for package in package_set.packages():
            with open(os.path.join(package.temp_dir,
                                   direc, tosca_filename), "w") as f:
                yaml.dump(self.generate_tosca(package, package_set), f,
                          default_flow_style=False)

    def generate_tosca(self, package, package_set):
        tosca = {"TOSCA-Meta-Version": "1.0",
                 "CSAR-Version": "1.0",
                 "Created-By": package_set.maintainer,
                 "Entry-Definitions": package.descriptor_file["filename"]}
        return tosca

    @OsmPackager._do_package_closure
    def _do_package(self, napdr, project_path=None, **kwargs):
        """
        Pack a 5GTANGO project to OSM packages.
        """
        onap_package_set = OnapPackageSet(napdr)
        wd = self.args.output
        if wd is None:
            wd = "{}.{}.{}".format(napdr.vendor,
                                   napdr.name,
                                   napdr.version)
        if not os.path.exists(wd):
            os.makedirs(wd)

        onap_package_set.project_name = os.path.basename(wd)

        onap_package_set._project_wd = wd
        onap_package_set._sort_files()
        # 5. creating temporary directories and copy descriptors
        self.create_temp_dirs(onap_package_set, project_path)
        # 6. copy files
        self.attach_files(onap_package_set, project_path)
        self.write_tosca_metadata(onap_package_set)
        # 7. create packages from temporary directories
        self.pack_packages(wd, onap_package_set)
        onap_package_set.__dict__.update(napdr.__dict__)
        return onap_package_set


def write_block_based_meta_file(data, path):
    """
    Writes TOSCA/ETSI block-based meta files.
    data = [block0_dict, ....blockN_dict]
    """
    with open(path, "w") as f:
        for block in data:
            if block is None:
                continue
            for k, v in block.items():
                f.write("{}: {}\n".format(k, v))
            f.write("\n")  # block separator
