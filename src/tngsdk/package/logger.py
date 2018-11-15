#  Copyright (c) 2018 SONATA-NFV, 5GTANGO, Paderborn University
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

#
# This module implements custom loggers for use in the 5GTANGO SP.
#
import logging
import coloredlogs


class TangoLogger(object):

    @classmethod
    def configure(cls, log_level=logging.INFO, log_json=False):
        """
        Configure all active TangoLoggers
        """
        # reconfigure all our TangoLoggers
        for n, l in logging.Logger.manager.loggerDict.items():
            # use prefix to only get TangoLoggers
            if n.startswith("tango.") and isinstance(l, logging.Logger):
                # apply log_level
                l.setLevel(log_level)
                for h in l.handlers:
                    # show messages in all handlers
                    h.setLevel(log_level)
                    # disable handler depending on log_json
                    if isinstance(h, TangoJsonLogHandler):
                        if not log_json:
                            h.setLevel(999)  # disable (hide all)
                    else:
                        if log_json:
                            h.setLevel(999)  # disable (hide all)

    @classmethod
    def getLogger(cls, name, log_level=logging.INFO):
        """
        Create a TangoLogger logger.
        """
        # all TangoLoggers are prefixed for global setup
        logger = logging.getLogger("tango.{}".format(name))
        coloredlogs.install(logger=logger, level=log_level)
        th = TangoJsonLogHandler()
        logger.addHandler(th)
        # logger.propagate = False  # do not send to root logger
        return logger


class TangoJsonLogHandler(logging.StreamHandler):
    """
    Custom log handler to create JSON-based log messages
    as required by the 5GTANGO SP.
    https://github.com/sonata-nfv/tng-gtk-utils
    """

    def emit(self, record):
        print("TANGO LOGGER {}".format(record.msg))
