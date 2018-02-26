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
import uuid


LOG = logging.getLogger(os.path.basename(__file__))


class UnsupportedPackageFormat(BaseException):
    pass


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
        # check if we have a packager for the given format or abort
        if packager_cls is None:
            raise UnsupportedPackageFormat(
                "Pkg. format: {} not supported.".format(pkg_format))
        p = packager_cls(args)
        # TODO clean up after packaging request has completed (pot. mem. leak)
        self._packager_list.append(p)
        return p


# have one global instance of the manager
PM = PackagerManager()


class Packager(object):
    # TODO abstract, have specific packagers per format

    def __init__(self, args):
        # unique identifier for this package request
        self.uuid = uuid.uuid4()
        self.args = args
        LOG.info("Packager created: {}".format(self))
        LOG.debug("Packager args: {}".format(self.args))

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.uuid)

    def package(self, callback_func=None):
        LOG.warning("packaging not implemented")

    def unpackage(self, callback_func=None):
        LOG.warning("unpackaging not implemented")

    def _do_unpackage(self):
        LOG.warning("_do_unpackage has to be overwritten")

    def _do_package(self):
        LOG.warning("_do_unpackage has to be overwritten")


class TangoPackager(Packager):
    pass


class EtsiPackager(Packager):
    pass
