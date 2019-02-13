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

import os
import yaml
import re
from tngsdk.package.logger import TangoLogger


LOG = TangoLogger.getLogger(__name__)


class StorageBackendFileException(BaseException):
    pass


class StorageBackendUploadException(BaseException):
    pass


class StorageBackendDuplicatedException(BaseException):
    pass


class StorageBackendResponseException(BaseException):
    pass


class BaseStorageBackend(object):

    def __init__(self, args):
        self.args = args

    def _get_package_content_of_type(self, napdr, wd, mime_type):
        """
        Returns a list of paths to files referenced in napdr that
        match the given mime type.
        Returns a list of tuples: (full_mime_type, file_path)
        """
        r = list()
        pattern = re.compile(mime_type)
        for pc in napdr.package_content:
            if pattern.search(pc.get("content-type")) is not None:
                r.append((pc.get("content-type"),
                          os.path.join(wd, pc.get("source"))))
        return r

    def _get_package_content_not_of_type(self, napdr, wd, mime_type):
        """
        Returns a list of paths to files referenced in napdr that
        not match the given mime type.
        Returns a list of tuples: (full_mime_type, file_path)
        """
        r = list()
        pattern = re.compile(mime_type)
        for pc in napdr.package_content:
            if pattern.search(pc.get("content-type")) is None:
                r.append((pc.get("content-type"),
                          os.path.join(wd, pc.get("source"))))
        return r

    def _get_id_triple_from_descriptor_file(self, path):
        """
        gets vendor, name, version from YAML descriptor
        returns dict
        """
        # 5gtango
        try:
            res = dict()
            with open(path, 'r') as f:
                data = yaml.load(f)
                res["vendor"] = data["vendor"]
                res["name"] = data["name"]
                res["version"] = data["version"]
            return res
        except BaseException as e:
            del e
        # TODO OSM
        # TODO ONAP
        return None

    def store(self, napdr, wd, pkg_file):
        """
        Must be overwritten.
        """
        LOG.error("store(...) not implemented.")
        return napdr
