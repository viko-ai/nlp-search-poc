import json
import logging.config

import plac  # type: ignore
import requests


def query_server(query):
    url = "http://localhost:8000/search"
    payload = json.dumps({"query": query})
    headers = {'Content-Type': 'application/json'}
    
    response = requests.request("GET", url, headers=headers, data=payload)
    json_response = response.json()
    pretty_response = json.dumps(json_response, indent=4)
    
    print(pretty_response)


@plac.pos('query', "Query")
def main(query):
    query_server(query)


if __name__ == '__main__':
    logging.config.fileConfig('conf/logging.conf')
    plac.call(main)
