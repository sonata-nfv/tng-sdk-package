#!/bin/bash
set -e
echo "checking style ..."
docker run -i --rm registry.sonata-nfv.eu:5000/tng-sdk-package flake8 --ignore=E741,E121,E123,E126,E226,W503,W504 --exclude .eggs .
echo "done."
# always exit with 0 (ugly code style is not an error :))
#exit 0
