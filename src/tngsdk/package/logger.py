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
import datetime
import json


class TangoLogger(object):

    @classmethod
    def configure(cls, log_level=logging.INFO, log_json=False):
        """
        Configure all active TangoLoggers
        Two modes:
        - log_json = False: Normal colored logging in text format
        - log_json = True: 5GTANGO logging (flat JSON objects and metadata)
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
        return logger


class TangoJsonLogHandler(logging.StreamHandler):
    """
    Custom log handler to create JSON-based log messages
    as required by the 5GTANGO SP.
    https://github.com/sonata-nfv/tng-gtk-utils

    It uses the normal Python logging interface and utilizes
    the "extra" parameter of the logging methods to add additional
    fields (optionally) for the JSON output.

    Example:
    LOG = TangoLogger.getLogger("logger_name")
    TangoLogger.configure(log_level=logging.INFO, log_json=True)
    LOG.info("the message", extra={"start_stop": "START", "status": "400"})

    Turns into:
    {
        "type": "I",
        "timestamp": "2018-10-18 15:49:08 UTC",
        "start_stop": "START",
        "component": "logger_name",
        "operation": "caling_function",
        "message": "the message",
        "status": "400",
        "time_elapsed": ""
    }
    """

    def _to_tango_dict(self, record):
        """
        Creates a dict in 5GTANGO format from the given record.
        Sets defaults of not given.
        """
        d = {
            # TANGO default fields
            "type": record.levelname[0],
            "timestamp": "{} UTC".format(datetime.datetime.utcnow()),
            "start_stop": record.__dict__.get("start_stop", ""),
            "component": record.name,
            "operation": record.__dict__.get("operation", record.funcName),
            "message": str(record.msg),
            "status": record.__dict__.get("status", ""),
            "time_elapsed": record.__dict__.get("time_elapsed", ""),
            # some additional fields (because we can ;-))
            "lineno": record.lineno,
            "threadName": record.threadName,
            "processName": record.processName,
        }
        return d

    def emit(self, record):
        """
        We go the simple way here: Just print the JSON :-)
        """
        print(json.dumps(self._to_tango_dict(record)))
