#!/bin/bash 
# shellcheck disable=SC1091

set -o errexit
set -o pipefail
set -o nounset
set +o xtrace

############################################################################
# The script runs all the unit tests.
#
# run:
#
# export AWS_ACCESS_KEY_ID=xxxxxx
# export AWS_SECRET_ACCESS_KEY=yyyyyy
# export AWS_DEFAULT_REGION=zzzzzz
#
# ./tests.sh
#
############################################################################

if [[ ! -v AWS_ACCESS_KEY_ID ]]
then
  echo "ERROR: environment variable AWS_ACCESS_KEY_ID not set!"
  exit 1
fi

if [[ ! -v AWS_SECRET_ACCESS_KEY ]]
then
  echo "ERROR: environment variable AWS_SECRET_ACCESS_KEY not set!"
  exit 1
fi

if [[ ! -v AWS_DEFAULT_REGION ]]
then
  echo "ERROR: environment variable AWS_DEFAULT_REGION not set!"
  exit 1
fi
  
export DATACENTER_DIR
DATACENTER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && cd ../.. && pwd)"

export PYTHONPATH
PYTHONPATH="${DATACENTER_DIR}"/vm/datacenter/src:"${DATACENTER_DIR}"/vm/datacenter/tests/src

source "${DATACENTER_DIR}"/.venv/bin/activate

cd "${DATACENTER_DIR}"/vm/datacenter/tests/src
pytest -s
