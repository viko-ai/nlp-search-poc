import json
import logging.config

import plac  # type: ignore
import requests


def query_server(query, predict_only):
    url = "http://localhost:8000/predict" if predict_only else "http://localhost:8000/search"
    payload = json.dumps({"query": query})
    headers = {'Content-Type': 'application/json'}
    
    response = requests.request("GET", url, headers=headers, data=payload)
    json_response = response.json()
    pretty_response = json.dumps(json_response, indent=4)
    
    print(pretty_response)


@plac.pos('query', "Query")
@plac.flg('predict_only', "NER prediction only")
def main(query, predict_only):
    query_server(query, predict_only)


if __name__ == '__main__':
    logging.config.fileConfig('conf/logging.conf')
    plac.call(main)
