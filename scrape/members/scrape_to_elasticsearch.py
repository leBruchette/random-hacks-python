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
es_url = f'{os.getenv('ELASTIC_URL')}/{index_name}'
es_token = os.getenv('ELASTIC_AUTH_TOKEN')

# Define the index settings and mappings
index_settings = {
    "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 1
    },
    "mappings": {
        "properties": {
            "rank": {"type": "integer"},
            "name": {"type": "text"},
            "age": {"type": "integer"},
            "city": {"type": "text"},
            "usacId": {"type": "text"},
            "all": {"type": "keyword"}
        }
    }
}

# Create the index
response = requests.put(es_url,
                        headers={"Content-Type": "application/json", "Authorization": f"ApiKey {es_token}"},
                        data=json.dumps(index_settings))
print(f'Index creation response: {response.json()}')

# when really parsing the page, instead using members.csv and splitting on '|'
from sources import rankings_url as _rankings_url
service = Service('/opt/homebrew/bin/chromedriver')
driver = webdriver.Chrome(service=service)
driver.get(_rankings_url)
time.sleep(3)

# Find anchor tags with href containing javascript:void(0)
anchor_get_more = driver.find_elements(By.CSS_SELECTOR, 'a[href="javascript:void(0)"][onclick="getMore()"]')

# keep loading the page
while anchor_get_more is not None and len(anchor_get_more) > 0:
    anchor_get_more[0].click()
    time.sleep(random.uniform(2, 4))
    anchor_get_more = driver.find_elements(By.CSS_SELECTOR, 'a[href="javascript:void(0)"][onclick="getMore()"]')

rows = []
tables = driver.find_elements(By.CSS_SELECTOR, 'table.datatable')

for table in tables:
    bulk_data = []
    for row in table.find_elements(By.TAG_NAME, 'tr'):
        columns = row.find_elements(By.TAG_NAME, 'td')
        if len(columns) < 7:
            continue
        document = {
            "rank": int(columns[0].text),
            "name": columns[2].text,
            "age": int(columns[5].text),
            "city": columns[3].text,
            "usacId": columns[4].text
        }
        bulk_data.append({
            "index": {
                "_index": index_name,
                "_id": document["usacId"]
            }
        })
        document["all"] = json.dumps(document)
        bulk_data.append(document)
        if len(bulk_data) >= 500:
            response = requests.post(f'{es_url}/_bulk',
                                     headers={"Content-Type": "application/json", "Authorization": f"ApiKey {es_token}"},
                                     data='\n'.join(json.dumps(d) for d in bulk_data) + '\n')
            bulk_data.clear()

driver.quit()
