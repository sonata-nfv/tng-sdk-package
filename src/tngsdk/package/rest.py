#  Copyright (c) 2015 SONATA-NFV, 5GTANGO, UBIWHERE, Paderborn University
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
from flask import Flask
from flask_restful import Resource, Api


LOG = logging.getLogger(os.path.basename(__file__))


class RestApi(object):

    def __init__(self, args, packager):
        self._args = args
        self._p = packager
        self._app = Flask(__name__)
        self._api = Api(self._app)
        self._define_routes()

    def _define_routes(self):
        self._api.add_resource(Package,
                               "/package",
                               resource_class_kwargs={"packager": self._p})
        self._api.add_resource(Project,
                               "/project",
                               resource_class_kwargs={"packager": self._p})

    def serve(self, debug=True):
        # TODO replace this with WSGIServer for better performance
        self._app.run(host=self._args.service_address,
                      port=self._args.service_port,
                      debug=debug)


class Package(Resource):
    """
    Endpoint for unpackaging.
    """

    def __init__(self, packager):
        self._p = packager

    def post(self):
        LOG.warning("endpoint not implemented")
        self._p.package()
        return "not implemented", 501


class Project(Resource):
    """
    Endpoint for package creation.
    """

    def __init__(self, packager):
        self._p = packager

    def post(self):
        LOG.warning("endpoint not implemented")
        self._p.unpackage()
        return "not implemented", 501
