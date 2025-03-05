import os

import requests
import json
import random
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from dotenv import load_dotenv

load_dotenv()

# Create a new Elasticsearch index
index_name = 'members'
es_url = os.getenv('ELASTIC_URL')
es_token = os.getenv('ELASTIC_AUTH_TOKEN')

# Define the index settings and mappings
# really looking for auto-completion on user names, first and last...
index_settings = {
    "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 1,
    },
    "mappings": {
        "properties": {
            "suggest": {
                "type": "completion",
            },
            "rank": {"type": "integer"},
            "name": {"type": "text"},
            "age": {"type": "integer"},
            "city": {"type": "text"},
            "usacId": {"type": "text"},
        }
    }
}

# Delete the index
response = requests.delete(f'{es_url}/{index_name}',
                           headers={"Content-Type": "application/json", "Authorization": f"ApiKey {es_token}"})
print(f'Index deletion response: {response.json()}')

# Create the index
response = requests.put(f'{es_url}/{index_name}',
                        headers={"Content-Type": "application/json", "Authorization": f"ApiKey {es_token}"},
                        data=json.dumps(index_settings))
print(f'Index creation response: {response.json()}')

with open('data/members.csv', 'r') as file:
    bulk_data = []
    total_count = 0
    for line in file:
        member_record = line.strip().split('|')

        name_records = member_record[2].split(' ')
        name_records.append(member_record[2])

        document = {
            "rank": int(member_record[0]),
            "name": member_record[2],
            "age": int(member_record[5]),
            "city": member_record[3],
            "usacId": member_record[4],
            "suggest": {
                "input": name_records,
            }

        }
        bulk_data.append({
            "index": {
                "_index": index_name,
                "_id": document["usacId"]
            }
        })
        # use 'copy_to' as describe in es docs, replicates the old '_all' field functionality that is deprecated
        # document["all"] = json.dumps(document)
        bulk_data.append(document)
        if len(bulk_data) >= 500:
            response = requests.post(f'{es_url}/_bulk',
                                     headers={"Content-Type": "application/json", "Authorization": f"ApiKey {es_token}"},
                                     data='\n'.join(json.dumps(d) for d in bulk_data) + '\n')
            total_count += len(bulk_data)
            print(f'Total written: {int(total_count / 2)}...')
            bulk_data.clear()
