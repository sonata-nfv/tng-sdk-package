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


LOG = logging.getLogger(os.path.basename(__file__))


class UnsupportedPackageFormat(BaseException):
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
            raise UnsupportedPackageFormat(
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


class TangoPackager(Packager):

    def _extract(self, path_zip, path_dest):
        """
        Simply extract the entire ZIP file for now.
        Might be improved for larger files.
        """
        # get path of output folder (it is based on zip name)
        outp = os.path.join(
            path_dest, os.path.splitext(
                os.path.basename(path_zip))[0])
        LOG.debug("Unzipping '{}' to '{}' ...".format(path_zip, outp))
        t_start = time.time()
        # unzipping
        with zipfile.ZipFile(path_zip, "r") as f:
            f.extractall(path_dest)
        LOG.debug("Unzipping done ({:.4f}s)".format(time.time()-t_start))
        return outp

    def _do_unpackage(self):
        wd = self._extract(self.args.unpackage, self.args.output)
        # TODO work on extracted files
        # TODO clean up temporary files and folders
        assert(wd is not None)
        return {"error": None}

    def _do_package(self):
        LOG.warning("TangoPackager _do_package not implemented")
        return {"error": None}


class EtsiPackager(Packager):
    pass
