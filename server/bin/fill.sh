#!/bin/bash

source ./cfg/include.sh

# AUTH

if [ $USE_LOCAL -eq 1 ]; then
  # Get auth cookie.
  curl ${CURL_DEBUG_FLAGS} -c ${COOKIE_FILE} "${GAE_URL}/_ah/login?email=${GAE_ADMIN}&admin=True&action=Login" -X GET
else
  # Get auth token.
  DATA="Passwd=$( rawurlencode "${GAE_APP_PASSWORD}" )&source=$( rawurlencode "${GAE_NAME}" )&accountType=$( rawurlencode "${GAE_ACCOUNT_TYPE}" )&Email=$( rawurlencode "${GAE_ADMIN}" )&service=ah"
  curl ${CURL_DEBUG_FLAGS} -c ${COOKIE_FILE} -d "${DATA}" "https://www.google.com/accounts/ClientLogin" -o "${AUTH_FILE}"

  SID=$(cat "${AUTH_FILE}" | perl -ne '/SID=([\w\-]+)/ && print "$1\n"')
  LSID=$(cat "${AUTH_FILE}" | perl -ne '/LSID=([\w\-]+)/ && print "$1\n"')
  AUTH_TOKEN=$(cat "${AUTH_FILE}" | perl -ne '/Auth=([\w\-]+)/ && print "$1\n"')
  echo SID="${SID}"
  echo LSID="${LSID}"
  echo AUTH_TOKEN="${AUTH_TOKEN}"

  # Get ACSID cookie.
  curl ${CURL_DEBUG_FLAGS} -c ${COOKIE_FILE} "${GAE_URL}/_ah/login?auth=${AUTH_TOKEN}" -X POST -H "Content-length: 0"

  #REDIRECT_URL=$( rawurlencode "${DEVICE_ALL_URL}/" )
  #echo REDIRECT_URL="${REDIRECT_URL}"
  #curl ${CURL_FLAGS} -L "${GAE_URL}/_ah/login?continue=${REDIRECT_URL}&auth=${AUTH_TOKEN}" -H "Accept: application/json"
fi

# Test auth token.
curl ${CURL_FLAGS} "${GAE_URL}/" -X GET
#curl ${CURL_FLAGS} ${DEVICE_ALL_URL}/ -X GET -H "Accept: application/json"
#curl ${CURL_FLAGS} ${USER_ALL_URL}/ -X GET -H "Accept: application/json"

# CONFIG

# Delete All
curl ${CURL_FLAGS} ${GAE_URL}/config/ -X DELETE

# Create One
curl ${CURL_FLAGS} ${GAE_URL}/config/ -X POST -H "Content-Type: application/json" -d "{\"name\": \"default\", \"gcm_api_key\": \"${GCM_API_KEY}\"}"
# DEVICE

# Delete All
curl ${CURL_FLAGS} ${DEVICE_ALL_URL}/ -X DELETE

# Create One
curl ${CURL_FLAGS} ${DEVICE_ALL_URL}/ -X POST -H "Content-Type: application/json" -d "${DEVICE_0}"
# Create One
curl ${CURL_FLAGS} ${DEVICE_ALL_URL}/ -X POST -H "Content-Type: application/json" -d "${DEVICE_1}"

# USER
# Delete All
curl ${CURL_FLAGS} ${USER_ALL_URL}/ -X DELETE
# Create One
curl ${CURL_FLAGS} ${USER_ALL_URL}/ -X POST -H "Content-Type: application/json" -d "{\"name\" : \"testname\", \"description\" : \"test description\", \"groups\" : \"test groups\"}"

# PUBLICATION

# Delete All
curl ${CURL_FLAGS} ${PUBLICATION_ALL_URL}/ -X DELETE
# Create One
curl ${CURL_FLAGS} ${PUBLICATION_ALL_URL}/ -X POST -H "Content-Type: application/json" -d "{\"topic\" : \"topic0\", \"description\" : \"topic0 description\"}"


# SUBSCRIPTION

# Delete All
curl ${CURL_FLAGS} ${SUBSCRIPTION_ALL_URL}/ -X DELETE
# Create One
curl ${CURL_FLAGS} ${SUBSCRIPTION_ALL_URL}/ -X POST -H "Content-Type: application/json" -d "{\"topic\" : \"topic0\", \"dev_id\" : \"${DEV_ID_0}\"}"
# Create One
curl ${CURL_FLAGS} ${SUBSCRIPTION_ALL_URL}/ -X POST -H "Content-Type: application/json" -d "{\"topic\" : \"topic0\", \"dev_id\" : \"${DEV_ID_1}\"}"
