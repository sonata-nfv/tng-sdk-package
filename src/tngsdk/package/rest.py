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
import json
from flask import Flask, Blueprint
from flask_restplus import Resource, Api, Namespace, fields
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.datastructures import FileStorage
import requests
from requests.exceptions import RequestException
from tngsdk.package.packager import PM


LOG = logging.getLogger(os.path.basename(__file__))


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
blueprint = Blueprint('api', __name__, url_prefix="/api")
api_v1 = Namespace("v1", description="tng-package API v1")
api = Api(blueprint,
          version="0.1",
          title='5GTANGO tng-package API',
          description="5GTANGO tng-package REST API " +
          "to package/unpacke NFV packages.")
app.register_blueprint(blueprint)
api.add_namespace(api_v1)


def dump_swagger(args):
    # TODO replace this with the URL of a real tng-package service
    app.config.update(SERVER_NAME="tng-package.5gtango.eu")
    with app.app_context():
        with open(args.dump_swagger_path, "w") as f:
            # TODO dump in nice formatting
            f.write(json.dumps(api.__schema__))


def serve_forever(args, debug=True):
    """
    Start REST API server. Blocks.
    """
    # TODO replace this with WSGIServer for better performance
    app.run(host=args.service_address,
            port=args.service_port,
            debug=debug)


packages_parser = api_v1.parser()
packages_parser.add_argument("package",
                             location="files",
                             type=FileStorage,
                             required=True,
                             help="Uploaded package file")
packages_parser.add_argument("callback_url",
                             location="form",
                             required=False,
                             default=None,
                             help="URL called after unpackaging (optional)")
packages_parser.add_argument("layer",
                             location="form",
                             required=False,
                             default=None,
                             help="Layer tag to be unpackaged (optional)")
packages_parser.add_argument("format",
                             location="form",
                             required=False,
                             default="eu.5gtango",
                             help="Package format (optional)")

packages_model = api_v1.model("Packages", {
    "package_process_uuid": fields.String(
        description="UUID of started unpackaging process.",
        required=True
    )
})


def _do_callback_request(url, body):
    try:
        base_body = {
            "event_name": "onPackageChangeEvent",
            "package_id": "foobar",  # TODO replace with None
            "package_location": "foobar",  # TODO replace with None
            "package_metadata": None
        }
        # apply parameters
        base_body.update(body)
        r = requests.post(url, json=base_body)
    except RequestException as e:
        LOG.error("Callback error: {}".format(e))
        return -1
    return r.status_code


def on_unpackaging_done(packager):
    """
    Callback function for packaging procedure.
    """
    LOG.info("DONE: Unpackaging using {}".format(packager))
    if packager.args is None or "callback_url" not in packager.args:
        return
    c_url = packager.args.callback_url
    LOG.info("Callback: POST to '{}'".format(c_url))
    # perform callback request
    r_code = _do_callback_request(c_url, {})
    LOG.info("DONE: Status {}".format(r_code))


def on_packaging_done(packager):
    """
    Callback function for packaging procedure.
    """
    LOG.info("DONE: Packaging using {}".format(packager))
    if packager.args is None or "callback_url" not in packager.args:
        return
    c_url = packager.args.callback_url
    LOG.info("Callback: POST to '{}'".format(c_url))
    # perform callback request
    r_code = _do_callback_request(c_url, {})
    LOG.info("DONE: Status {}".format(r_code))


@api_v1.route("/packages")
class Package(Resource):
    """
    Endpoint for unpackaging.
    """
    @api_v1.expect(packages_parser)
    @api_v1.marshal_with(packages_model)
    @api_v1.response(200, "Successfully started unpackaging.")
    @api_v1.response(400, "Bad package: Could not unpackage given package.")
    def post(self, **kwargs):
        args = packages_parser.parse_args()
        # TODO replace package data with local path to file
        print(args["package"])
        print(args["callback_url"])
        p = PM.new_packager(args)  # TODO pass args to packager
        p.unpackage(callback_func=on_unpackaging_done)
        return {"package_process_uuid": p.uuid}


@api_v1.route("/projects")
class Project(Resource):
    """
    Endpoint for package creation.
    """
    def post(self):
        LOG.warning("endpoint not implemented")
        p = PM.new_packager(None)
        p.package(callback_func=on_packaging_done)
        return "not implemented", 501
