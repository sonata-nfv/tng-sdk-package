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
FROM python:3.6-slim

#
# Configurations
#
# Select the storage backend to be used
# TangoCatalogBackend, OsmNbiBackend
ENV STORE_BACKEND TangoCatalogBackend
# Disables uploading of artifacts after unpackaging
ENV STORE_SKIP False
# URL to the catalogue enpoint to which package contents are uploaded
ENV CATALOGUE_URL http://tng-cat:4011/catalogues/api/v2
#
# Logging
ENV LOGLEVEL INFO
ENV LOGJSON True


#
# Installation (packager)
#
RUN pip install flake8
ADD . /tng-sdk-package
WORKDIR /tng-sdk-package
RUN python setup.py install

#
# Installation (validator)
# We include tng-sdk-validation by default in this container so that the
# packager can always make use of it to validate packages/projects.
# Installation is done by fetching the HEAD of MASTER from GitHub.
#
# use wget/zip to install
RUN apt-get update && apt-get install -y wget unzip
WORKDIR /
RUN wget https://github.com/sonata-nfv/tng-sdk-validation/archive/master.zip
RUN unzip master.zip
WORKDIR /tng-sdk-validation-master
RUN python setup.py install
# alternative: use git/pip to install (but we don't have git in the container ;-))
#RUN apt-get update && apt-get install -y git
#RUN pip install git+https://github.com/sonata-nfv/tng-sdk-validation.git

#
# Runtime
#
WORKDIR /tng-sdk-package
EXPOSE 5099
CMD ["tng-package","-s"]
