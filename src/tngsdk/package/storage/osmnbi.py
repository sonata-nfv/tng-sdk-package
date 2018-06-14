#  Copyright (c) 2018 SONATA-NFV, 5GTANGO, Paderborn University
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
# Neither the name of the SONATA-NFV, 5GTANGO, Paderborn University
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
# import requests
# import yaml
# import json
from tngsdk.package.storage import BaseStorageBackend  # , \
#    StorageBackendResponseException, StorageBackendUploadException


LOG = logging.getLogger(os.path.basename(__file__))


class OsmNbiBackend(BaseStorageBackend):

    def __init__(self, args):
        self.args = args
        # get environment config
        # cat_url = OSM NBI URL
        self.cat_url = os.environ.get(
            "CATALOGUE_URL",  # ENV CATALOGUE_URL
            "http://127.0.0.1:4011/catalogues/api/v2"  # fallback
        )
        # args overwrite other configurations (e.g. for unit tests)
        if "cat_url" in self.args:
            self.cat_url = self.args.cat_url
        LOG.info("osn-nbi-be: initialized OsmNbiBackend({})"
                 .format(self.cat_url))

    def store(self, napdr, wd, pkg_file):
        """
        Turns the given unpacked package into
        multiple OSM packages and on-boards
        them on the given OSM instance.
        """
        LOG.error("osm-nbi-be: store() not yet implemented.")
        return napdr
