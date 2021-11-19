#!/bin/ksh

# Calls the /search endpoint
# Requires curl & jq

die() {
    printf '%s\n' "$1" >&2
    exit -1
}

show_help() {
  echo "Usage: $0 'search query'"
  exit -1
}

query() {
  data='{"query": "'$1'"}'

  curl -s --location --request GET 'http://localhost:8000/search' \
  --header 'Content-Type: application/json' \
  --data-raw "$data" | jq
}

if [ -z "$1" ]; then
  show_help
else
  query "$1"
fi
