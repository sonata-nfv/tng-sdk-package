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
import requests


LOG = logging.getLogger(os.path.basename(__file__))


class StorageBackendFileException(BaseException):
    pass


class StorageBackendUploadException(BaseException):
    pass


class BaseStorageBackend(object):
    pass


class TangoCatalogBackend(BaseStorageBackend):

    def __init__(self, args):
        self.args = args
        # get environment config
        self.cat_url = os.environ.get(
            "CATALOGUE_URL",  # ENV CATALOGUE_URL
            "http://127.0.0.1:4011/catalogues/api/v2"  # fallback
        )
        LOG.info("Initialized TangoCatalogBackend({})"
                 .format(self.cat_url))

    def _get_package_content_of_type(self, napdr, wd, mime_type):
        """
        Returns a list of paths to files referenced in napdr that
        match the given mime type.
        """
        r = list()
        for pc in napdr.package_content:
            if pc.get("content-type") == mime_type:
                r.append(os.path.join(wd, pc.get("source")))
        return r

    def _post_yaml_file_to_catalog(self, endpoint, path):
        url = "{}{}".format(self.cat_url, endpoint)
        LOG.info("POST YAML to {} content {}".format(url, path))
        with open(path, "rb") as f:
            data = f.read()
            return requests.post(url,
                                 data=data,
                                 headers={"Content-Type":
                                          "application/x-yaml"})
        return None

    def _post_pkg_file_to_catalog(self, endpoint, path):
        url = "{}{}".format(self.cat_url, endpoint)
        cd_str = "attachment; filename={}.tgo".format(os.path.basename(path))
        LOG.info("POST PKG to {} content {} using {}"
                 .format(url, path, cd_str))
        with open(path, "rb") as f:
            data = f.read()
            return requests.post(url,
                                 data=data,
                                 headers={"Content-Type": "application/zip",
                                          "Content-Disposition": cd_str})
        return None

    def _post_package_descriptor(self, napdr):
        """
        Uploads NAPD.yaml
        """
        napd_path = napdr.metadata.get("_napd_path")
        if napd_path is None:
            raise StorageBackendFileException(
                "NAPD.yaml not found. Attention: TangoCatalogBackend supports"
                + " 5GTANGO packages only (no NAPDR upload yet).")
        return self._post_yaml_file_to_catalog("/packages", napd_path)

    def _post_vnf_descriptors(self, vnfd):
        return self._post_yaml_file_to_catalog("/vnfs", vnfd)

    def _post_ns_descriptors(self, nsd):
        return self._post_yaml_file_to_catalog("/network-services", nsd)

    def _post_test_descriptors(self, tstd):
        return self._post_yaml_file_to_catalog("/tests", tstd)

    def _build_catalog_metadata(self, napdr, vnfds, nsds, pkg_uuid):
        """
        Build dict with additional data for catalog.
        see: https://github.com/sonata-nfv/tng-sdk-package/issues/14
        """
        pass

    def store(self, napdr, wd, pkg_file):
        """
        Stores the pushes given package and its files to the
        5GTANGO catalog.
        :param napdr: package descriptor record from unpacking
        :param wd: working directory with package contents
        :param pkg_file: path to the original package file
        :return napdr: updated/annotated napdr
        """

        # 1. upload package descriptor
        self._post_package_descriptor(napdr)
        # 2. collect and upload VNFDs
        vnfds = self._get_package_content_of_type(
            napdr, wd, "application/vnd.5gtango.vnfd")
        for vnfd in vnfds:
            self._post_vnf_descriptors(vnfd)
        # 3. collect and upload NSDs
        nsds = self._get_package_content_of_type(
            napdr, wd, "application/vnd.5gtango.nsd")
        for nsd in nsds:
            self._post_ns_descriptors(nsd)
        # 4. collect and upload TESTDs
        tstds = self._get_package_content_of_type(
            napdr, wd, "application/vnd.5gtango.tstd")
        for tstd in tstds:
            self._post_vnf_descriptors(tstd)
        # 5. upload Package file *.tgo and get catalog UUID
        pkg_resp = self._post_pkg_file_to_catalog(
            "/tgo-packages", pkg_file)
        if pkg_resp.status_code != 201 and pkg_resp.status_code != 200:
            raise StorageBackendUploadException(
                "Could not upload package. Response: {}"
                .format(pkg_resp.status_code))
        pkg_uuid = pkg_resp.json().get("uuid")
        pkg_url = "{}/tgo-packages/{}".format(self.cat_url, pkg_uuid)
        LOG.info("Received PKG UUID from catalog: {}".format(pkg_uuid))
        # 6. upload mata data mapping (catalog support)
        cat_metadata = self._build_catalog_metadata(
            napdr, vnfds, nsds, pkg_uuid)
        LOG.debug("Prepared add. catalog meta data: {}".format(cat_metadata))
        LOG.error("Additional catalog meta data not yet pushed to catalog!")
        # updated/annotated napdr
        napdr.metadata["_storage_uuid"] = pkg_uuid
        napdr.metadata["_storage_location"] = pkg_url
        LOG.info("TangoCatalogBackend stored: {}".format(pkg_url))
        return napdr
