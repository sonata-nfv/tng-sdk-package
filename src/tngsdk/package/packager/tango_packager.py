import os
import tempfile
import shutil
import yaml
import zipfile
import time
import pyrfc3339
from tngsdk.package.validator import validate_project_with_external_validator, validate_yaml_online
from tngsdk.package.packager.packager import EtsiPackager, NapdRecord
from tngsdk.package.packager.exeptions import MetadataValidationException,\
    NapdNotValidException,\
    ChecksumException,\
    MissingFileException
from tngsdk.package.helper import search_for_file, extract_zip_file_to_temp
from tngsdk.package.storage.tngprj import TangoProjectFilesystemBackend
from tngsdk.package.logger import TangoLogger

LOG = TangoLogger.getLogger(__name__)


class TangoPackager(EtsiPackager):

    def collect_metadata(self, wd):
        nr = super().collect_metadata(wd)
        LOG.debug("Collecting 5GTANGO (NAPD) meta data ...")
        napd, napd_path = self._read_napd(
            wd, nr.metadata.get("tosca"))
        # update NR with NAPD data
        return self._update_nr_with_napd(napd, napd_path, nr)

    def _update_nr_with_napd(self, napd, napd_path, nr=None):
        """
        Updates NR with data from NAPD file input.
        """
        if nr is None:
            nr = NapdRecord()
        nr.update(napd)
        nr.metadata["_napd_path"] = napd_path
        return nr

    def _read_napd(self, wd, tosca_meta):
        """
        Tries to read NAPD file and optionally validates it
        against its online schema.
        - try 1: Use block_1 from TOSCA.meta to find NAPD
        - try 2: Look for **/NAPD.yaml
        Returns valid NAPD schema formatted dict. and NAPD path
        """
        try:
            path = None
            if (tosca_meta is not None
                    and len(tosca_meta) > 1):
                # try 1:
                path = search_for_file(
                    os.path.join(wd, tosca_meta[1].get("Name")))
                if path is None:
                    LOG.warning("TOSCA block_1 file '{}' not found.".format(
                        tosca_meta[1].get("Name")))
                    # try 2:
                    path = search_for_file(
                        os.path.join(wd, "**/NAPD.yaml"), recursive=False)
            if path is None:
                LOG.warning("Couldn't find NAPD file: {}".format(wd))
                return dict(), None  # TODO return an empty NAPD skeleton here
            with open(path, "r") as f:
                data = yaml.load(f)
                if self.args.offline:
                    LOG.warning("Skipping NAPD validation (--offline)")
                else:
                    if not validate_yaml_online(data):
                        raise NapdNotValidException(
                            "Validation of {} failed.".format(path))
                return data, path
        except NapdNotValidException as e:
            LOG.error("Validation error: {}".format(e))
            raise e
        except BaseException as e:
            LOG.error("Cannot read NAPD.yaml file: {}".format(e))
            # raise e
        return dict(), None  # TODO return an empty NAPD skeleton here

    def _assert_usable_tango_package(self, napdr):
        """
        Assert that we have read enough information to have
        a 'usable' 5GTANGO package at hand.
        Where 'usable' means that the minimum set of fields
        is available to let any 5GTANGO component work with the package
        contents.
        Contains hard-coded checks that might evolve over time.
        raises MetadataValidationException
        """
        try:
            # check for empty fields
            assert(napdr.vendor is not None)
            assert(napdr.name is not None)
            assert(napdr.version is not None)
            assert(napdr.package_type is not None)
            assert(napdr.maintainer is not None)
            assert(napdr.release_date_time is not None)
            assert(len(napdr.metadata) > 0)
            # check if date strings can be parsed
            pyrfc3339.parse(napdr.release_date_time)
            # TODO extend as needed
            return True
        except AssertionError as e:
            m = "Package metadata vailidation failed. Package unusable. Abort."
            LOG.exception(m)
            del e
            raise MetadataValidationException(m)
        return False

    def _pack_create_package_directory_tree(self, napdr):
        """
        Generates directory tree in given working dir.
        5GTANGO package format specific.
        """
        def makedirs(p):
            if not os.path.exists(p):
                LOG.debug("Creating: {}".format(p))
                os.makedirs(p)

        wd = napdr._project_wd
        # TOSCA-Metadata directory
        makedirs(os.path.join(wd, "TOSCA-Metadata"))
        # Definitions directory
        makedirs(os.path.join(wd, "Definitions"))
        # Custom directories based on user project
        for pc in napdr.package_content:
            makedirs(os.path.join(
                wd, os.path.dirname(pc.get("source"))))

    def _pack_copy_files_to_package_directory_tree(self, pp, napdr):
        """
        Copy files from project to package wd.
        Improvement: Maybe we could speed this up with symbolic links?
        """
        wd = napdr._project_wd
        for pc in napdr.package_content:
            s = os.path.join(pp, pc.get("_project_source"))
            d = os.path.join(wd, pc.get("source"))
            LOG.debug("Copying {}\n\t to {}".format(s, d))
            shutil.copyfile(s, d)

    def _pack_write_napd(self, napdr, name="TOSCA-Metadata/NAPD.yaml"):
        wd = napdr._project_wd
        data = napdr.to_clean_dict()
        path = os.path.join(wd, name)
        # validate
        if self.args.offline:
            LOG.warning("Skipping NAPD validation (--offline)")
        else:
            if not validate_yaml_online(data):
                raise NapdNotValidException(
                    "NAPD validation failed. See logs for details.")
        LOG.debug("Writing NAPD to: {}".format(path))
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
        return name

    def _pack_gen_write_etsi_manifest(self, napdr, name="etsi_manifest.mf"):
        # TODO fix ETSI manifest naming
        wd = napdr._project_wd
        # collect data for manifest block file
        data = list()
        b0 = None
        if napdr.package_type == "application/vnd.5gtango.package.nsp":
            b0 = {"ns_product_name": napdr.name,
                  "ns_provider_id": napdr.vendor,
                  "ns_package_version": napdr.version,
                  "ns_release_date_time": napdr.release_date_time}
        elif napdr.package_type == "application/vnd.5gtango.package.vnfp":
            b0 = {"vnf_product_name": napdr.name,
                  "vnf_provider_id": napdr.vendor,
                  "vnf_package_version": napdr.version,
                  "vnf_release_date_time": napdr.release_date_time}
        elif napdr.package_type == "application/vnd.5gtango.package.tstp":
            b0 = {"tst_product_name": napdr.name,
                  "tst_provider_id": napdr.vendor,
                  "tst_package_version": napdr.version,
                  "tst_release_date_time": napdr.release_date_time}
        data.append(b0)
        for pc in napdr.package_content:
            bN = {"Source": pc.get("source"),
                  "Algorithm": pc.get("algorithm"),
                  "Hash": pc.get("hash")}
            data.append(bN)
        # write file
        path = os.path.join(wd, name)
        LOG.debug("Writing ETSI manifest to: {}".format(path))
        write_block_based_meta_file(data, path)
        return name

    def _pack_gen_write_tosca_manifest(
            self, napdr, napd_path, etsi_mf_path,
            name="TOSCA-Metadata/TOSCA.meta"):
        wd = napdr._project_wd
        # collect data for manifest block file
        data = list()
        b0 = None
        b0 = {"TOSCA-Meta-Version": "1.0",
              "CSAR-Version": "1.0",
              "Created-By": napdr.maintainer,
              "Entry-Manifest": etsi_mf_path,
              "Entry-Definitions": "TODO"}
        data.append(b0)
        b1 = {"Name": napd_path,
              "Content-Type": "application/vnd.5gtango.napd"}
        data.append(b1)
        # write file
        path = os.path.join(wd, name)
        LOG.debug("Writing TOSCA.meta to: {}".format(path))
        write_block_based_meta_file(data, path)
        return path

    def _do_unpackage(self, wd=None):
        """
        Unpack a 5GTANGO package.
        """
        # TODO re-factor: single try block with multiple excepts.
        # extract package contents
        if wd is None:
            wd = extract_zip_file_to_temp(self.args.unpackage)
        # fuzzy find right wd path
        wd = fuzzy_find_wd(wd)
        # collect metadata
        napdr = None
        try:
            napdr = self.collect_metadata(wd)
        except BaseException as e:
            LOG.error(str(e))
            self.error_msg = str(e)
            return NapdRecord(error=str(e))
        # LOG.debug("Collected metadata: {}".format(napdr))
        # validate metadata
        try:
            self._assert_usable_tango_package(napdr)
        except MetadataValidationException as e:
            LOG.error(str(e))
            self.error_msg = str(e)
            napdr.error = str(e)
            return napdr
        # validate checksums
        try:
            self._validate_package_content_checksums(wd, napdr)
        except ChecksumException as e:
            LOG.error(str(e))
            self.error_msg = str(e)
            napdr.error = str(e)
            return napdr
        except MissingFileException as e:
            LOG.error(str(e))
            self.error_msg = str(e)
            napdr.error = str(e)
            return napdr
        # validate network service using tng-validate
        try:
            # we do a trick here, since tng-validate needs a
            # 5GTANGO project strcuture to work on, and we not
            # always use the 5GTANGO project storage backend:
            # Solution: we store it to a temporary 5GTANGO project
            # only used for the validation step.
            if (self.args.skip_validation or
                    self.args.validation_level == 'skip'):
                LOG.warning(
                    "Skipping validation (--skip-validation).")
            else:  # ok, do the validation
                tmp_project_path = tempfile.mkdtemp()
                tmp_tpfbe = TangoProjectFilesystemBackend(self.args)
                tmp_napdr = tmp_tpfbe.store(
                    napdr, wd, self.args.unpackage, output=tmp_project_path)
                tmp_project_path = tmp_napdr.metadata["_storage_location"]
                validate_project_with_external_validator(
                    self.args, tmp_project_path)
                shutil.rmtree(tmp_project_path)
        except BaseException as e:
            LOG.exception(str(e))
            self.error_msg = str(e)
            napdr.error = str(e)
            return napdr
        # call storage backend
        if self.storage_backend is not None:
            try:
                # store/upload contents of package and get updated napdr
                napdr = self.storage_backend.store(
                    napdr, wd, self.args.unpackage)
            except BaseException as e:
                LOG.error(str(e))
                LOG.debug("Args: {}".format(self.args))
                self.error_msg = str(e)
                napdr.error = str(e)
                return napdr

        # TODO clean up temporary files and folders
        return napdr

    @EtsiPackager._do_package_closure
    def _do_package(self, napdr, project_path, **kwargs):
        """
        Pack a 5GTANGO project to a 5GTANGO package.
        """
        # 4. generate package's directory tree
        self._pack_create_package_directory_tree(napdr)
        # 5. copy project files to package tree
        self._pack_copy_files_to_package_directory_tree(
            project_path, napdr)
        # 6. generate/write NAPD
        napd_path = self._pack_write_napd(napdr)
        # 7. generate/write ETSI MF
        etsi_mf_path = self._pack_gen_write_etsi_manifest(napdr)
        # 8. generate/write TOSCA
        self._pack_gen_write_tosca_manifest(napdr, napd_path, etsi_mf_path)
        # 9. zip package
        auto_file_name = "{}.{}.{}.tgo".format(napdr.vendor,
                                               napdr.name,
                                               napdr.version)
        path_dest = self.args.output
        if path_dest is None:
            path_dest = auto_file_name
        if os.path.isdir(path_dest):
            path_dest = os.path.join(path_dest, auto_file_name)
        creat_zip_file_from_directory(napdr._project_wd, path_dest)
        LOG.info("Package created: '{}'"
                 .format(path_dest))
        # annotate napdr
        napdr.metadata["_storage_location"] = path_dest
        return napdr

# #########################
# Helpers
# #########################

def creat_zip_file_from_directory(path_src, path_dest):
    LOG.debug("Zipping '{}' ...".format(path_dest))
    t_start = time.time()
    zf = zipfile.ZipFile(path_dest, 'w', zipfile.ZIP_DEFLATED)
    for root, _, files in os.walk(path_src):
        for f in files:
            zf.write(os.path.join(root, f),
                     os.path.relpath(
                         os.path.join(root, f), path_src))
    zf.close()
    LOG.debug("Zipping done ({:.4f}s)".format(time.time()-t_start))


def fuzzy_find_wd(wd):
    """
    Zip files often contain a kind of
    'root' folder, instead of placing the files themselves
    into the root of the archive.
    This function tries to find the 'real' root of the
    extracted package directory and returns it.
    Detection is done by 'TOSCA-Metadata' folder.
    """
    found_path = search_for_file(os.path.join(wd, "**/TOSCA-Metadata"))
    if found_path is None:
        return wd
    wd_root = found_path.replace("TOSCA-Metadata", "").strip()
    if wd_root != wd:
        LOG.warning("Fuzzy found WD root: {}".format(wd_root))
    return wd_root


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
