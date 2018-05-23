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
        cd_str = "attachment; filename={}".format(os.path.basename(path))
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
            return None
        return res

    def _parse_cat_yaml_response(self, response):
        try:
            return yaml.load(response.text)
        except BaseException as e:
            LOG.exception()
            raise StorageBackendResponseException(
                "tng-cat-be: could not parse tng-cat resp.: '{}'"
                .format(response.text))
        return dict()

    def _annotate_napdr_with_cat_uuids(
            self, napdr, uuids):
        """
        Add UUIDs from catalog to package_content entries in
        NAPDR data structure.
        """
        for pc in napdr.package_content:
            uuid = uuids.get(pc.get("source"))
            if uuid is not None:
                pc["uuid"] = uuid

    def _annotate_napdr_with_id_triples(self, napdr, wd):
        """
        Add vendor.name.version triples to the package_content
        entries of the NAPDR to support the catalogs.
        """
        for pc in napdr.package_content:
            triple = self._get_id_triple_from_descriptor_file(
                os.path.join(wd, pc.get("source")))
            if triple is not None:
                # annotate
                pc["id"] = triple

    def _annotate_napdr_with_pkg_file(
            self, napdr, pkg_file_uuid, pkg_file):
        """
        Add UUID of uploaded package file to NAPDR.
        """
        napdr.package_file_uuid = pkg_file_uuid
        napdr.package_file_name = os.path.basename(pkg_file)

    def store(self, napdr, wd, pkg_file):
        """
        Stores the pushes given package and its files to the
        5GTANGO catalog.
        :param napdr: package descriptor record from unpacking
        :param wd: working directory with package contents
        :param pkg_file: path to the original package file
        :return napdr: updated/annotated napdr
        """
        # 1. collect and upload VNFDs
        vnfds = self._get_package_content_of_type(
            napdr, wd, "application/vnd.5gtango.vnfd")
        file_catalog_uuids = dict()
        for vnfd in vnfds:
            vnfd_resp = self._post_vnf_descriptors(vnfd)
            if vnfd_resp.status_code != 201:
                raise StorageBackendUploadException(
                    "tng-cat-be: could not upload VNF descriptor: ({}) {}"
                    .format(vnfd_resp.status_code, vnfd_resp.text))
            vnfd_uuid = self._parse_cat_yaml_response(vnfd_resp).get("uuid")
            if vnfd_uuid is None:
                raise StorageBackendUploadException(
                    "tng-cat-be: could not retrieve UUID from tng-cat.")
            file_catalog_uuids[vnfd.replace(wd, "")] = vnfd_uuid
        # 2. collect and upload NSDs
        nsds = self._get_package_content_of_type(
            napdr, wd, "application/vnd.5gtango.nsd")
        for nsd in nsds:
            nsd_resp = self._post_ns_descriptors(nsd)
            if nsd_resp.status_code != 201:
                raise StorageBackendUploadException(
                    "tng-cat-be: could not upload NS descriptor: ({}) {}"
                    .format(nsd_resp.status_code, nsd_resp.text))
            nsd_uuid = self._parse_cat_yaml_response(nsd_resp).get("uuid")
            if nsd_uuid is None:
                raise StorageBackendUploadException(
                    "tng-cat-be: could not retrieve UUID from tng-cat.")
            file_catalog_uuids[nsd.replace(wd, "")] = nsd_uuid
        # 3. collect and upload TESTDs
        tstds = self._get_package_content_of_type(
            napdr, wd, "application/vnd.5gtango.tstd")
        for tstd in tstds:
            tstd_resp = self._post_test_descriptors(tstd)
            if tstd_resp.status_code != 201:
                raise StorageBackendUploadException(
                    "tng-cat-be: could not upload test descriptor: ({}) {}"
                    .format(tstd_resp.status_code, tstd_resp.text))
            tstd_uuid = self._parse_cat_yaml_response(tstd_resp).get("uuid")
            if tstd_uuid is None:
                raise StorageBackendUploadException(
                    "tng-cat-be: could not retrieve UUID from tng-cat.")
            file_catalog_uuids[tstd.replace(wd, "")] = tstd_uuid
        # 4. collect and upload all arbitrary other files
        generic_files = self._get_package_content_not_of_type(
            napdr, wd, "application/vnd.5gtango")
        gf_filenames_uuids = dict()
        for gf in generic_files:
            gf_resp = self._post_generic_file_to_catalog("/files", gf)
            if gf_resp.status_code != 201:
                raise StorageBackendUploadException(
                    "tng-cat-be: could not upload generic file ({}): ({}) {}"
                    .format(gf, gf_resp.status_code, gf_resp.text))
            gf_clean = os.path.basename(gf)
            gf_filenames_uuids[gf_clean] = gf_resp.json().get("uuid")
            file_catalog_uuids[gf.replace(wd, "")] = gf_resp.json().get("uuid")
            LOG.debug("Generic file '{}' stored under UUID: {}".format(
                gf_clean, gf_filenames_uuids[gf_clean]))
        # 5. upload Package file *.tgo and get catalog UUID
        pkg_resp = self._post_pkg_file_to_catalog(
            "/tgo-packages", pkg_file)
        if pkg_resp.status_code != 201:
            raise StorageBackendUploadException(
                "tng-cat-be: could not upload package. Response: {}"
                .format(pkg_resp.status_code))
        pkg_file_uuid = pkg_resp.json().get("uuid")
        # 6. upload package descriptor
        # annotate package descriptor with catalog locations
        self._annotate_napdr_with_cat_uuids(napdr, file_catalog_uuids)
        self._annotate_napdr_with_id_triples(napdr, wd)
        self._annotate_napdr_with_pkg_file(napdr, pkg_file_uuid, pkg_file)
        pkg_resp = self._post_package_descriptor(napdr)
        if pkg_resp.status_code != 201:
            raise StorageBackendUploadException(
                "tng-cat-be: could not upload package descriptor: ({}) {}"
                .format(pkg_resp.status_code, pkg_resp.text))
        pkg_uuid = self._parse_cat_yaml_response(pkg_resp).get("uuid")
        if pkg_uuid is None:
            raise StorageBackendUploadException(
                "tng-cat-be: could not retrieve package UUID from tng-cat.")
        LOG.info("tng-cat-ne: received PKG UUID from catalog: {}"
                 .format(pkg_uuid))
        pkg_url = "{}/packages/{}".format(self.cat_url, pkg_uuid)
        # updated/annotated napdr
        napdr.metadata["_storage_uuid"] = pkg_uuid
        napdr.metadata["_storage_location"] = pkg_url
        LOG.info("tng-cat-be: tangoCatalogBackend stored: {}".format(pkg_url))
        return napdr
