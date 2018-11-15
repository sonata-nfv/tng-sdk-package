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
import argparse
import os
import sys
from tngsdk.package.packager import PM
from tngsdk.package.storage.tngcat import TangoCatalogBackend
from tngsdk.package.storage.tngprj import TangoProjectFilesystemBackend
from tngsdk.package.storage.osmnbi import OsmNbiBackend
from tngsdk.package.logger import TangoLogger


LOG = TangoLogger.getLogger(__name__)


def dispatch(args):
    # trigger pack/unpack
    if args.package:
        # instantiate packager
        p = PM.new_packager(args, pkg_format=args.pkg_format)
        p.package()
        LOG.debug("Packager result: {}".format(p.result))
        display_result_package(args, p.result)
    elif args.unpackage:
        # select and instantiate storage backend
        # default in CLI mode: TangoProjectFilesystemBackend
        sb = None
        if (not args.store_skip
                and not os.environ.get("STORE_SKIP", "False") == "True"):
            sb_env = args.store_backend
            if sb_env is None:
                sb_env = os.environ.get(
                    "STORE_BACKEND", "TangoProjectFilesystemBackend")
            if sb_env == "TangoCatalogBackend":
                sb = TangoCatalogBackend(args)
            elif sb_env == "TangoProjectFilesystemBackend":
                sb = TangoProjectFilesystemBackend(args)
            elif sb_env == "OsmNbiBackend":
                sb = OsmNbiBackend(args)
            else:
                LOG.warning("Unknown storage backend: {}. Stop."
                            .format(sb_env))
                exit(1)
        # instantiate packager
        p = PM.new_packager(args, storage_backend=sb)
        p.unpackage()
        LOG.debug("Packager result: {}".format(p.result))
        display_result_unpackage(args, p.result)
    else:
        print("Missing arguments. Type tng-package -h.")
        exit(1)
    return p.result


def display_result_unpackage(args, r):
    if args.quiet:
        return
    print("=" * 79)
    print("U N P A C K A G I N G   R E P O R T")
    print("=" * 79)
    print("Unpackaged:  {}".format(args.unpackage))
    if r.error is None:
        print("Project:     {}.{}.{}"
              .format(r.vendor, r.name, r.version))
        print("Artifacts:   {}".format(len(r.package_content)))
        print("Output:      {}".format(r.metadata.get("_storage_location")))
        print("Error:       {}".format(r.error))
        print("Result:      Success.")
    else:
        print("Error:       {}".format(r.error))
        print("Result:      Failed.")
    print("=" * 79)


def display_result_package(args, r):
    if args.quiet:
        return
    print("=" * 79)
    print("P A C K A G I N G   R E P O R T")
    print("=" * 79)
    print("Packaged:    {}".format(args.package))
    if r.error is None:
        print("Project:     {}.{}.{}"
              .format(r.vendor, r.name, r.version))
        print("Artifacts:   {}".format(len(r.package_content)))
        print("Output:      {}".format(r.metadata.get("_storage_location")))
        print("Error:       {}".format(r.error))
        print("Result:      Success.")
    else:
        print("Error:       {}".format(r.error))
        print("Result:      Failed.")
    print("=" * 79)


def parse_args(input_args=None):
    parser = argparse.ArgumentParser(
        description="5GTANGO SDK packager")

    # input/output
    parser.add_argument(
        "-p",
        "--package",
        help="Create package from given project.",
        required=False,
        default=None,
        dest="package")

    parser.add_argument(
        "-u",
        "--unpackage",
        help="Unpackage given package.",
        required=False,
        default=None,
        dest="unpackage")

    parser.add_argument(
        "-o",
        "--output",
        help="Path to outputs (optional)",
        required=False,
        default=None,
        dest="output")

    parser.add_argument(
        "--format",
        help="Package format [eu.5gtango|eu.etsi|eu.etsi.osm]."
        + "\nDefault: eu.5gtango",
        required=False,
        default="eu.5gtango",
        dest="pkg_format")

    parser.add_argument(
        "-v",
        "--verbose",
        help="Output debug messages.",
        required=False,
        default=False,
        dest="verbose",
        action="store_true")

    parser.add_argument(
        "--loglevel",
        help="Directly specify loglevel. Default: INFO",
        required=False,
        default=None,
        dest="log_level")

    parser.add_argument(
        "--logjson",
        help="Use 5GTANGO JSON-based logging. Default: False",
        required=False,
        default=False,
        dest="logjson",
        action="store_true")

    parser.add_argument(
        "-q",
        "--quiet",
        help="Do not print packaging info.",
        required=False,
        default=False,
        dest="quiet",
        action="store_true")

    # packaging/unpackaging process
    parser.add_argument(
        "--ignore-checksums",
        help="Do not validate artifact checksums.",
        required=False,
        default=False,
        dest="no_checksums",
        action="store_true")

    parser.add_argument(
        "--no-autoversion",
        help="Auto. increase package version field.",
        required=False,
        default=False,
        dest="no_autoversion",
        action="store_true")

    parser.add_argument(
        "--offline",
        help="Don't resolve online resource, like schemas"
        + " for validation.",
        required=False,
        default=False,
        dest="offline",
        action="store_true")

    parser.add_argument(
        "--store-skip",
        help="Skip store step.",
        required=False,
        default=False,
        dest="store_skip",
        action="store_true")

    parser.add_argument(
        "--store-backend",
        help="Storage backend to be used."
        + " Default: TangoProjectFilesystemBackend",
        required=False,
        default=None,
        dest="store_backend")

    # service management
    parser.add_argument(
        "-s",
        "--service",
        help="Run packager in service mode with REST API.",
        required=False,
        default=False,
        dest="service",
        action="store_true")

    parser.add_argument(
        "--dump-swagger",
        help="Dump Swagger JSON of REST API and exit."
        + "\nDefault: False",
        required=False,
        default=False,
        dest="dump_swagger",
        action="store_true")

    parser.add_argument(
        "--dump-swagger-path",
        help="Path to dump Swagger JSON using --dump-swagger"
        + "\nDefault: doc/rest_api_model.json",
        required=False,
        default="doc/rest_api_model.json",
        dest="dump_swagger_path")

    parser.add_argument(
        "--address",
        help="Listen address of REST API when in service mode."
        + "\nDefault: 0.0.0.0",
        required=False,
        default="0.0.0.0",
        dest="service_address")

    parser.add_argument(
        "--port",
        help="TCP port of REST API when in service mode."
        + "\nDefault: 5099",
        required=False,
        default=5099,
        dest="service_port")
    if input_args is None:
        input_args = sys.argv[1:]
    return parser.parse_args(input_args)
