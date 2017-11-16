#!/bin/bash

# Convert string into a valid URL encoded string.
# From:
#  http://stackoverflow.com/questions/296536/urlencode-from-a-bash-script
rawurlencode() {
  local string="${1}"
  local strlen=${#string}
  local encoded=""

  for (( pos=0 ; pos<strlen ; pos++ )); do
     c=${string:$pos:1}
     case "$c" in
        [-_.~a-zA-Z0-9] ) o="${c}" ;;
        * )               printf -v o '%%%02x' "'$c"
     esac
     encoded+="${o}"
  done
  echo "${encoded}"    # You can either set a return variable (FASTER)
  REPLY="${encoded}"   #+or echo the result (EASIER)... or both... :p
}

# Set to 1 to use the local server, otherwise use the remote server.
USE_LOCAL=1

# Python source file that contains configuration.
PYTHON_DEPLOY="./cfg/deploy.py"
PYTHON_TEST_DATA="./cfg/testdata.py"

GAE_NAME=$(cat "${PYTHON_DEPLOY}" | perl -ne '/GAE_NAME\s*=\s*.(\w+)./ && print "$1\n"')
GAE_ADMIN=$(cat "${PYTHON_DEPLOY}" | perl -ne '/GAE_ADMIN\s*=\s*.(.+)./ && print "$1\n"')
GAE_ACCOUNT_TYPE=$(cat "${PYTHON_DEPLOY}" | perl -ne '/HOSTED_OR_GOOGLE\s*=\s*.(.+)./ && print "$1\n"')
GAE_APP_PASSWORD=$(cat "${PYTHON_DEPLOY}" | perl -ne '/GAE_APP_PASSWORD\s*=\s*.(\w+)./ && print "$1\n"')
GAE_LOCAL_SERVER=$(cat "${PYTHON_DEPLOY}" | perl -ne '/GAE_LOCAL_SERVER\s*=\s*.(.+)./ && print "$1\n"')
GAE_REMOTE_SERVER="${GAE_NAME}.appspot.com"
GAE_LOCAL_URL='http://${GAE_LOCAL_SERVER}'
GAE_REMOTE_URL='http://${GAE_REMOTE_SERVER}'
GCM_API_KEY=$(cat "${PYTHON_DEPLOY}" | perl -ne '/GCM_API_KEY\s*=\s*.(\w+)./ && print "$1\n"')

NAME_0=$(cat "${PYTHON_TEST_DATA}" | perl -ne '/TEST_DEVICE_0\s*=\s*{.name.\s*.\s*.([^'\'']+).,.*/ && print "$1\n"')
DEV_ID_0=$(cat "${PYTHON_TEST_DATA}" | perl -ne '/TEST_DEVICE_0\s*=\s*{.*.dev_id.\s*.\s*.([^'\'']+)..*/ && print "$1\n"')
REG_ID_0=$(cat "${PYTHON_TEST_DATA}" | perl -ne '/TEST_DEVICE_0\s*=\s*{.*.reg_id.\s*.\s*.([^'\'']+)..*/ && print "$1\n"')
RESOURCE_0=$(cat "${PYTHON_TEST_DATA}" | perl -ne '/TEST_DEVICE_0\s*=\s*{.*.resource.\s*.\s*.([^'\'']+)..*/ && print "$1\n"')
TYPE_0=$(cat "${PYTHON_TEST_DATA}" | perl -ne '/TEST_DEVICE_0\s*=\s*{.*.type.\s*.\s*.([^'\'']+)..*/ && print "$1\n"')
echo NAME_0=${NAME_0}
echo DEV_ID_0=${DEV_ID_0}
echo REG_ID_0=${REG_ID_0}
echo RESOURCE_0=${RESOURCE_0}
echo TYPE_0=${TYPE_0}

