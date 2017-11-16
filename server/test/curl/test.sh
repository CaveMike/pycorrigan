#!/bin/bash

source ./cfg/include.sh

# AUTH

if [ $USE_LOCAL -eq 1 ]; then
  # Get auth cookie.
  curl ${CURL_DEBUG_FLAGS} -c ${COOKIE_FILE} "${GAE_URL}/_ah/login?email=${NAME_0}&admin=True&action=Login" -X GET
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

# DEVICE

# Delete All
curl ${CURL_FLAGS} ${DEVICE_ALL_URL}/ -X DELETE
# List All
curl ${CURL_FLAGS} ${DEVICE_ALL_URL}/ -X GET -H "Accept: application/json"

# Create One
curl ${CURL_FLAGS} ${DEVICE_ALL_URL}/ -X POST -H "Content-Type: application/json" -d "${DEVICE_0}"
# Create One
curl ${CURL_FLAGS} ${DEVICE_ALL_URL}/ -X POST -H "Content-Type: application/json" -d "${DEVICE_1}"
# List One
curl ${CURL_FLAGS} ${DEVICE_0_URL}/ -X GET -H "Accept: application/json"

# Send message to device 0.
curl ${CURL_FLAGS} ${DEVICE_1_URL}/message/ -X POST -H "Content-Type: application/json" -d "{\"dev_id\" : \"${DEV_ID_0}\", \"message\" : \"test message -- hello device 0\"}"
# Send message to device 1.
curl ${CURL_FLAGS} ${DEVICE_1_URL}/message/ -X POST -H "Content-Type: application/json" -d "{\"dev_id\" : \"${DEV_ID_1}\", \"message\" : \"test message -- hello device 1\"}"

# Update One
curl ${CURL_FLAGS} ${DEVICE_0_URL}/ -X PUT -H "Content-Type: application/json" -d "${DEVICE_0_UPDATED}"
# List One
curl ${CURL_FLAGS} ${DEVICE_0_URL}/ -X GET -H "Accept: application/json"

# Delete One
#curl ${CURL_FLAGS} ${DEVICE_0_URL}/ -X DELETE
# List One
#curl ${CURL_FLAGS} ${DEVICE_0_URL}/ -X GET -H "Accept: application/json"
# List All
#curl ${CURL_FLAGS} ${DEVICE_ALL_URL}/ -X GET -H "Accept: application/json"

# USER
# Delete All
curl ${CURL_FLAGS} ${USER_ALL_URL}/ -X DELETE
# List All
curl ${CURL_FLAGS} ${USER_ALL_URL}/ -X GET -H "Accept: application/json"

# Create One
curl ${CURL_FLAGS} ${USER_ALL_URL}/ -X POST -H "Content-Type: application/json" -d "{\"name\" : \"test name\", \"description\" : \"test description\", \"groups\" : \"test groups\"}"
# List All
curl ${CURL_FLAGS} ${USER_ALL_URL}/ -X GET -H "Accept: application/json"

# PUBLICATION

# Delete All
curl ${CURL_FLAGS} ${PUBLICATION_ALL_URL}/ -X DELETE

# Create One
curl ${CURL_FLAGS} ${PUBLICATION_ALL_URL}/ -X POST -H "Content-Type: application/json" -d "{\"topic\" : \"topic0\", \"description\" : \"topic0 description\"}"
# List All
curl ${CURL_FLAGS} ${PUBLICATION_ALL_URL}/ -X GET -H "Accept: application/json"


# SUBSCRIPTION

# Delete All
curl ${CURL_FLAGS} ${SUBSCRIPTION_ALL_URL}/ -X DELETE

# Create One
curl ${CURL_FLAGS} ${SUBSCRIPTION_ALL_URL}/ -X POST -H "Content-Type: application/json" -d "{\"topic\" : \"topic0\", \"dev_id\" : \"${DEV_ID_0}\"}"
# Create One
curl ${CURL_FLAGS} ${SUBSCRIPTION_ALL_URL}/ -X POST -H "Content-Type: application/json" -d "{\"topic\" : \"topic0\", \"dev_id\" : \"${DEV_ID_1}\"}"
# List All
curl ${CURL_FLAGS} ${SUBSCRIPTION_ALL_URL}/ -X GET -H "Accept: application/json"

# Send message to device 0.
#curl ${CURL_FLAGS} ${PUBLICATION_ALL_URL}/xxx/message/ -X POST -H "Content-Type: application/json" -d "{\"pub_id\" : \"xxx\", \"message\" : \"test message -- publishing\"}"
