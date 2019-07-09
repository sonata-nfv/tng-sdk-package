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
import os
import time
import json
import tempfile
import subprocess
from flask import Flask, Blueprint, send_from_directory, url_for
from flask_restplus import Resource, Api, Namespace
from flask_restplus import fields, inputs
from werkzeug.contrib.fixers import ProxyFix
from werkzeug.datastructures import FileStorage
import requests
from requests.exceptions import RequestException
from tngsdk.package.packager import PM
from tngsdk.package.helper import extract_zip_file_to_temp
from tngsdk.package.storage.tngcat import TangoCatalogBackend
from tngsdk.package.storage.tngprj import TangoProjectFilesystemBackend
from tngsdk.package.storage.osmnbi import OsmNbiBackend
from tngsdk.package.logger import TangoLogger


PACKAGES_SUBDIR = "packages"


LOG = TangoLogger.getLogger(__name__)


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
    app.cliargs = args
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
                             store_missing=True,
                             help="URL called after unpackaging (optional)")
packages_parser.add_argument("username",
                             location="form",
                             required=False,
                             default=None,
                             store_missing=True,
                             help="Username of the uploader (optional)")
packages_parser.add_argument("layer",
                             location="form",
                             required=False,
                             default=None,
                             store_missing=True,
                             help="Layer tag to be unpackaged (optional)")
packages_parser.add_argument("format",
                             location="form",
                             required=False,
                             default=None,
                             store_missing=True,
                             help="Package format (optional)")
packages_parser.add_argument("skip_store",
                             location="form",
                             type=inputs.boolean,
                             required=False,
                             default=None,
                             store_missing=True,
                             help="""Skip catalog upload
                                    of contents (optional)""")
packages_parser.add_argument("skip_validation",
                             location="form",
                             type=inputs.boolean,
                             required=False,
                             default=None,
                             store_missing=True,
                             help="Skip service validation (optional)")
packages_parser.add_argument("validation_level",
                             location="form",
                             type=str,
                             choices=['s', 'syntax', 'i', 'integrity',
                                      't', 'topology', 'skip'],
                             required=False,
                             default=None,
                             store_missing=True,
                             help="""Set validation level.
                              Possible values:
                               's' or 'syntax',
                               'i' or 'integrity',
                               't' or 'topology' ,
                               'skip'""")
packages_parser.add_argument("workspace",
                             location="form",
                             store_missing=True,
                             default=None,
                             help="Workspace (ignored for now)")
packages_parser.add_argument("output",
                             location="form",
                             store_missing=True,
                             default=None,
                             help="Output (ignored for now)")
packages_parser.add_argument("offline",
                             required=False,
                             default=None,
                             store_missing=True,
                             location="form",
                             help="Offline")
packages_parser.add_argument("no_checksums",
                             required=False,
                             default=None,
                             store_missing=True,
                             location="form",
                             help="Do not validate artifact checksums.")

packages_status_item_get_return_model = api_v1.model(
    "PackagesStatusItemGetReturn",
    {"package_process_uuid": fields.String(
        description="UUID of started unpackaging process.",
        required=True),
     "status": fields.String(
        description="Status of the unpacking process:"
        + " waiting|runnig|failed|done",
        required=True),
     "error_msg": fields.String(
        description="More detailed error message.",
         required=False), }
)

packages_status_list_get_return_model = api_v1.model(
    "PackagesStatusListGetReturn",
    {"package_processes": fields.List(
        fields.Nested(packages_status_item_get_return_model)), }
)


projects_parser = api_v1.parser()
projects_parser.add_argument("project",
                             location="files",
                             type=FileStorage,
                             required=True,
                             help="Uploaded project archive")
projects_parser.add_argument("callback_url",
                             location="form",
                             required=False,
                             help="URL called after unpackaging (optional)",
                             store_missing=True,
                             default=None)
projects_parser.add_argument("username",
                             location="form",
                             required=False,
                             default=None,
                             help="Username of the uploader (optional)",
                             store_missing=True)
projects_parser.add_argument("format",
                             dest="pkg_format",
                             location="form",
                             required=False,
                             default=None,
                             help="Package format (optional)",
                             store_missing=True)
projects_parser.add_argument("skip_store",
                             location="form",
                             type=inputs.boolean,
                             required=False,
                             default=None,
                             help="""Skip catalog upload
                                    of contents (ignored)""",
                             store_missing=True)
projects_parser.add_argument("skip_validation",
                             location="form",
                             type=inputs.boolean,
                             required=False,
                             default=None,
                             help="Skip service validation (optional)",
                             store_missing=True)
projects_parser.add_argument("validation_level",
                             location="form",
                             type=str,
                             choices=['s', 'syntax', 'i', 'integrity',
                                      't', 'topology', 'skip'],
                             required=False,
                             default=None,
                             help="""Set validation level.
                              Possible values:
                               's' or 'syntax',
                               'i' or 'integrity',
                               't' or 'topology' ,
                               'skip'""",
                             store_missing=True)
