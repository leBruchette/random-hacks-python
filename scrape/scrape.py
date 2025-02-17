import argparse
<<<<<<< HEAD
import json
=======
import boto3
import datetime
>>>>>>> 923ea3a (unignored hubspot interview)
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
<<<<<<< HEAD
=======

>>>>>>> 923ea3a (unignored hubspot interview)
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
# parser.add_argument('id', type=int, help='license number to scrape results for')
parser.add_argument('id', type=int, nargs='+', help='license numbers to scrape results for')

args = parser.parse_args()
urls = [("https://{sub}.{domain1}{domain2}.{suffix}/results/index.php?{queryParm}={id}"
         .format(sub='legacy',
                 domain1='usa',
                 domain2='cycling',
                 suffix='org',
                 queryParm="compid",
                 id=license_id)) for license_id in args.id]
for url in urls:
    print(f"Scraping {url}")
    response = requests.get(url)
    if response.status_code == 200:
        dynamodb = boto3.resource('dynamodb', endpoint_url='http://0.0.0.0:8000', aws_access_key_id='AKIA2BOGUSAWSKEYJ2QW',
                                  aws_secret_access_key='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', region_name='us-east-1')
        ddb_table = dynamodb.Table('results')

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
                # ddb_table.put_item(
                #     Item= {
                #         'usac_date': "{usac}#{date}#{discipline}".format(usac=current_result.result.license, date=str(current_result.event.date), discipline=current_result.event.discipline),
                #         'event': current_result.event.__dict__,
                #         'result': current_result.result.__dict__
                #     }
                # )

                usac_profile = {
                    'pk_usac_or_event_id': 'USAC#' + str(current_result.result.license),
                    'sk_result': 'PROFILE',
                    'type': 'USER',
                    'name': current_result.result.name,
                    'license': current_result.result.license,
                    'club': current_result.result.club,
                }
                try:
                    ddb_table.put_item(Item=usac_profile, ConditionExpression='attribute_not_exists(pk_usac_or_event_id)')
                except ddb_table.meta.client.exceptions.ConditionalCheckFailedException:
                    pass #going to ignore and only write a profile once

                user_result = {
                    'pk_usac_or_event_id': 'USAC#' + str(current_result.result.license),
                    'sk_result': 'RESULT#' + str(current_result.event.date)+"#"+str(current_result.event.permit),
                    'type': 'RESULT',
                    'discipline': current_result.event.discipline.upper(),
                    'name': current_result.event.name,
                    'timestamp': current_result.event.date,
                    'data': {
                        'date': current_result.event.date,
                        'name': current_result.event.name,
                        'permit': current_result.event.permit,
                        'discipline': current_result.event.discipline,
                        'license': current_result.result.license,
                        'position': current_result.result.position,
                        'points': current_result.result.points,
                        'bib': current_result.result.bib,
                    },
                }
                ddb_table.put_item(Item=user_result)

                event = {
                    'pk_usac_or_event_id': 'EVENT#' + str(current_result.event.permit),
                    'sk_result': 'PROFILE',
                    'type': 'EVENT',
                    'discipline': current_result.event.discipline.upper(),
                    'name': current_result.event.name,
                    'timestamp': current_result.event.date,
                }

                try:
                    ddb_table.put_item(Item=event, ConditionExpression='attribute_not_exists(pk_usac_or_event_id)')
                except ddb_table.meta.client.exceptions.ConditionalCheckFailedException:
                    pass

                event_results = {
                    'pk_usac_or_event_id': 'EVENT#' + str(current_result.event.permit),
                    'sk_result': 'RESULT#' + str(current_result.event.date)+"#"+str(current_result.event.permit)+"#"+str(current_result.result.license),
                    'type': 'EVENTRESULTS',
                    'discipline': current_result.event.discipline.upper(),
                    'timestamp': current_result.event.date,
                    'name': current_result.event.name,
                    'result': {
                        'license': current_result.result.license,
                        'position': current_result.result.position,
                        'category': 'TBD',
                        'bib': current_result.result.bib,
                    },
                }
                # this could occur if we have multiple categories in the same event
                try:
                    ddb_table.put_item(Item=event_results, ConditionExpression='attribute_not_exists(sk_result)')
                except ddb_table.meta.client.exceptions.ConditionalCheckFailedException:
                    pass

                current_result = RaceResult(None, None)

            cols = row.find_all('td')
            if is_event_row():  # event info (header) row
                span = cols[0].find('span', {'class': 'homearticleheader'})
                if span:
                    date_event = span.text.strip().split(' - ')
                    date = datetime.datetime.strptime(date_event[0], '%m/%d/%Y').date().strftime('%Y-%m-%d')
                    event_name = span.find('a').text.strip()
                    permit = span.find('a')['href'].split('=')[1]
                    discipline = cols[0].find('span', {'title': 'discipline'}).text.strip().lower()
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
    else:
        print(f"Failed to parse results. \n\tStatus code: {response.status_code}\n\tMessage: {response.text}")
