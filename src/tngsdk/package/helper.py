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
import hashlib
import os
import zipfile
import tempfile
import time
import glob
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


def file_hash(path, h_func=hashlib.sha256):
    h = h_func()
    with open(path, 'rb', buffering=0) as f:
        for b in iter(lambda: f.read(128 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def _makedirs(p):
    if not os.path.exists(p) and p != "":
        LOG.debug("Creating: {}".format(p))
        os.makedirs(p)


def search_for_file(path="**/TOSCA.meta", recursive=True):
    """
    Recursively searches for a file.
    If there are multiple matches, the first one is
    returned.
    param: path: src/**/*.c
    """
    f_lst = list()
    try:
        # Trick17: Depending on the Python version, the recursive
        # argument might not be available. This provides a fallback.
        # This reduces the robustness against malformed packages but ensures
        # that the tool works well in older environments.
        f_lst = list(glob.iglob(path, recursive=recursive))
    except BaseException:
        f_lst = list(glob.iglob(path))
    LOG.debug("Searching for '{}' found: {}".format(path, f_lst))
    if len(f_lst) > 0:
        return f_lst[0]
    return None


def extract_zip_file_to_temp(path_zip, path_dest=None):
    """
    Simply extract the entire ZIP file for now.
    Might be improved for larger files.
    Always extract to a temp folder to work on.
    """
    if path_dest is None:
        path_dest = tempfile.mkdtemp()
    LOG.debug("Unzipping '{}' ...".format(path_zip))
    t_start = time.time()
    # unzipping
    with zipfile.ZipFile(path_zip, "r") as f:
        f.extractall(path_dest)
    LOG.debug("Unzipping done ({:.4f}s)".format(time.time()-t_start))
    # get path of output folder (it is based on zip name)
    wd = find_root_folder_of_pkg(path_dest)
    LOG.debug("Working root '{}'".format(wd))
    return wd


def find_root_folder_of_pkg(d):
    """
    Zip files can be odd and may contain folders
    w. name of zip file which then contain the root of
    the package structure.
    This functions tries to find the right root.
    """
    root_indicators = ["TOSCA-Metadata"]
    for ri in root_indicators:
        lst = glob.glob("{}/{}".format(d, ri))
        if len(lst) > 0:
            return lst[0].replace(ri, "")
    return d


def creat_zip_file_from_directory(path_src, path_dest):
    LOG.debug("Zipping '{}' ...".format(path_dest))
    t_start = time.time()
    zf = zipfile.ZipFile(path_dest, 'w', zipfile.ZIP_DEFLATED)
    for root, _, files in os.walk(path_src):
        for f in files:
            zf.write(os.path.join(root, f),
                     os.path.relpath(
                         os.path.join(root, f), path_src))
    zf.close()
    LOG.debug("Zipping done ({:.4f}s)".format(time.time()-t_start))


def write_block_based_meta_file(data, path):
    """
    Writes TOSCA/ETSI block-based meta files.
    data = [block0_dict, ....blockN_dict]
    """
    with open(path, "w") as f:
        for block in data:
            if block is None:
                continue
            for k, v in block.items():
                f.write("{}: {}\n".format(k, v))
            f.write("\n")  # block separator
