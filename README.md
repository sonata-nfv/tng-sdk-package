[![Join the chat at https://gitter.im/5gtango/tango-sdk](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/5gtango/tango-sdk) [![Build Status](https://jenkins.sonata-nfv.eu/buildStatus/icon?job=tng-sdk-package-pipeline/master)](https://jenkins.sonata-nfv.eu/job/tng-sdk-package-pipeline/job/master/)

<p align="center"><img src="https://github.com/sonata-nfv/tng-api-gtw/wiki/images/sonata-5gtango-logo-500px.png" /></p>

# tng-sdk-package


This repository contains the `tng-sdk-package` component that is part of the European H2020 project [5GTANGO](http://www.5gtango.eu) NFV SDK. This component is responsible to create and unpack [5GTANGO service, VNF, and test packages](https://github.com/sonata-nfv/tng-schema/wiki/PkgSpec_LATEST). The seed code of this component is based on the `son-cli` toolbox that was developed as part of the European H2020 project [SONATA](http://sonata-nfv.eu).

To simplify the creation and extraction of 5GTANGO packages, we develop this packager tool as part of 5GTANGO's SDK. This tool is a complete rewrite of the SONATA packaging tool. The reason for this rewrite is that the 5GANGO packaging tool does not only support and simplifies the package creation but can also be used to unpack packages. For this, the packaging tool can be deployed as a micro service and used, e.g., by the service platform to unpack packages. The clear benefit of this design, compared to the SONATA design in which we used different tools for this, is that only one common codebase needs to be maintained that deals with packages. Thus, code changes, which may be a result of a change in the package format, need only be done in a single component of 5GTANGO. The architecture and design of the packaging tools is described in [5GTANGO D4.1 First open-source release of the SDK toolset](https://5gtango.eu/project-outcomes/deliverables/42-d4-1-first-open-source-release-of-the-sdk-toolset.html) in more detail.

## Documentation

Besides this README file, more documentation is available in the [wiki](https://github.com/sonata-nfv/tng-sdk-package/wiki) belonging to this repository. Additional information are available in the project's deliverables:

* [5GTANGO D2.2 Architecture Design](https://5gtango.eu/project-outcomes/deliverables/2-uncategorised/31-d2-2-architecture-design.html)
* [5GTANGO D4.1 First open-source release of the SDK toolset](https://5gtango.eu/project-outcomes/deliverables/42-d4-1-first-open-source-release-of-the-sdk-toolset.html)

## Installation and Dependencies

This component is implemented in Python3. Its requirements are specified [here](https://github.com/sonata-nfv/tng-sdk-package/blob/master/requirements.txt).

### Automated:

The automated installation requires `pip` (more specifically `pip3`).

```bash
$ pip install git+https://github.com/sonata-nfv/tng-sdk-package
```

### Manual:

```bash
$ git clone git@github.com:sonata-nfv/tng-sdk-package.git
$ cd tng-sdk-package
$ python setup.py install
```

## Usage

The packager can either be used as command line tool (CLI mode) or deployed as a micro service which offers a REST API.

### CLI mode

Runs the packager locally from the command line. Details about all possible parameters can be shown using:

```bash
tng-pkg -h
```

#### Packaging

```sh
# package a 5GTANGO SDK project
tng-pkg -p misc/5gtango_ns_project_example1
```

#### Unpackaging

```sh
# unpack a 5GTANGO package to a local 5GTANGO SDK project
tng-pkg -u misc/5gtango-ns-package-example.tgo
```

### Service mode

Runs the packager as a micro service that exposes a REST API.

* `Note:` Currently *only unpackaging* is supported in this mode.

#### Run `tng-sdk-package` as a service:
##### Bare metal
```bash
tng-pkg -s
```

##### Docker-based
```bash
# build Docker container
pipeline/build/build.sh

# run Docker container
docker run --rm -d -p 5099:5099 --name tng-sdk-package registry.sonata-nfv.eu:5000/tng-sdk-package
```


#### Unpackaging

```sh
# terminal 1 (run tng-sdk-package service)
tng-pkg -s

# terminal 2 (client that sends a package to be unpacked using REST API)
curl -X POST -v -H "Content-Type: multipart/form-data" \
    -F package="@misc/5gtango-ns-package-example.tgo" \
    http://127.0.0.1:5099/api/v1/packages
    
# get status of all known packageing processes
curl -X GET http://127.0.0.1:5099/api/v1/packages/status
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

### Execute full CI pipeline locally:

```bash
$ ./pipeline_local.sh
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
