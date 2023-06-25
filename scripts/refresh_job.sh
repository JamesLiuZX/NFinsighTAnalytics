export USER_NAME="{USERNAME}"
export PASSWORD="{PASSWORD}"
export HOSTNAME="{HOSTNAME}"

export TOKEN=$(curl -X 'POST' \
  "http://${HOSTNAME}/token" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d "grant_type=&username=${USER_NAME}&password=${PASSWORD}&scope=&client_id=&client_secret=" | jq -r ".access_token")

curl -X 'GET' "http://${HOSTNAME}/nft/refresh" \
  -H 'accept: application/json' \
  -H "Authorization: Bearer ${TOKEN}"

# curl -X 'GET' \
  # "http://${HOSTNAME}/upsert_collection_data?contract_address=0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D&duration=DURATION_1_DAY" \
  # -H 'accept: application/json' \
  # -H "Authorization: Bearer ${TOKEN}"

