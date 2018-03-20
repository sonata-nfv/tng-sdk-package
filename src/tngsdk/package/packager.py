#  Copyright (c) 2018 SONATA-NFV, 5GTANGO, UBIWHERE, Paderborn University
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
import logging
import os
import threading
import uuid
import zipfile
import time
import tempfile
import io
import glob


LOG = logging.getLogger(os.path.basename(__file__))


class UnsupportedPackageFormatException(BaseException):
    pass


class MissingMetadataException(BaseException):
    pass


class PkgStatus(object):
    WAITING = "waiting"
    RUNNING = "running"
    FAILED = "failed"
    DONE = "done"


class PackagerManager(object):

    def __init__(self):
        self._packager_list = list()

    def new_packager(self, args, pkg_format="eu.5gtango"):
        # select the right Packager for the given format
        packager_cls = None
        if pkg_format == "eu.5gtango":
            packager_cls = TangoPackager
        elif pkg_format == "eu.etsi":
            packager_cls = EtsiPackager
        elif pkg_format == "test":
            packager_cls = TestPackager
        # check if we have a packager for the given format or abort
        if packager_cls is None:
            raise UnsupportedPackageFormatException(
                "Pkg. format: {} not supported.".format(pkg_format))
        p = packager_cls(args)
        # TODO cleanup after packaging has completed (memory leak!!!)
        self._packager_list.append(p)
        return p

    def get_packager(self, uuid):
        LOG.debug(self._packager_list)
        for p in self._packager_list:
            if str(p.uuid) == uuid:
                return p
        return None


# have one global instance of the manager
PM = PackagerManager()


class Packager(object):
    """
    Abstract packager class.
    Takes care about asynchronous packaging processes.
    Actual packaging/unpackaging methods have to be overwritten
    by format-specific packager classes.
    """

    def __init__(self, args):
        # unique identifier for this package request
        self.uuid = uuid.uuid4()
        self.status = PkgStatus.WAITING
        self.error_msg = None
        self.args = args
        self.result = None
        LOG.info("Packager created: {}".format(self))
        LOG.debug("Packager args: {}".format(self.args))

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.uuid)

    def _wait_for_thread(self, t):
        while t.is_alive():
            LOG.debug("Waiting for package/unpackage process ...")
            # TODO display a nicer process status when in CLI mode
            t.join(timeout=0.5)

    def package(self, callback_func=None):
        t = threading.Thread(
            target=self._thread_package,
            args=(callback_func,))
        t.daemon = True
        self.status = PkgStatus.RUNNING
        t.start()
        if callback_func is None:
            # behave synchronous if callback is None
            self._wait_for_thread(t)

    def unpackage(self, callback_func=None):
        t = threading.Thread(
            target=self._thread_unpackage,
            args=(callback_func,))
        t.daemon = True
        self.status = PkgStatus.RUNNING
        t.start()
        if callback_func is None:
            # behave synchronous if callback is None
            self._wait_for_thread(t)

    def _thread_unpackage(self, callback_func):
        t_start = time.time()
        # call format specific implementation
        self.result = self._do_unpackage()
        LOG.info("Packager done ({:.4f}s): {}".format(
            time.time()-t_start, self))
        self.status = PkgStatus.DONE
        # callback
        if callback_func:
            callback_func(self)

    def _thread_package(self, callback_func):
        t_start = time.time()
        # call format specific implementation
        self.result = self._do_package()
        LOG.info("Packager done ({:.4f}s): {}".format(
            time.time()-t_start, self))
        self.status = PkgStatus.DONE
        # callback
        if callback_func:
            callback_func(self)

    def _do_unpackage(self):
        LOG.error("_do_unpackage has to be overwritten")
        # time.sleep(2)
        return {"error": "_do_unpackage has to be overwritten"}

    def _do_package(self):
        LOG.error("_do_unpackage has to be overwritten")
        # time.sleep(2)
        return {"error": "_do_unpackage has to be overwritten"}


class TestPackager(Packager):

    def _do_unpackage(self):
        return {"error": None}

    def _do_package(self):
        return {"error": None}


class CsarBasePackager(Packager):

    def _read_tosca_meta(self, wd):
        """
        Tries to find TOSCA.meta file.
        Returns list of blocks from that file
        or an list with a single empty block.
        """
        try:
            path = search_for_file(os.path.join(wd, "**/TOSCA.meta"))
            if path is None:
                raise MissingMetadataException("Cannot find TOSCA.meta")
            with open(path, "r") as f:
                return parse_block_based_meta_file(f)
        except BaseException as e:
            LOG.error("Cannot read TOSCA metadata: {}".format(e))
        return [{}]


