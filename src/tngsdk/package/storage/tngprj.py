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
import shutil
import yaml
from tngsdk.package.storage import BaseStorageBackend
from tngsdk.package.logger import TangoLogger
from tngsdk.package.helper import extract_zip_file_to_temp

LOG = TangoLogger.getLogger(__name__)


# where to put the artifacts in the project structure
BASE_ARTIFACT_DIR = "sources/"
PROJECT_MANIFEST_NAME = "project.yml"


class TangoProjectFilesystemBackend(BaseStorageBackend):

    def __init__(self, args):
        self.args = args
        # if no output folder is given use CWD
        if self.args.output is None:
            self.args.output = os.getcwd()
        LOG.info(
            "tng-prj-be: Initialized TangoProjectFilesystemBackend({})"
            .format(self.args.output))

    def remove_Definitions(self, s):
        s = s.strip().strip(os.sep)
        s = s.split(os.sep)
        if "Definitions" in s:
            s.remove("Definitions")
        return os.path.join(*s)

    def _makedirs(self, d):
        if not os.path.exists(d):
            os.makedirs(d)
            LOG.debug("tng-prj-be: Created directories: {}".format(d))

    def _create_project_tree(self, pd):
        """
        Creates the empty dir. tree of a 5GTANGO project
        This might be changed if tng-sdk-project evolves.
        """
        self._makedirs(os.path.join(pd, "sources"))
        self._makedirs(os.path.join(pd, "dependencies"))
        self._makedirs(os.path.join(pd, "deployment"))

    def _create_project_manifest(self, napdr):
        """
        Create a project manifest (project.yml) based
        on the information from the NAPDR.
        """
        # base structure
        pm = {
            "descriptor_extension": "yml",
            "version": "0.5",
            "package": {
                "vendor": napdr.vendor,
                "name": napdr.name,
                "version": napdr.version,
                "maintainer": napdr.maintainer,
                "description": napdr.description
            },
            "files": []
        }
        self.sources = []
        self.destinations = []
        # add entries for artifacts
        for pc in napdr.package_content:
            tmp = pc.copy()
            # remove checksum information
            del tmp["algorithm"]
            del tmp["hash"]
            # re-write path (source -> path)
            tmp["path"] = os.path.join(self.remove_Definitions(tmp["source"]))
            self.sources.append(tmp["source"])
            self.destinations.append(tmp["path"])
            del tmp["source"]
            # re-write content type (content-type -> type)
            tmp["type"] = tmp["content-type"]
            del tmp["content-type"]
            # add to pm
            pm.get("files").append(tmp)
        return pm

    def extract_subfolder_zips(self, pm, pd):
        for file in pm["files"]:
            if file["type"] == 'application/vnd.folder.compressed.zip':
                src = os.path.join(pd, file["path"])
                new_path = os.path.splitext(file["path"])[0]
                dest = os.path.join(pd, new_path)
                extract_zip_file_to_temp(src, dest)
                file["path"] = new_path
                os.remove(src)

    def _copy_package_content_to_project(self, napdr, wd, pd):
        """
        Copies all unpackaged artifacts to project directory.
        """
        for src, dst in zip(self.sources, self.destinations):
            s = os.path.join(wd, src)
            d = os.path.join(pd, dst)
            self._makedirs(os.path.dirname(d))
            LOG.debug("Copying {}\n\t to {}".format(s, d))
            shutil.copyfile(s, d)

    def store(self, napdr, wd, pkg_file, output=None):
        """
        Turns the given unpacked package to a
        5GTANGO SDK project in the local filesystem.
        """
        # 1. create project manifest from NAPDR
        pm = self._create_project_manifest(napdr)
        LOG.debug("tng-prj-be: Generated project manifest: {}"
                  .format(pm))
        # 2. create project directory
        if output is None:
            output = self.args.output
        if pkg_file is None:
            pkg_file = "tng-pkg.tgo"
        pd = os.path.join(
            output,
            os.path.splitext(os.path.basename(pkg_file))[0])
        self._makedirs(pd)
        # 3. create empty project tree
        self._create_project_tree(pd)
        # 4. copy artifacts from package to project
        self._copy_package_content_to_project(napdr, wd, pd)
        # 5. extract subfolder zips if there are any
        self.extract_subfolder_zips(pm, pd)
        # 6. write project.yml
        with open(os.path.join(pd, PROJECT_MANIFEST_NAME), "w") as f:
            yaml.dump(pm, f, default_flow_style=False)
        LOG.info("tng-prj-be: Created 5GTANGO SDK project: {}".format(pd))
        # annotate napdr
        napdr.metadata["_storage_location"] = pd
        return napdr
