import os
from hashlib import sha256
from tngsdk.package.logger import TangoLogger
from tngsdk.package.helper import creat_zip_file_from_directory,\
    write_block_based_meta_file, file_hash
from tngsdk.package.packager.exeptions import NoOnapFilesFound
from tngsdk.package.packager.osm_packager import OsmPackage, OsmPackagesSet, \
    OsmPackager

LOG = TangoLogger.getLogger(__name__)


class OnapPackage(OsmPackage):
    pass


class OnapPackageSet(OsmPackagesSet):
    folders = ["Artifacts", "TOSCA-Metadata"]

    def _sort_files(self, _type='onap', package_class=OnapPackage,
                    folders_nsd=folders, folders_vnf=folders,
                    no_files_exception=NoOnapFilesFound(
                        "No Onap-descriptor-files found in project")):

        super()._sort_files(_type=_type, package_class=package_class,
                            folders_nsd=folders_nsd, folders_vnf=folders_vnf,
                            no_files_exception=no_files_exception)


class OnapPackager(OsmPackager):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._store_checksums = False
        self.checksum_algorithm = "SHA-256"

    def file_hash(self, *args, **kwargs):
        """
        Returns hash value for a onap-file (SHA-256 Algorithm),
        by using helper.file_hash().
        Args:
            *args:
            **kwargs:

        Returns:
            hash value
        """
        return file_hash(h_func=sha256, *args, **kwargs)

    def _pack_package_source_path(self, f):
        if "lf.onap" in f.get("tags"):
            for tag in f.get("tags"):
                _tag = tag.split(":")
                if "onap-target" == _tag[0]:
                    return _tag[1]
            return "Artifacts"
        else:
            return ""

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

    def write_manifests(self, package_set, TOSCA_direc="TOSCA-Metadata",
                        tosca_filename="TOSCA.meta"):
        """
        Iterates over package_ser.packages() and writes TOSCA.meta and
        etsi_manifest using helper function write_block_based_meta_file.
        Args:
            package_set: of type OnapPackageSet
            TOSCA_direc:
            tosca_filename:

        Returns: None

        """
        for package in package_set.packages():

            etsi_mf_filename = os.path.splitext(
                package.descriptor_file["filename"])[0] + ".mf"
            path = os.path.join(package.temp_dir, etsi_mf_filename)
            mf_data = self.generate_etsi_mf(package, package_set)
            LOG.debug("Writing ETSI manifest to: {}".format(path))
            write_block_based_meta_file(mf_data, path)

            tosca_data = self.generate_tosca(package, package_set)
            path = os.path.join(package.temp_dir, TOSCA_direc, tosca_filename)
            LOG.debug("Writing TOSCA.meta to: {}".format(path))
            write_block_based_meta_file(tosca_data, path)

    def generate_tosca(self, package, package_set, tosca_meta_version="1.0",
                       csar_version="1.0"):
        """
        Returns tosca manifest as list of blocks for function
        write_block_based_meta_file.
        Args:
            package: of type OnapPackage
            package_set: of type OnapPackageSet
            tosca_meta_version:
            csar_version:

        Returns:
            list of dictionaries
        """
        tosca = {"TOSCA-Meta-Version": tosca_meta_version,
                 "CSAR-Version": csar_version,
                 "Created-By": package_set.maintainer,
                 "Entry-Definitions": package.descriptor_file["filename"]}
        return [tosca]

    def generate_etsi_mf(self, package, package_set):
        """
        Returns etsi manifest as list of blocks for function
        write_block_based_meta_file.
        Args:
            package: of type OnapPackage
            package_set: of type OnapPackageSet

        Returns:
            list of dictionaries
        """
        data = list()
        b0 = None
        if (package.descriptor_file["content-type"] ==
                "application/vnd.onap.nsd"):
            b0 = {"ns_product_name": package_set.name,
                  "ns_provider_id": package_set.vendor,
                  "ns_package_version": package_set.version,
                  "ns_release_date_time": package_set.release_date_time}
        elif (package.descriptor_file["content-type"] ==
              "application/vnd.onap.vnfd"):
            b0 = {"vnf_product_name": package_set.name,
                  "vnf_provider_id": package_set.vendor,
                  "vnf_package_version": package_set.version,
                  "vnf_release_date_time": package_set.release_date_time}
        elif (package.descriptor_file["content-type"] ==
              "application/vnd.onap.pnfd"):
            b0 = {"pnfd_name": package_set.name,
                  "pnfd_provider": package_set.vendor,
                  "pnfd_archive_version": package_set.version,
                  "pnfd_release_date_time": package_set.release_date_time}
        data.append(b0)
        data.append({"Source": os.path.join(
            package.descriptor_file.get("source"),
            package.descriptor_file.get("filename")),
                     "Algorithm": package.descriptor_file.get("algorithm"),
                     "Hash": package.descriptor_file.get("hash")})
        for pc in package.package_content:
            bN = {"Source": os.path.join(pc.get("source"), pc.get("filename")),
                  "Algorithm": pc.get("algorithm"),
                  "Hash": pc.get("hash")}
            data.append(bN)
        return data

    @OsmPackager._do_package_closure
    def _do_package(self, napdr, project_path=None, **kwargs):
        """
        Pack a 5GTANGO project to Onap packages.
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
        self.write_manifests(onap_package_set)
        # 7. create packages from temporary directories
        self.pack_packages(wd, onap_package_set)
        onap_package_set.metadata["_storage_location"] = wd
        return onap_package_set
