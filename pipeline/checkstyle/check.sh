#!/bin/bash
mkdir -p reports
docker run -i --rm registry.sonata-nfv.eu:5000/tng-sdk-package pycodestyle --exclude .eggs . > reports/checkstyle-pep8.txt
echo "checkstyle result:"
cat reports/checkstyle-pep8.txt
echo "done."
# always exit with 0 (ugly code style is not an error :))
#exit 0
