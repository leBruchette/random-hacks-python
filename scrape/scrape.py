import argparse
import json
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Event:
    date: str
    name: str
    permit: str
    discipline: str


@dataclass_json
@dataclass
class Result:
    position: str
    points: str
    name: str
    license: str
    time: str
    bib: str
    club: str


@dataclass_json
@dataclass
class RaceResult:
    event: Event
    result: Result


def is_race_result_hydrated():
    return current_result.result is not None and current_result.event is not None


def is_result_row():
    return len(cols) == 7


def is_event_row():
    return len(cols) == 1


parser = argparse.ArgumentParser(
    description='Scrapes race results from usa cycling dot org for a given rider\'s license number')
parser.add_argument('id', type=int, help='license number to scrape results for')

with open ('members.json', 'r') as file:
    members = json.load(file)
    for member in members:
        compid = member['usacId']

args = parser.parse_args()
url = ("https://{sub}.{domain1}{domain2}.{suffix}/results/index.php?{queryParm}={id}"
       .format(sub='legacy',
               domain1='usa',
               domain2='cycling',
               suffix='org',
               queryParm="compid",
               id=args.id))
response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.content, 'html.parser')
    results = []
    current_result = RaceResult(None, None)

    # just look at the <table> with align=center - this contains the result data
    table = soup.find_all('table', {'align': 'center'})
    if len(table) == 0:
        print('No results found for id {}'.format(args.id))
        exit(0)
    for row in table[0].find_all('tr'):
        if is_race_result_hydrated():
            results.append(current_result)
            current_result = RaceResult(None, None)

        cols = row.find_all('td')
        if is_event_row():  # event info (header) row
            span = cols[0].find('span', {'class': 'homearticleheader'})
            if span:
                date_event = span.text.strip().split(' - ')
                date = date_event[0]
                event_name = span.find('a').text.strip()
                permit = span.find('a')['href'].split('=')[1]
                discipline = cols[0].find('span', {'title': 'discipline'}).text.strip()
                current_result.event = Event(date, event_name, permit, discipline)

        if is_result_row():  # event result row
            position = cols[0].text.strip()
            points = cols[1].text.strip()
            name = cols[2].text.strip()
            license = cols[3].text.strip()
            time = cols[4].text.strip()
            bib = cols[5].text.strip()
            club = cols[6].text.strip()
            current_result.result = Result(position, points, name, license, time, bib, club)

    print(RaceResult.schema().dumps(results, many=True, indent=4))

else:
    print(f"Failed to parse results. \n\tStatus code: {response.status_code}\n\tMessage: {response.text}")
