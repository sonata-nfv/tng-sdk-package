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
import logging
import os
import requests
import yaml
from jsonschema import validate


LOG = logging.getLogger(os.path.basename(__file__))


def validate_project_with_external_validator(project_path):
    """
    Try to use an external validator (typically tng-sdk-validation)
    to validate the given service project.
    """
    # called in do_package
    # not yet called for unpacker (needs to be called from
    #    filestore backend right now, (maybe unpack to tmp project
    #    for validation))
    return True, None  # return bool, error_msg


def validate_yaml_online(data, schema_uri=None):
    """
    Validates the given data structure against an online
    schema definition provided by schema_uri.
    If schema_uri is not given, we try to get it from
    the 'descriptor_schema' field in 'data'.
    Returns: True/False
    """
    if schema_uri is None:
        # try to get schema_uri from data
        schema_uri = data.get("descriptor_schema", None)
    if schema_uri is None:
        LOG.error("Cannot find URI pointing to schema.")
        return False
    try:
        # try to download schema
        r = requests.get(schema_uri, timeout=3)
    except BaseException as e:
        LOG.error("Couldn't fetch schema from '{}': {}".format(
            schema_uri, e))
        return False
    try:
        # try to parse schema
        schema = yaml.load(r.text)
    except BaseException as e:
        LOG.error("Couldn't parse schema from '{}': {}".format(
            schema_uri, e))
        return False
    try:
        # validate data against schema
        validate(data, schema)
    except BaseException as e:
        LOG.error("Couldn't validate against schema from '{}': {}".format(
            schema_uri, e))
        return False
    return True
