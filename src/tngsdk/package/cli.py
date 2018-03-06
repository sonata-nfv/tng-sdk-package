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
import argparse
import os
import sys
from tngsdk.package.packager import PM


LOG = logging.getLogger(os.path.basename(__file__))


def dispatch(args):
    # set default output paths
    if args.output is None:
            args.output = os.getcwd()
    # create packager object
    p = PM.new_packager(args)
    # trigger pack/unpack
    if args.package:
        p.package()
    else:
        p.unpackage()
    LOG.debug("Packager result: {}".format(p.result))
    return p.result


def parse_args(input_args=None):
    parser = argparse.ArgumentParser(
        description="5GTANGO SDK packager")

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
        help="Package format [5GTANGO|OSM]."
        + "\nDefault: 5GTANGO",
        required=False,
        default="5GTANGO",
        dest="format")

    parser.add_argument(
        "-v",
        "--verbose",
        help="Output debug messages.",
        required=False,
        default=False,
        dest="verbose",
        action="store_true")

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
