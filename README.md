[![Join the chat at https://gitter.im/5gtango/tango-sdk](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/5gtango/tango-sdk)

<p align="center"><img src="https://github.com/sonata-nfv/tng-api-gtw/wiki/images/sonata-5gtango-logo-500px.png" /></p>

# tng-sdk-package


This repository contains the `tng-sdk-package` component that is part of the European H2020 project [5GTANGO](http://www.5gtango.eu) NFV SDK. This component is responsible to create and unpack [5GTANGO service, VNF, and test packages](https://github.com/sonata-nfv/tng-schema/wiki/PkgSpec_LATEST).

The seed code of this component is based on the `son-cli` toolbox that was developed as part of the European H2020 project [SONATA](http://sonata-nfv.eu).

## Installation

```bash
$ python setup.py install
```

## Usage

### CLI mode

Runs the packager locally from the command line. Display detailed usage information with:

```bash
tng-package -h
```

#### Packaging

```sh
# package a NS project
tng-pkg -p misc/5gtango_ns_project_example1

# optionally specify output file name
tng-pkg -p misc/5gtango_ns_project_example1 -o my_package.tgo
```

#### Unpackaging

```sh
# unpack a 5GTANGO package to a local 5GTANGO SDK project
tng-pkg -u misc/5gtango-ns-package-example.tgo
```

### Service mode

Runs the packager as a micro service that exposes a REST API.

* `Note:` Currently only unpackaging is supported in this mode.

#### Run
##### Bare metal
```bash
tng-package -s
```

##### Docker-based
```bash
# build Docker container
pipeline/build/build.sh

# run Docker container
docker run --rm -d -p 5099:5099 --name tng-sdk-package registry.sonata-nfv.eu:5000/tng-sdk-package
```

#### Packaging

* `Note:` Currently only unpackaging is supported in this mode.

#### Unpackaging

```sh
# terminal 1 (tng-package service)
tng-package -s

# terminal 2 (callback dummy)
python misc/callback_mock.py

# terminal 3 (client)
# unpack valid package
curl -X POST -v -H "Content-Type: multipart/form-data" \
    -F callback_url="http://127.0.0.1:8000/api/v1/packages/on-change" \
    -F package="@misc/5gtango-ns-package-example.tgo" \
    http://127.0.0.1:5099/api/v1/packages

# unpack invalid package
curl -X POST -v -H "Content-Type: multipart/form-data" \
    -F callback_url="http://127.0.0.1:8000/api/v1/packages/on-change" \
    -F package="@misc/5gtango-ns-package-example-malformed.tgo" \
    http://127.0.0.1:5099/api/v1/packages
    
# unpack package w. bad checksum
curl -X POST -v -H "Content-Type: multipart/form-data" \
    -F callback_url="http://127.0.0.1:8000/api/v1/packages/on-change" \
    -F package="@misc/5gtango-ns-package-example-bad-checksum.tgo" \
    http://127.0.0.1:5099/api/v1/packages
    
# get status of all known packageing processes
curl -X GET http://127.0.0.1:5099/api/v1/packages/status

# get status of specific packageing process
curl -X GET http://127.0.0.1:5099/api/v1/packages/status/<packager_process_uuid>
```

## Development

To contribute to the development of this 5GTANGO component, you may use the very same development workflow as for any other 5GTANGO Github project. That is, you have to fork the repository and create pull requests.

### Setup development environment

```bash
$ python setup.py develop
```

### CI Integration

All pull requests are automatically tested by Jenkins and will only be accepted if no test is broken.

### Run tests manually

You can also run the test manually on your local machine. To do so, you need to do:

```bash
$ pytest -v
```

## License

This 5GTANGO component is published under Apache 2.0 license. Please see the LICENSE file for more details.

---
#### Lead Developers

The following lead developers are responsible for this repository and have admin rights. They can, for example, merge pull requests.

- Manuel Peuster ([@mpeuster](https://github.com/mpeuster))
- Stefan Schneider ([@StefanUPB](https://github.com/StefanUPB))

#### Feedback-Chanel

* Please use the GitHub issues to report bugs.
