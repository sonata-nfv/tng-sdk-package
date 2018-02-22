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
from flask_restplus import Resource, Api
from werkzeug.contrib.fixers import ProxyFix
from tngsdk.package.packager import PM


LOG = logging.getLogger(os.path.basename(__file__))


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app,
          version="1.0",
          title='5GTANGO tng-package API',
          description="5GTANGO tng-package REST API " +
          "to package/unpacke NFV packages.")


def serve_forever(args, debug=True):
    # TODO replace this with WSGIServer for better performance
    app.run(host=args.service_address,
            port=args.service_port,
            debug=debug)


@api.route("/package")
class Package(Resource):
    """
    Endpoint for unpackaging.
    """
    def post(self):
        LOG.warning("endpoint not implemented")
        p = PM.new_packager()
        p.unpackage()
        return "not implemented", 501


@api.route("/project")
class Project(Resource):
    """
    Endpoint for package creation.
    """
    def post(self):
        LOG.warning("endpoint not implemented")
        p = PM.new_packager()
        p.package()
        return "not implemented", 501
