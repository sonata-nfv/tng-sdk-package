#!/bin/bash
set -e
docker tag registry.sonata-nfv.eu:5000/tng-sdk-package:latest registry.sonata-nfv.eu:5000/tng-sdk-package:int
docker push registry.sonata-nfv.eu:5000/tng-sdk-package:int
