import requests
import json
import random
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service

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

with open('data/members.csv', 'a') as file:
    for table in tables:
        for row in table.find_elements(By.TAG_NAME, 'tr'):
            columns = row.find_elements(By.TAG_NAME, 'td')
            if len(columns) < 7:
                continue
            file.write('|'.join([col.text for col in columns]) + '\n')

    driver.quit()
