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
import yaml
import json


LOG = logging.getLogger(os.path.basename(__file__))


class StorageBackendFileException(BaseException):
    pass


class StorageBackendUploadException(BaseException):
    pass


class StorageBackendResponseException(BaseException):
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
        LOG.info("tng-cat-be: initialized TangoCatalogBackend({})"
                 .format(self.cat_url))

    def _get_package_content_of_type(self, napdr, wd, mime_type):
        """
        Returns a list of paths to files referenced in napdr that
        match the given mime type.
        """
        r = list()
        for pc in napdr.package_content:
            if mime_type in pc.get("content-type"):
                r.append(os.path.join(wd, pc.get("source")))
        return r

    def _get_package_content_not_of_type(self, napdr, wd, mime_type):
        """
        Returns a list of paths to files referenced in napdr that
        not match the given mime type.
        """
        r = list()
        for pc in napdr.package_content:
            if mime_type not in pc.get("content-type"):
                r.append(os.path.join(wd, pc.get("source")))
        return r

    def _post_yaml_data_to_catalog(self, endpoint, data):
        url = "{}{}".format(self.cat_url, endpoint)
        LOG.info("tng-cat-be: POST YAML data to {}"
                 .format(url))
        return requests.post(url,
                             data=yaml.dump(data),
                             headers={"Content-Type":
                                      "application/x-yaml"})

    def _post_yaml_file_to_catalog(self, endpoint, path):
        url = "{}{}".format(self.cat_url, endpoint)
        LOG.info("tng-cat-be: POST YAML to {} content {}".format(url, path))
        with open(path, "rb") as f:
            data = f.read()
            return requests.post(url,
                                 data=data,
                                 headers={"Content-Type":
                                          "application/x-yaml"})

    def _post_json_data_to_catalog(self, endpoint, data):
        url = "{}{}".format(self.cat_url, endpoint)
        LOG.info("tng-cat-be: POST JSON data to {}"
                 .format(url))
        return requests.post(url,
                             data=json.dumps(data),
                             headers={"Content-Type":
                                      "application/json"})

    def _post_json_file_to_catalog(self, endpoint, path):
        url = "{}{}".format(self.cat_url, endpoint)
        LOG.info("tng-cat-be: POST JSON to {} content {}".format(url, path))
        with open(path, "rb") as f:
            data = f.read()
            return requests.post(url,
                                 data=data,
                                 headers={"Content-Type":
                                          "application/json"})

    def _post_pkg_file_to_catalog(self, endpoint, path):
        url = "{}{}".format(self.cat_url, endpoint)
        cd_str = "attachment; filename={}.tgo".format(os.path.basename(path))
        cd_str = cd_str.replace(".pkg", "")  # fix to not loose file ext.
        LOG.info("tng-cat-be: POST PKG to {} content {} using {}"
                 .format(url, path, cd_str))
        with open(path, "rb") as f:
            data = f.read()
            return requests.post(url,
                                 data=data,
                                 headers={"Content-Type": "application/zip",
                                          "Content-Disposition": cd_str})

    def _post_generic_file_to_catalog(self, endpoint, path):
        url = "{}{}".format(self.cat_url, endpoint)
        cd_str = "attachment; filename={}".format(os.path.basename(path))
        LOG.info("tng-cat-be: POST generic file to {} content {} using {}"
                 .format(url, path, cd_str))
        with open(path, "rb") as f:
            data = f.read()
            return requests.post(
                url, data=data,
                headers={"Content-Type": "application/octet-stream",
                         "Content-Disposition": cd_str})

    def _post_package_descriptor(self, napdr):
        """
        Uploads annotated NAPDR, not the original NAPD.
        """
        # clean up NAPDR for catalogue upload
        n = napdr.to_dict()
        del n["metadata"]
        del n["error"]
        return self._post_yaml_data_to_catalog("/packages", n)

    def _post_vnf_descriptors(self, vnfd):
        return self._post_yaml_file_to_catalog("/vnfs", vnfd)

    def _post_ns_descriptors(self, nsd):
        return self._post_yaml_file_to_catalog("/network-services", nsd)

    def _post_test_descriptors(self, tstd):
        return self._post_yaml_file_to_catalog("/tests", tstd)

    def _get_id_triple_from_descriptor_file(self, path):
        """
        gets vendor, name, version from YAML descriptor
        returns dict
        """
        res = dict()
        try:
            with open(path, 'r') as f:
                data = yaml.load(f)
                res["vendor"] = data["vendor"]
                res["name"] = data["name"]
                res["version"] = data["version"]
        except BaseException as e:
            LOG.error(str(e))
            raise StorageBackendFileException(
                "Couldn't get ID triple from descriptor {}"
                .format(path))
        return res

    def _build_catalog_metadata(
            self, napdr,
            nsds, vnfds, tstds,
            generic_files_uuids, pkg_uuid):
        """
        Build dict with additional data for catalog mapping.
        see: https://github.com/sonata-nfv/tng-sdk-package/issues/14
        """
        res = dict()
        res["pd"] = {"vendor": napdr.vendor,
                     "name": napdr.name,
                     "version": napdr.version}
        res["nsds"] = [
            self._get_id_triple_from_descriptor_file(f) for f in nsds]
        res["vnfds"] = [
            self._get_id_triple_from_descriptor_file(f) for f in vnfds]
        res["testds"] = [
            self._get_id_triple_from_descriptor_file(f) for f in tstds]
        res["deps"] = []
        res["files"] = [
            {"file_uuid": v, "file_name": k} for
            k, v in generic_files_uuids.items()]
        res["tgo_package_uuid"] = pkg_uuid
        return res

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
        pkg_resp = self._post_package_descriptor(napdr)
        if pkg_resp.status_code != 201:
            raise StorageBackendUploadException(
                "tng-cat-be: could not upload package descriptor: ({}) {}"
                .format(pkg_resp.status_code, pkg_resp.text))
        try:
            pkg_yaml = yaml.load(pkg_resp.text)
        except BaseException as e:
            LOG.exception()
            raise StorageBackendResponseException(
                "tng-cat-be: could not parse YAML response from tng-cat.")
        pkg_uuid = pkg_yaml.get("uuid")
        if pkg_uuid is None:
            raise StorageBackendUploadException(
                "tng-cat-be: could not retrieve package UUID from tng-cat.")
        LOG.info("tng-cat-ne: received PKG UUID from catalog: {}"
                 .format(pkg_uuid))
        pkg_url = "{}/packages/{}".format(self.cat_url, pkg_uuid)
        # 2. collect and upload VNFDs
        vnfds = self._get_package_content_of_type(
            napdr, wd, "application/vnd.5gtango.vnfd")
        for vnfd in vnfds:
            vnfd_resp = self._post_vnf_descriptors(vnfd)
            if vnfd_resp.status_code != 201:
                raise StorageBackendUploadException(
                    "tng-cat-be: could not upload VNF descriptor: ({}) {}"
                    .format(vnfd_resp.status_code, vnfd_resp.text))
        # 3. collect and upload NSDs
        nsds = self._get_package_content_of_type(
            napdr, wd, "application/vnd.5gtango.nsd")
        for nsd in nsds:
            nsd_resp = self._post_ns_descriptors(nsd)
            if nsd_resp.status_code != 201:
                raise StorageBackendUploadException(
                    "tng-cat-be: could not upload NS descriptor: ({}) {}"
                    .format(nsd_resp.status_code, nsd_resp.text))
        # 4. collect and upload TESTDs
        tstds = self._get_package_content_of_type(
            napdr, wd, "application/vnd.5gtango.tstd")
        for tstd in tstds:
            tstd_resp = self._post_test_descriptors(tstd)
            if tstd_resp.status_code != 201:
                raise StorageBackendUploadException(
                    "tng-cat-be: could not upload test descriptor: ({}) {}"
                    .format(tstd_resp.status_code, tstd_resp.text))
        # 5. collect and upload all arbitrary other files
        generic_files = self._get_package_content_not_of_type(
            napdr, wd, "application/vnd.5gtango")
        generic_files_uuids = dict()
        for gf in generic_files:
            gf_resp = self._post_generic_file_to_catalog("/files", gf)
            if gf_resp.status_code != 201:
                raise StorageBackendUploadException(
                    "tng-cat-be: could not upload generic file ({}): ({}) {}"
                    .format(gf, gf_resp.status_code, gf_resp.text))
            gf_clean = os.path.basename(gf)
            generic_files_uuids[gf_clean] = gf_resp.json().get("uuid")
            LOG.debug("Generic file '{}' stored under UUID: {}".format(
                gf_clean, generic_files_uuids[gf_clean]))
        # 6. upload Package file *.tgo and get catalog UUID
        pkg_resp = self._post_pkg_file_to_catalog(
            "/tgo-packages", pkg_file)
        if pkg_resp.status_code != 201:
            raise StorageBackendUploadException(
                "tng-cat-be: could not upload package. Response: {}"
                .format(pkg_resp.status_code))
        pkg_file_uuid = pkg_resp.json().get("uuid")
        # pkg_file_url = "{}/tgo-packages/{}".format(self.cat_url, pkg_uuid)
        # 7. upload mata data mapping (catalog support)
        # generate
        cat_metadata = self._build_catalog_metadata(
            napdr, nsds, vnfds, tstds, generic_files_uuids, pkg_file_uuid)
        # upload
        map_resp = self._post_json_data_to_catalog(
            "/tgo-packages/mappings", cat_metadata)
        if map_resp.status_code != 201 and map_resp.status_code != 200:
            raise StorageBackendUploadException(
                "tng-cat-be: could not upload cat. mapping. Response: ({}) {}"
                .format(map_resp.status_code, map_resp.text))
        # updated/annotated napdr
        napdr.metadata["_storage_uuid"] = pkg_uuid
        napdr.metadata["_storage_location"] = pkg_url
        napdr.metadata["_storage_pkg_file"] = pkg_file_uuid
        napdr.metadata["_storage_generic_files"] = generic_files_uuids
        LOG.info("tng-cat-be: tangoCatalogBackend stored: {}".format(pkg_url))
        return napdr
