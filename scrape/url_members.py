from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import requests
import json
import random
import time

service = Service('/opt/homebrew/bin/chromedriver')
driver = webdriver.Chrome(service=service)




# Open the URL
# https://legacy.usacycling.org/rankings/points.php?state=&sex=M&disc=Road%3ACRIT&cat=&agemin=1&agemax=99&mode=get_rank
# Create a new Elasticsearch index
index_name = 'members'
es_url = f'http://localhost:9200/{index_name}'

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
            "all": {"type":"keyword"}
        }
    }
}

# Create the index
response = requests.put(es_url, headers={"Content-Type": "application/json", "Authorization": "ApiKey cmpMMkFKVUJsM2lIcm0xX3pfV1M6VGlxVUJTRE1ReXU4V0M0UHNZM1hMZw=="}, data=json.dumps(index_settings))
print(f'Index creation response: {response.json()}')

# when really parsing the page, instead using members.csv and splitting on '|'
url = 'https://legacy.usacycling.org/rankings/points.php?state=&sex=M&disc=Road%3ACRIT&cat=&agemin=1&agemax=99&mode=get_rank'
driver.get(url)
time.sleep(3)

# Find anchor tags with href containing javascript:void(0)
anchor_get_more = driver.find_elements(By.CSS_SELECTOR, 'a[href="javascript:void(0)"][onclick="getMore()"]')

# keep loading the page
while anchor_get_more is not None and len(anchor_get_more) > 0:
    anchor_get_more[0].click()
    time.sleep(random.uniform(2,4))
    anchor_get_more = driver.find_elements(By.CSS_SELECTOR, 'a[href="javascript:void(0)"][onclick="getMore()"]')

rows = []
tables = driver.find_elements(By.CSS_SELECTOR, 'table.datatable')


with open('members.csv', 'a') as file:
    for table in tables:
        for row in table.find_elements(By.TAG_NAME, 'tr'):
            columns = row.find_elements(By.TAG_NAME, 'td')
            if len(columns) < 7:
                continue
            file.write('|'.join([col.text for col in columns]) + '\n')

    driver.quit()
# for table in tables:
#     bulk_data = []
#     for row in table.find_elements(By.TAG_NAME, 'tr'):
#         columns = row.find_elements(By.TAG_NAME, 'td')
#         if len(columns) < 7:
#             continue
        # document = {
        #     "rank": int(columns[0].text),
        #     "name": columns[2].text,
        #     "age": int(columns[5].text),
        #     "city": columns[3].text,
        #     "usacId": columns[4].text
        # }
        # bulk_data.append({
        #     "index": {
        #         "_index": index_name,
        #         "_id": document["usacId"]
        #     }
        # })
        # document["all"] = json.dumps(document)
        # bulk_data.append(document)
        # if len(bulk_data) >= 500:
        #     response = requests.post(f'{es_url}/_bulk', headers={"Content-Type": "application/json",
        #                                                      "Authorization": "ApiKey cmpMMkFKVUJsM2lIcm0xX3pfV1M6VGlxVUJTRE1ReXU4V0M0UHNZM1hMZw=="},
        #                          data='\n'.join(json.dumps(d) for d in bulk_data) + '\n')
        #     bulk_data.clear()