projects_parser.add_argument("output",
                             type=str,
                             location="form",
                             required=False,
                             help="Output",
                             default=None,
                             store_missing=True)
projects_parser.add_argument("workspace",
                             required=False,
                             default=None,
                             store_missing=True,
                             location="form",
                             help="Workspace (ignored for now)")
projects_parser.add_argument("offline",
                             required=False,
                             default=None,
                             store_missing=True,
                             location="form",
                             help="Offline")
projects_parser.add_argument("no_checksums",
                             required=False,
                             default=None,
                             store_missing=True,
                             location="form",
                             help="Do not validate artifact checksums.")
projects_parser.add_argument("no_subfolder_compression",
                             help="""Ignore type:
                             application/vnd.folder.compressed.zip""",
                             required=False,
                             default=None,
                             store_missing=True,
                             type=inputs.boolean,
                             dest="no_subfolder_compression",
                             location="form")


ping_get_return_model = api_v1.model("PingGetReturn", {
    "alive_since": fields.String(
        description="system uptime",
        required=True),
})


def _do_callback_request(url, body):
    try:
        base_body = {
            "event_name": "onPackageChangeEvent",
            "package_id": None,
            "package_location": None,
            "package_metadata": None,
            "package_process_status": None,
            "package_process_uuid": None
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
    LOG.info("{}: Unpackaging using {} error: {}".format(
        packager.status.upper(), packager, packager.result.error))
    if packager.args is None or "callback_url" not in packager.args:
        return
    c_url = packager.args.get("callback_url")
    if c_url is None:
        LOG.warning("'callback_url' is None. Skipping callback.")
        return
    LOG.info("Callback: POST to '{}'".format(c_url))
    # build callback payload
    pl = {"package_id": packager.result.metadata.get("_storage_uuid"),
          "package_location": packager.result.metadata.get(
              "_storage_location"),
          "package_metadata": packager.result.to_dict(),
          "package_process_status": str(packager.status),
          "package_process_uuid": str(packager.uuid)}
    # perform callback request
    r_code = _do_callback_request(c_url, pl)
    LOG.info("DONE: Callback response status {}".format(r_code))
    return r_code


def on_packaging_done(packager):
    """
    Callback function for packaging procedure.
    """
    LOG.info("DONE: Packaging using {}".format(packager))
    if packager.args is None or "callback_url" not in packager.args:
        return
    c_url = packager.args.get("callback_url")

    if c_url is None:
        LOG.warning("'callback_url' is None. Skipping callback.")
        return
    LOG.info("Callback: POST to '{}'".format(c_url))
    # perform callback request
    pl = packaging_done_answer(packager)
    r_code = _do_callback_request(c_url, pl)
    LOG.info("DONE: Status {}".format(r_code))
    return r_code


def packaging_done_answer(packager):
    """
    Constitutes an answer dictionary.
    Args:
        packager:

    Returns: dictionary

    """
    package_location = packager.result.metadata.get("_storage_location")
    package_download_link = ("/api/v1/projects/" +
                             os.path.basename(package_location))
    pl = {"package_id": packager.result.metadata.get("_storage_uuid"),
          "package_location": package_location,
          "package_metadata": packager.result.to_dict(),
          "package_process_status": str(packager.status),
          "package_process_uuid": str(packager.uuid),
          "package_download_link": package_download_link}
    return pl


def _write_to_temp_file(package_data):
    # create a temp directory
    path_dest = tempfile.mkdtemp()
    path = os.path.join(path_dest, os.path.basename(package_data.filename))
    package_data.save(path)
    LOG.debug("Written uploaded package file to {}".format(path))
    LOG.debug("-- File size {} byte".format(os.path.getsize(path)))
    return path


@api_v1.route("/packages")
class Packages(Resource):
    """
    Endpoint for unpackaging.
    """
    @api_v1.expect(packages_parser)
    @api_v1.marshal_with(packages_status_item_get_return_model)
    @api_v1.response(200, "Successfully started unpackaging.")
    @api_v1.response(400, "Bad package: Could not unpackage given package.")
    def post(self, **kwargs):
        t_start = time.time()
        args = packages_parser.parse_args()
        LOG.info("POST to /packages w. args: {}".format(args),
                 extra={"start_stop": "START"})
        if args.package.filename is None:
            LOG.warning("Posted package filename was None.")
            args.package.filename = "temp_pkg.tgo"
        temppkg_path = _write_to_temp_file(args.package)
        args.package = None
        args.unpackage = temppkg_path
        # pass CLI args to REST args
        if app.cliargs is not None:
            cliargs = vars(app.cliargs)
            for cliarg in cliargs:
                if cliarg not in args or args[cliarg] is None:
                    args[cliarg] = cliargs[cliarg]

        # select and instantiate storage backend
        sb = None
        if (not args.store_skip  # from CLI
                and not args.skip_store  # from request
                and not os.environ.get("STORE_SKIP", "False") == "True"):
            sb_env = os.environ.get("STORE_BACKEND", "TangoCatalogBackend")
            if sb_env == "TangoCatalogBackend":
                sb = TangoCatalogBackend(args)
            elif sb_env == "TangoProjectFilesystemBackend":
                sb = TangoProjectFilesystemBackend(args)
            elif sb_env == "OsmNbiBackend":
                sb = OsmNbiBackend(args)
            else:
                LOG.warning("Unknown storage backend: {}."
                            .format(sb_env))
        # instantiate packager
        p = PM.new_packager(args, storage_backend=sb)
        try:
            p.unpackage(callback_func=on_unpackaging_done)
        except BaseException as e:
            LOG.exception("Unpackaging error: {}".format(e))
        LOG.info("POST to /packages done",
                 extra={"start_stop": "STOP", "status": p.status,
                        "time_elapsed": str(time.time()-t_start)})
        return {"package_process_uuid": str(p.uuid),
                "status": p.status,
                "error_msg": p.error_msg}


@api_v1.route("/packages/status/<string:package_process_uuid>")
class PackagesStatusItem(Resource):

    @api_v1.marshal_with(packages_status_item_get_return_model)
    @api_v1.response(200, "OK")
    @api_v1.response(404, "Package process not found.")
    def get(self, package_process_uuid):
        LOG.info("GET to /packages/status/ w. args: {}".format(
                    package_process_uuid),
                 extra={"start_stop": "START"})
        p = PM.get_packager(package_process_uuid)
        if p is None:
            LOG.warning("GET to /packages/status/ done",
                        extra={"start_stop": "STOP", "status": 404})
            return {"error_msg": "Package process not found: {}".format(
                package_process_uuid)}, 404
        LOG.info("GET to /packages/status/ done",
                 extra={"start_stop": "STOP", "status": p.status})
        return {"package_process_uuid": str(p.uuid),
                "status": p.status,
                "error_msg": p.error_msg}


@api_v1.route("/packages/status")
class PackagesStatusList(Resource):

    @api_v1.marshal_with(packages_status_list_get_return_model)
    @api_v1.response(200, "OK")
    def get(self):
        LOG.info("GET to /packages/status",
                 extra={"start_stop": "START"})
        r = list()
        for p in PM.packager_list:
            r.append({"package_process_uuid": str(p.uuid),
                      "status": p.status,
                      "error_msg": p.error_msg})
        LOG.info("GET to /packages/status done",
                 extra={"start_stop": "STOP", "status": "200"})
        return {"package_processes": r}


@api_v1.route("/projects")
class Projects(Resource):
    """
    Endpoint for package creation.
    """
    def get(self):
        """
        Get a list created packages.
        Returns: List of dictionaries: [{'package_name: <name>,
                                        'package_download_link': <link>}, ..]

        """
        packages = os.listdir(PACKAGES_SUBDIR)
        return [{"package_name": name,
                 "package_download_link": url_for("api.v1_project_download",
                                                  filename=name,
                                                  _external=True)}
                for name in packages]

    @api_v1.expect(projects_parser)
    @api_v1.response(200, "Successfully started packaging.")
    @api_v1.response(400, "Bad project: Could not package given project.")
    def post(self):
        args = projects_parser.parse_args()
        LOG.info("POST to /projects w. args: {}".format(args),
                 extra={"start_stop": "START"})
        tempproject_path = _write_to_temp_file(args.project)
        tempproject_path = extract_zip_file_to_temp(tempproject_path)
        args.package = (
            os.path.join(tempproject_path,
                         os.path.splitext(args.project.filename)[0]))
        args.package = os.path.split(args.package)[0]
        args.unpackage = None

        # pass CLI args to REST args
        if not os.path.exists(PACKAGES_SUBDIR):
            os.makedirs(PACKAGES_SUBDIR)

        if app.cliargs is not None:
            cliargs = vars(app.cliargs)
            for key in cliargs:
                if key not in args or args[key] is None:
                    args[key] = cliargs[key]
        if args.output is None:
            args.output = PACKAGES_SUBDIR
        else:
            args.output = os.path.join(PACKAGES_SUBDIR, args.output)
        p = PM.new_packager(args, pkg_format=args.pkg_format)
        p.package(callback_func=on_packaging_done)
        LOG.info("POST to /projects done.",
                 extra={"start_stop": "START", "status": 501})
        return {"package_process_uuid": str(p.uuid),
                "status": p.status,
                "error_msg": p.error_msg}


@api_v1.route("/projects/<string:filename>")
class Project_download(Resource):
    """
    Endpoint for download created package.
    """
    @api_v1.expect(projects_parser)
    def get(self, filename):
        return send_from_directory(
            os.path.join(os.getcwd(), PACKAGES_SUBDIR),
            filename, as_attachment=True)


@api_v1.route("/pings")
class Ping(Resource):

    @api_v1.marshal_with(ping_get_return_model)
    @api_v1.response(200, "OK")
    def get(self):
        ut = None
        try:
            ut = str(subprocess.check_output("uptime")).strip()
        except BaseException as e:
            LOG.warning(str(e))
        return {"alive_since": ut}
