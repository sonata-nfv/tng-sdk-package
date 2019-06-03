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

# Install basics
RUN apt-get update && apt-get install -y git wget  # We net git to install other tng-* tools.
RUN pip install flake8 pyaml

# Pre-fetch latest tng-schemas (so that container works w/o internet connection)
RUN mkdir /root/.tng-schema
RUN mkdir /root/.tng-schema/service-descriptor/
WORKDIR /root/.tng-schema/service-descriptor/
RUN wget https://raw.githubusercontent.com/sonata-nfv/tng-schema/master/service-descriptor/nsd-schema.yml
RUN mkdir /root/.tng-schema/function-descriptor/
WORKDIR /root/.tng-schema/function-descriptor/
RUN wget https://raw.githubusercontent.com/sonata-nfv/tng-schema/master/function-descriptor/vnfd-schema.yml
RUN mkdir /root/.tng-schema/test-descriptor/
WORKDIR /root/.tng-schema/test-descriptor/
RUN wget https://raw.githubusercontent.com/sonata-nfv/tng-schema/master/test-descriptor/test-descriptor-schema.yml -O test-schema.yml
RUN mkdir /root/.tng-schema/policy-descriptor/
WORKDIR /root/.tng-schema/policy-descriptor/
RUN wget https://raw.githubusercontent.com/sonata-nfv/tng-schema/master/policy-descriptor/policy-schema.yml
RUN mkdir /root/.tng-schema/sla-template-descriptor/
WORKDIR /root/.tng-schema/sla-template-descriptor/
RUN wget https://raw.githubusercontent.com/sonata-nfv/tng-schema/master/sla-template-descriptor/sla-template-schema.yml
RUN mkdir /root/.tng-schema/slice-descriptor/
WORKDIR /root/.tng-schema/slice-descriptor/
RUN wget https://raw.githubusercontent.com/sonata-nfv/tng-schema/master/slice-descriptor/nst-schema.yml -O nstd-schema.yml
RUN mkdir /root/.tng-schema/package-specification/
WORKDIR /root/.tng-schema/package-specification/
RUN wget https://raw.githubusercontent.com/sonata-nfv/tng-schema/master/package-specification/napd-schema.yml

WORKDIR /
# Install other 5GTAGNO SDK components
# - tng-sdk-project (required by validator)
RUN pip install git+https://github.com/sonata-nfv/tng-sdk-project.git
RUN tng-sdk-project -h
RUN tng-wks  # create the default workspace
# - tng-sdk-validate (required to validate packages)
RUN pip install git+https://github.com/sonata-nfv/tng-sdk-validation.git
RUN tng-sdk-validate -h

#
# Installation (packager)
#
ADD . /tng-sdk-package
WORKDIR /tng-sdk-package
RUN python setup.py develop

#
# Runtime
#
WORKDIR /tng-sdk-package
EXPOSE 5099
#CMD ["tng-package","-s", "--skip-validation"]
CMD ["tng-package","-s"]
