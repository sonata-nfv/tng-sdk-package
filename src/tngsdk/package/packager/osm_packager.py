import hashlib
import os
import tempfile
import shutil
import tarfile
from tngsdk.package.helper import file_hash, _makedirs
from tngsdk.package.packager.packager import EtsiPackager, NapdRecord
from tngsdk.package.validator import validate_project_with_external_validator
from tngsdk.package.packager.exeptions import NoOSMFilesFound, MissingInputException, MissingMetadataException
from tngsdk.package.logger import TangoLogger

LOG = TangoLogger.getLogger(__name__)


class OsmPackager(EtsiPackager):
    folders_nsd = ["ns_config", "vnf_config", "icons", "scripts"]
    folders_vnf = ["charms", "cloud_init", "icons", "images", "scripts"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checksum_algorithm = "MD5"
        self.ns_temp_dir = None

    def _pack_create_napdr(self, *args, **kwargs):
        """
        Extends Packager._pack_create_napdr(). Adds a filename key-value-pair
        to every element of napdr.package_content.
        Args:
            *args:
            **kwargs:

        Returns:
            napdr of type NapdRecord
        """
        napdr = super()._pack_create_napdr(*args, **kwargs)
        for d in napdr.package_content:
            d["filename"] = os.path.basename(d["_project_source"])
        return napdr

    def file_hash(self, *args, **kwargs):
        return file_hash(h_func=hashlib.md5, *args, **kwargs)

    def store_checksums(self, path, files, checks_filename="checksums.txt"):
        """

        Args:
            path: storage_location (str)
            files: list of dictionaries
                   (typically a subset of NapdRecord.package_content)

        Returns:
            None
        """
        lines = ["{} {}\n".format(file["hash"], file["filename"])
                 for file in files]
        with open(os.path.join(path, checks_filename), "a") as f:
            f.writelines(lines)

    def _pack_package_source_path(self, f):
        """
        Used in Packager._pack_create_napdr()
        Args:
            f: dict (yaml describing file)

        Returns:
            name of destination folder (str) for the file in an osm-package
        """
        filename = os.path.basename(f.get("path"))
        ret = self.choose_folder(f.get("tags", list()),
                                 f.get("type", "text/plain"),
                                 filename)
        return ret

    def create_temp_dir(self, subdir_name=None, descriptor=None, hash=None,
                        folders=folders_vnf, checks_filename="checksums.txt"):
        """
        Creates a temporary directory, which is will be used to create a
        .tar.gz-archive.
        Args:
            subdir_name: str: name of parent folder
            descriptor: str
            hash: hash value of descriptor file
            folders: list of str - folders to create in the directory
            checks_filename: name of file with checksums of the files

        Returns:
            path to the temp directory
        """
        temp = tempfile.mkdtemp()
        if subdir_name is not None:
            _makedirs(os.path.join(temp, subdir_name))
            temp = os.path.join(temp, subdir_name)
        for folder in folders:
            _makedirs(os.path.join(temp, folder))
        if descriptor is not None:
            shutil.copy(os.path.join(self.args.package, descriptor), temp)
        if hash is not None:
            with open(os.path.join(temp, checks_filename), "w") as f:
                f.writelines(["{} {}\n".format(hash, descriptor)])
        return temp

    def _sort_files(self, napdr):
        """
        Chooses relevant files and sorts them after store destination.
        Args:
            napdr: NapdRecord

        Returns:
            None
        """
        self.nsd = None  # ns
        self.vnfds = []  # list of vnfs

        self.general_files = []  # files to store in all archives
        self.ns_files = []  # files to store only in the ns-archive
        self.vnf_files = []  # files to store in all vnfs
        # files to store only in certain vnfs, list of 2-tuples
        self.unique_files = []
        for file in napdr.package_content:
            # find relevant descriptors
            if "osm.nsd" in file["content-type"]:
                self.nsd = file
            elif "osm.vnfd" in file["content-type"]:
                self.vnfds.append(file)
            else:
                # find other relevant files
                tags = map(lambda tag: tag.split("."),
                           file.get("tags", list()))
                for tag in tags:
                    if tag[-1] == "osm":
                        self.general_files.append(file)
                    elif tag[-2:] == ["osm", "ns"]:
                        self.ns_files.append((file))
                    elif tag[-2:] == ["osm", "vnf"]:
                        self.vnf_files.append(file)
                    elif tag[-3:-1] == ["osm", "vnf"]:
                        package_name = "_".join([self.project_name, tag[-1]])
                        self.unique_files.append((package_name, file))
        if self.nsd is None and self.vnfds == []:
            raise NoOSMFilesFound("No OSM-descriptor-files found in project")

    def create_temp_dirs(self, project_name):
        """
        Create temporary directories for all future archives.
        Paths of the directories stored in self.ns_temp_dir and
        self.vnf_temp_dirs.
        Args:
            project_name: str: used to construct archive names.

        Returns:
            None
        """
        if self.nsd is not None:
            self.ns_temp_dir = self.create_temp_dir(
                "_".join([project_name,  # subdir
                          os.path.splitext(self.nsd["filename"])[0]]),
                os.path.join(self.nsd["_project_source"]),  # descriptor_path
                self.nsd["hash"],  # hash
                OsmPackager.folders_nsd)  # folders
        self.vnf_temp_dirs = {}
        for vnfd in self.vnfds:
            package_name = "_".join([project_name,  # subdir
                                     os.path.splitext(vnfd["filename"])[0]])
            self.vnf_temp_dirs[package_name] = (
                self.create_temp_dir(package_name,  # package_name
                                     vnfd["_project_source"],  # desc_path
                                     vnfd["hash"]))  # hash

    def attach_files(self):
        """
        Copy files to temporary directories.
        Returns:
            None
        """
        # files for ns
        if self.ns_temp_dir is not None:
            for file in self.general_files+self.ns_files:
                folder = os.path.join(self.ns_temp_dir,
                                      file["source"])
                _makedirs(folder)
                shutil.copy(os.path.join(self.args.package,
                                         file["_project_source"]), folder)
            self.store_checksums(self.ns_temp_dir,
                                 self.general_files+self.ns_files)
        # files for all vnfs
        for path in self.vnf_temp_dirs.values():
            for file in self.general_files+self.vnf_files:
                folder = os.path.join(path, file["source"])
                _makedirs(folder)
                shutil.copy(os.path.join(self.args.package,
                                         file["_project_source"]), folder)
            self.store_checksums(path, self.general_files+self.vnf_files)
        # files for unique vnfs
        for package_name, file in self.unique_files:
            if package_name not in self.vnf_temp_dirs:
                LOG.warning("{} not found. {} ignored.".format(
                    package_name, file["filename"]))
                continue
            folder = os.path.join(self.vnf_temp_dirs[package_name],
                                  file["source"])
            _makedirs(folder)
            shutil.copy(os.path.join(self.args.package,
                                     file["_project_source"]), folder)
            self.store_checksums(self.vnf_temp_dirs[package_name], [file])

    def create_packages(self, wd):
        """
        Creates .tar.gz archives.
        Args:
            wd: path where to create archives

        Returns:
            None
        """
        package_name = os.path.basename(self.ns_temp_dir.strip(os.sep))
        package_path = os.path.join(wd, "{}.tar.gz".format(package_name))
        with tarfile.open(package_path, "w:gz") as f:
            f.add(self.ns_temp_dir, arcname=package_name)
        for package_name, path in self.vnf_temp_dirs.items():
            package_path = os.path.join(wd, "{}.tar.gz".format(package_name))
            with tarfile.open(package_path, "w:gz") as f:
                f.add(path, arcname=package_name)

    def choose_folder(self, tags, _type, filename):
        """
        Returns a foldername where to place a file in an archive.
        Args:
            tags: list of strs
            _type: content_type (str)
            filename: str

        Returns:
            foldername (str)
        """
        for tag in tags:
            _tag = tag.split(".")
            if _tag[0] == "folder":
                return _tag[1]
        if "image" in _type:
            return "icons"
        elif "scripts" in _type:
            return "scripts"
        elif "cloud.init" in filename:
            return "cloud_init"
        return ""

    @EtsiPackager._do_package_closure
    def _do_package(self, napdr, **kwargs):
        """
        Pack a 5GTANGO project to OSM packages.
        """
        wd = self.args.output
        if wd is None:
            wd = "{}.{}.{}".format(napdr.vendor,
                                   napdr.name,
                                   napdr.version)
        if not os.path.exists(wd):
            os.makedirs(wd)

        self.project_name = os.path.basename(wd)

        napdr._project_wd = wd
        # 4. assign files to objects
        self._sort_files(napdr)
        # 5. creating temporary directories and copy descriptors
        self.create_temp_dirs(self.project_name)
        # 6. copy files
        self.attach_files()
        # 7. create packages from temporary directories
        self.create_packages(wd)
        return napdr


class OsmPackagesSet(NapdRecord):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nsd = None
        self.vnfds = []

        self.general_files = []
        self.ns_files = []
        self.vnf_files = []
        self.unique_files = {}

        self.ns_temp_dir = None
        self.vnf_temp_dirs = {}

    def _sort_files(self, napdr):
        for file in napdr.package_content:
            if "osm.nsd" in file["content-type"]:
                self.nsd = file
            elif "osm.vnfd" in file["content-type"]:
                self.vnfds.append(file)
            else:
                tags = map(lambda tag: tag.split("."), file["tags"])
                for tag in tags:
                    if tag[-1] == "osm":
                        self.general_files.append(file)
                    elif tag[-2:] == ["osm", "ns"]:
                        self.ns_files.append((file))
                    elif tag[-2:] == ["osm", "vnf"]:
                        self.vnf_files.append(file)
                    elif tag[-2:-1] == ["osm", "vnf"]:
                        self.unique_files[tag[-1]] = file


class OsmPackage():

    def __init__(self, descriptor_file):
        self.descriptor_file = descriptor_file


class OsmNSPackage(OsmPackage):
    pass


class OsmVNFPackage(OsmPackage):
    pass