class EtsiPackager(CsarBasePackager):

    def _read_etsi_manifest(self, wd, tosca_meta):
        """
        Tries to find ETSI Manifest file.
        - try 1: Use "Entry-Manifest" from TOSCA.meta
        - try 2: Look for *.mf file in root of package
        Returns list of blocks from that file
        or an empty list.
        """
        try:
            if (tosca_meta is not None
                    and tosca_meta[0].get("Entry-Manifest") is not None):
                # try 1:
                path = search_for_file(
                    os.path.join(wd, tosca_meta[0].get("Entry-Manifest")))
                if path is None:
                    LOG.warning("Entry-Manifest '{}' not found.".format(
                        tosca_meta[0].get("Entry-Manifest")))
                    # try 2:
                    path = search_for_file(
                        os.path.join(wd, "*.mf"), recursive=False)
            if path is None:
                raise MissingMetadataException(
                    "Cannot find ETSI manifest file.")
            with open(path, "r") as f:
                return parse_block_based_meta_file(f)
        except BaseException as e:
            LOG.error("Cannot read ETSI manifest file: {}".format(e))
        return [{}]


class TangoPackager(EtsiPackager):

    def _read_napd(self, wd):
        # TODO validate (get schema with a global helper?)
        pass

    def _collect_metadata(self, wd):
        tosca_meta = self._read_tosca_meta(wd)
        etsi_mf = self._read_etsi_manifest(wd, tosca_meta)
        napd = self._read_napd(wd)
        print(tosca_meta)
        print(etsi_mf)
        print(napd)
        # TODO unify input metadata
        # (this is non trivial! deduplicate information,
        # the idea is to use a NAPD skeleton and fill its gaps)
        return dict()

    def _do_unpackage(self):
        wd = extract_zip_file_to_temp(self.args.unpackage)
        md = self._collect_metadata(wd)
        # TODO work on extracted files
        # TODO clean up temporary files and folders
        print(md)
        assert(wd is not None)
        assert(md is not None)
        return {"error": None}

    def _do_package(self):
        LOG.warning("TangoPackager _do_package not implemented")
        return {"error": None}

# #########################
# Helpers
# #########################


def find_root_folder_of_pkg(d):
    """
    Zip files can be odd and may contain folders
    w. name of zip file which then contain the root of
    the package structure.
    This functions tries to find the right root.
    """
    root_indicators = ["TOSCA-Metadata"]
    for ri in root_indicators:
        lst = glob.glob("{}/{}".format(d, ri))
        if len(lst) > 0:
            return lst[0].replace(ri, "")
    return d


def extract_zip_file_to_temp(path_zip, path_dest=None):
        """
        Simply extract the entire ZIP file for now.
        Might be improved for larger files.
        Always extract to a temp folder to work on.
        """
        if path_dest is None:
            path_dest = tempfile.mkdtemp()
        LOG.debug("Unzipping '{}' ...".format(path_zip))
        t_start = time.time()
        # unzipping
        with zipfile.ZipFile(path_zip, "r") as f:
            f.extractall(path_dest)
        LOG.debug("Unzipping done ({:.4f}s)".format(time.time()-t_start))
        # get path of output folder (it is based on zip name)
        wd = find_root_folder_of_pkg(path_dest)
        LOG.debug("Working root '{}'".format(wd))
        return wd


def search_for_file(path="**/TOSCA.meta", recursive=True):
    """
    Recursively searches for a file.
    If there are multiple matches, the first one is
    returned.
    param: path: src/**/*.c
    """
    f_lst = list(glob.iglob(path, recursive=recursive))
    LOG.debug("Searching for '{}' found: {}".format(path, f_lst))
    if len(f_lst) > 0:
        return f_lst[0]
    return None


def parse_block_based_meta_file(inputs):
    """
    Parses a block-based meta data file, like used by TOSCA.
    Return list of dicts. Each dict is a block.
    param: inputs: string or file IO object
    [block1, block2, blockN]
    """
    def _parse_line(l):
        prts = l.split(":")  # colon followed by space (TOSCA)
        if len(prts) < 2:
            LOG.warning("Malformed line in block: '{}' len: {}"
                        .format(l, len(l)))
            return None, None
        key = str(prts.pop(0)).strip()  # first part is keys
        value = (": ".join(prts)).strip()  # rest is value
        return key, value

    blocks = list()
    # extract content as stirng
    content = ""
    if isinstance(inputs, io.IOBase):
        # read content from file
        content = inputs.read()
    else:  # assume string as input
        content = inputs
    # parse line by line and build blocks
    curr_block = dict()
    for l in content.split("\n"):
        if len(l.strip()) < 1:
            # new block (empty line)
            if len(curr_block) > 0:
                blocks.append(curr_block.copy())
            curr_block = dict()
        else:  # parse line and add to curr_block
            k, v = _parse_line(l.strip())
            if k is not None:
                curr_block[k] = v
    if len(blocks) < 1:
        # ensure that block_0 is always there
        LOG.warning("No blocks found in: {}".format(inputs))
        blocks.append(dict())
    return blocks
