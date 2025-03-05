import requests
from bs4 import BeautifulSoup

# Scrape the event permit URLs after searching with an empty query of ''
# These will be written to a file for later processing
url = "https://{sub}.{domain1}{domain2}.{suffix}/results/index.php?event=%27+%27".format(sub='legacy',
                                                                                            domain1='usa',
                                                                                            domain2='cycling',
                                                                                            suffix='org')

response = requests.get(url)
if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')
    anchors = soup.find_all('a', href=lambda href: href and '/results/index.php?year=' in href)
    for anchor in anchors:
        with open('data/events.txt', 'a') as file:
            file.write(anchor['href'] + '\n')

