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
import copy
from tngsdk.package.logger import TangoLogger


LOG = TangoLogger.getLogger(__name__)


def dictionary_deep_merge(d1, d2, skip=None):
    """
    Recursively merges dicts containing other dicts or lists.
    Fills d1 with additional contents of d2.
    d2 overwrites keys in d1

    source: https://www.electricmonk.nl/log/2017/05/07/...
    ... merging-two-python-dictionaries-by-deep-updating/
    """
    if skip is None:
        skip = list()
    for k, v in d2.items():
        if k in skip:
            continue
        if type(v) == list:
            if k not in d1:
                d1[k] = copy.deepcopy(v)
            else:
                d1[k].extend(v)
        elif type(v) == dict:
            if k not in d1:
                d1[k] = copy.deepcopy(v)
            else:
                dictionary_deep_merge(d1[k], v)
        else:
            d1[k] = copy.copy(v)
