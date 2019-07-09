import hashlib
import os
import tempfile
import shutil
import tarfile
from tngsdk.package.helper import file_hash, _makedirs
from tngsdk.package.packager.packager import EtsiPackager, NapdRecord
from tngsdk.package.packager.exeptions import NoOSMFilesFound
from tngsdk.package.logger import TangoLogger

LOG = TangoLogger.getLogger(__name__)


class OsmPackager(EtsiPackager):
    folders_nsd = ["ns_config", "vnf_config", "icons", "scripts"]
    folders_vnf = ["charms", "cloud_init", "icons", "images", "scripts"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.checksum_algorithm = "MD5"
        self.ns_temp_dir = None

    def file_hash(self, *args, **kwargs):
        """
        Returns hash value for a osm-file (MD5 Algorithm),
        by using helper.file_hash().
        Args:
            *args:
            **kwargs:

        Returns:
            hash value
        """
        return file_hash(h_func=hashlib.md5, *args, **kwargs)

    def store_checksums(self, path, files, checks_filename="checksums.txt"):
        """
        Args:
            path: storage_location (str) of checksums-file without filename,
                    only directory
            files: list of dictionaries, with key 'hash'
                   (typically a subset of NapdRecord.package_content)

        Returns:
            None
        """
        lines = ["{} {}\n".format(file["hash"], file["filename"])
                 for file in files if isinstance(file["hash"], str)]
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
                        folders=folders_vnf, project_path="",
                        checks_filename="checksums.txt"):
        """
        Creates a temporary directory, which is will be used to create a
        .tar.gz-archive.
        Args:
            subdir_name: str: name of parent folder
            descriptor: str
            hash: hash value of descriptor file
            folders: list of str - folders to create in the directory
            project_path: str
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
            shutil.copy(os.path.join(project_path, descriptor), temp)
        if hash is not None:
            with open(os.path.join(temp, checks_filename), "w") as f:
                f.writelines(["{} {}\n".format(hash, descriptor)])
        return temp

    def create_temp_dirs(self, package_set, *args, **kwargs):
        """
        Create temporary directories for all future archives.
        Paths of the directories stored in attribute temp_dir of the objects
        of type OsmPackage contained in package_set.nsd und package_set.vnfds.
        Args:
            package_set: of type OsmPackageSet
            args and kwargs inserted in self.create_temp_dir()

        Returns:
            None
        """
        for package in package_set.packages():
            package.temp_dir = self.create_temp_dir(
                package._subdir,
                package.descriptor_file["_project_source"],
                package.descriptor_file["hash"],
                package.folders,
                *args, **kwargs
            )

    def attach_files(self, package_set, project_path=""):
        """
        Copy files to temporary directories.
        Args:
            package_set: of type OsmPackageSet
            project_path: str
        Returns:
            None
        """
        for package in package_set.packages():
            for file in package.package_content:
                destination = os.path.join(package.temp_dir, file["source"])
                _makedirs(destination)
                shutil.copy(
                    os.path.join(project_path, file["_project_source"]),
                    destination)
            self.store_checksums(package.temp_dir, package.package_content)

    def pack_packages(self, wd, package_set):
        """
        Creates .tar.gz archives.
        Args:
            wd: path where to create archives
            package_set: of type OsmPackageSet

        Returns:
            None
        """
        for package in package_set.packages():
            package_path = (
                os.path.join(wd, "{}.tar.gz".format(package.package_name)))
            with tarfile.open(package_path, "w:gz") as f:
                f.add(package.temp_dir, arcname=package.package_name)

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
            _tag = tag.split(":")
            if _tag[0] == "osm-target":
                return _tag[1]
        if "image" in _type:
            return "icons"
        elif "scripts" in _type:
            return "scripts"
        elif "cloud.init" in filename:
            return "cloud_init"
        return ""

    def compress_subfolders(self, project_descriptor, pp):
        """
        Overloads function in parent class. Doesn't actually compress the
        subfolder. Adds all files of subfolder to the project descriptor
        instead.
        Args:
            project_descriptor:
            pp:

        Returns:

        """
        subfolder_files = []
        subfolders = []
        for i, file in enumerate(project_descriptor["files"]):
            if 'application/vnd.folder.compressed.zip' == file["type"]:
                foldername = os.path.basename(file["path"])
                files = self._compress_subfolder(foldername, pp)
                tags = [tg.split(":")[0] for tg in file["tags"]]
                if "osm-target" not in tags:
                    file["tags"].append(
                        "osm-target:{}".format(foldername))
                subfolder_files.extend(list(
                    map(lambda f: {"path": f,
                                   "type": "text/plain",
                                   "tags": file["tags"]}, files)))
                subfolders.append(i)
        for i in subfolders[::-1]:
            project_descriptor["files"].pop(i)
        project_descriptor["files"].extend(subfolder_files)

    def _compress_subfolder(self, subf_path, pp):
        """
        Returns a list of subfolder-files and of its files subfolder.
        Args:
            subf_path:
            pp:

        Returns:
            list of paths
        """
        files = []
        _listed_dirs = os.listdir(os.path.join(pp, subf_path))
        for dir in _listed_dirs:
            path = os.path.join(subf_path, dir)
            if os.path.isfile(os.path.join(pp, path)):
                files.append(path)
            elif os.path.isdir(os.path.join(pp, path)):
                sub_subfolder_files = self._compress_subfolder(
                    dir, os.path.join(pp, subf_path))
                files.extend(list(map(lambda s: os.path.join(subf_path, s),
                                      sub_subfolder_files)))
        return files


    @EtsiPackager._do_package_closure
    def _do_package(self, napdr, project_path=None, **kwargs):
        """
        Pack a 5GTANGO project to OSM packages.
        """
        osm_package_set = OsmPackagesSet(napdr)
        wd = self.args.output
        if wd is None:
            wd = "{}.{}.{}".format(napdr.vendor,
                                   napdr.name,
                                   napdr.version)
        if not os.path.exists(wd):
            os.makedirs(wd)

        osm_package_set.project_name = os.path.basename(wd)

        osm_package_set._project_wd = wd
        osm_package_set._sort_files()
        # 5. creating temporary directories and copy descriptors
        self.create_temp_dirs(osm_package_set, project_path)
        # 6. copy files
        self.attach_files(osm_package_set, project_path)
        # 7. create packages from temporary directories
        self.pack_packages(wd, osm_package_set)
        return osm_package_set


class OsmPackagesSet(NapdRecord):
    """
    Contains runtime data for creating OSM-Packages from 5GTANGO projects.
    """
    folders_nsd = ["ns_config", "vnf_config", "icons", "scripts"]
    folders_vnf = ["charms", "cloud_init", "icons", "images", "scripts"]

    def __init__(self, napdr=None, **kwargs):
        if napdr is None:
            napdr = super().__init__(**kwargs)
        self.__dict__.update(napdr.__dict__)

        for d in self.package_content:
            d["filename"] = os.path.basename(d["_project_source"])

        self.project_name = None

        self.nsd = None
        self.vnfds = {}

    def packages(self):
        """
        Generator to iterate over all packages of this OsmPackagesSet.
        Returns:
            Generator object like [self.nsd] + self.vnfds
        """
        yield self.nsd
        for vnfd in self.vnfds.values():
            yield vnfd

    def _sort_files(self, folders_nsd=folders_nsd, folders_vnf=folders_vnf):
        """
        Iterates over self.napdr.package_content and filters for files
        relevant for OSM (identified by content-type and tags). Creates
        OsmPackage() from every descriptor and add other files to relevant
        OsmPackage().
        Args:
            folders_nsd: list of directories (str) to create in the later
                        ns-archive
            folders_vnf: list of directories (str) to create in the later
                        vnf-archive

        Returns:
            None
        """
        general_files = []
        ns_files = []
        vnf_files = []
        unique_files = {}
        for file in self.package_content:
            if "osm.nsd" in file["content-type"]:
                self.nsd = OsmPackage(file, project_name=self.project_name,
                                      folders=folders_nsd)
            elif "osm.vnfd" in file["content-type"]:
                _filename = os.path.splitext(file["filename"])[0]
                self.vnfds[_filename] = (
                    OsmPackage(file,
                               project_name=self.project_name,
                               folders=folders_vnf))
            else:
                tags = map(lambda tag: tag.split("."), file["tags"])
                for tag in tags:
                    if tag[-1] == "osm":
                        general_files.append(file)
                    elif tag[-2:] == ["osm", "ns"]:
                        ns_files.append(file)
                    elif tag[-2:] == ["osm", "vnf"]:
                        vnf_files.append(file)
                    elif tag[-3:-1] == ["osm", "vnf"]:
                        if tag[-1] in unique_files:
                            unique_files[tag[-1]].append(file)
                        else:
                            unique_files[tag[-1]] = [file]

        if self.nsd is None and self.vnfds == {}:
            raise NoOSMFilesFound("No OSM-descriptor-files found in project")

        self.nsd.package_content.extend(general_files+ns_files)
        for name, vnf_package in self.vnfds.items():
            vnf_package.package_content.extend(general_files+vnf_files)
            if name in unique_files:
                self.vnfds[name].package_content.extend(unique_files[name])


class OsmPackage:
    """
    Contains runtime date to a single OsmPackage.
    """

    def __init__(self, descriptor_file, **kwargs):
        self._subdir = None
        self.folders = None
        self.project_name = ""
        self.temp_dir = None
        self.descriptor_file = descriptor_file
        self.__dict__.update(kwargs)
        self._subdir = "_".join(
            [self.project_name,
             os.path.splitext(
                 os.path.basename(self.descriptor_file["filename"]))[0]])
        self.package_name = self._subdir
        self.package_content = []
