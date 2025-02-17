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


url = 'https://legacy.usacycling.org/rankings/points.php?state=&sex=M&disc=Road%3ACRIT&cat=&agemin=1&agemax=99&mode=get_rank'
driver.get(url)
time.sleep(3)

# Create a directory to store the results for permit id
# members_dir = f'./data/members'
# os.makedirs(members_dir, exist_ok=True)

# Find anchor tags with href containing javascript:void(0)

anchor_get_more = driver.find_elements(By.CSS_SELECTOR, 'a[href="javascript:void(0)"][onclick="getMore()"]')
# anchor_get_more[0].click()
# time.sleep(random.uniform(2, 4))

# keep loading the page
while anchor_get_more is not None and len(anchor_get_more) > 0:
    anchor_get_more[0].click()
    time.sleep(random.uniform(2,4))
    anchor_get_more = driver.find_elements(By.CSS_SELECTOR, 'a[href="javascript:void(0)"][onclick="getMore()"]')


rows = []
tables = driver.find_elements(By.CSS_SELECTOR, 'table.datatable')
for table in tables:
    for row in table.find_elements(By.TAG_NAME, 'tr'):
        rows.append(row)

print(f'Found {len(rows)} rows')

# should be able to add each row in our elasticsearch index
# PUT /members/_doc/{usac_id}
# {
#     "data": "{
#       \"name\":\"Mike Bruzina\",
#       \"team\":\"Cyclex Racing\",
#       \"city\":\"Hartsburg, MO\",
#       \"id\":\"282794\",
#       }"
# }


for row in rows:
    columns = row.find_elements(By.TAG_NAME, 'td')
    if len(columns) < 7:
        continue
    document = {
        "rank": int(columns[0].text),
        "name": columns[2].text,
        "age": int(columns[5].text),
        "city": columns[3].text,
        "usacId": columns[4].text
    #     todo - make a keyword field that is all of these fields concatenated
    }
    document["all"] = json.dumps(document)
    response = requests.put(f'{es_url}/_doc/{document["usacId"]}', headers={"Content-Type": "application/json", "Authorization": "ApiKey cmpMMkFKVUJsM2lIcm0xX3pfV1M6VGlxVUJTRE1ReXU4V0M0UHNZM1hMZw=="}, data=json.dumps(document))



driver.quit()