NAME_1=$(cat "${PYTHON_TEST_DATA}" | perl -ne '/TEST_DEVICE_1\s*=\s*{.name.\s*.\s*.([^'\'']+).,.*/ && print "$1\n"')
DEV_ID_1=$(cat "${PYTHON_TEST_DATA}" | perl -ne '/TEST_DEVICE_1\s*=\s*{.*.dev_id.\s*.\s*.([^'\'']+)..*/ && print "$1\n"')
REG_ID_1=$(cat "${PYTHON_TEST_DATA}" | perl -ne '/TEST_DEVICE_1\s*=\s*{.*.reg_id.\s*.\s*.([^'\'']+)..*/ && print "$1\n"')
RESOURCE_1=$(cat "${PYTHON_TEST_DATA}" | perl -ne '/TEST_DEVICE_1\s*=\s*{.*.resource.\s*.\s*.([^'\'']+)..*/ && print "$1\n"')
TYPE_1=$(cat "${PYTHON_TEST_DATA}" | perl -ne '/TEST_DEVICE_1\s*=\s*{.*.type.\s*.\s*.([^'\'']+)..*/ && print "$1\n"')
echo NAME_1=${NAME_1}
echo DEV_ID_1=${DEV_ID_1}
echo REG_ID_1=${REG_ID_1}
echo RESOURCE_1=${RESOURCE_1}
echo TYPE_1=${TYPE_1}

DEVICE_0="{\"name\": \"${NAME_0}\", \"dev_id\": \"${DEV_ID_0}\", \"reg_id\": \"${REG_ID_0}\", \"resource\": \"${RESOURCE_0}\", \"type\": \"${TYPE_0}\"}"
DEVICE_0_UPDATED="{\"name\": \"updated-${NAME_0}\", \"dev_id\": \"${DEV_ID_0}\", \"reg_id\": \"${REG_ID_0}\", \"resource\": \"${RESOURCE_0}\", \"type\": \"${TYPE_0}\"}"

DEVICE_1="{\"name\": \"${NAME_1}\", \"dev_id\": \"${DEV_ID_1}\", \"reg_id\": \"${REG_ID_1}\", \"resource\": \"${RESOURCE_1}\", \"type\": \"${TYPE_1}\"}"

# Generic variables
TEMP_DIR=$(mktemp -dt "GAE_NAME")

COOKIE_FILE="${TEMP_DIR}/cookies.txt"
AUTH_FILE="${TEMP_DIR}/auth.txt"

CURL_DEBUG_FLAGS="-i -v"
CURL_FLAGS="${CURL_DEBUG_FLAGS} -b ${COOKIE_FILE}"

if [ $USE_LOCAL -eq 1 ]; then
  GAE_URL="http://${GAE_LOCAL_SERVER}"
else
  GAE_URL="http://${GAE_REMOTE_SERVER}"
fi

USER_ALL_URL="${GAE_URL}/user"

DEVICE_ALL_URL="${GAE_URL}/device"
DEVICE_0_URL="${GAE_URL}/device/${DEV_ID_0}"
DEVICE_1_URL="${GAE_URL}/device/${DEV_ID_1}"

PUBLICATION_ALL_URL="${GAE_URL}/publication"

SUBSCRIPTION_ALL_URL="${GAE_URL}/subscription"

# Print variables
echo USE_LOCAL="${USE_LOCAL}"
echo GAE_NAME="${GAE_NAME}"
echo GAE_ADMIN="${GAE_ADMIN}"
echo GAE_ACCOUNT_TYPE="${GAE_ACCOUNT_TYPE}"
echo GAE_APP_PASSWORD="${GAE_APP_PASSWORD}"
echo GAE_LOCAL_SERVER="${GAE_LOCAL_SERVER}"
echo GAE_REMOTE_SERVER="${GAE_REMOTE_SERVER}"
echo GAE_LOCAL_URL="${GAE_LOCAL_URL}"
echo GAE_REMOTE_URL="${GAE_REMOTE_URL}"
echo GAE_URL="${GAE_URL}"
echo TEMP_DIR="${TEMP_DIR}"
echo COOKIE_FILE="${COOKIE_FILE}"
echo AUTH_FILE="${AUTH_FILE}"
echo CURL_DEBUG_FLAGS="${CURL_DEBUG_FLAGS}"
echo CURL_FLAGS="${CURL_FLAGS}"
