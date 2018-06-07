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
import coloredlogs
import os
import sys

from tngsdk.package import rest, cli


LOG = logging.getLogger(os.path.basename(__file__))


def logging_setup():
    os.environ["COLOREDLOGS_LOG_FORMAT"] \
        = "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"


def main():
    logging_setup()
    args = cli.parse_args()
    # TODO better log configuration (e.g. file-based logging)
    if args.verbose:
        coloredlogs.install(level="DEBUG")
    else:
        coloredlogs.install(level="INFO")
    if args.dump_swagger:
        rest.dump_swagger(args)
        LOG.info("Dumped Swagger API model to {}".format(
            args.dump_swagger_path))
        sys.exit(0)
    # TODO validate if args combination makes any sense
    if args.service:
        # start tng-sdk-package in service mode (REST API)
        rest.serve_forever(args)
    else:
        # run package in CLI mode
        r = cli.dispatch(args)
        if r.error is not None:
            exit(1)  # exit with error code
        exit(0)
