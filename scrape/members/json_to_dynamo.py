import os

import boto3
import datetime
import json
import random
import requests
import time as _time

from bs4 import BeautifulSoup
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from dotenv import load_dotenv

load_dotenv()


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


with open('data/members.json', 'r') as file:
    members = json.load(file)
    for member in members:
        license_id = member['usacId']
        url = "https://{sub}.{domain1}{domain2}.{suffix}/results/index.php?{queryParm}={id}".format(sub='legacy',
                                                                                                    domain1='usa',
                                                                                                    domain2='cycling',
                                                                                                    suffix='org',
                                                                                                    queryParm="compid",
                                                                                                    id=license_id)

        print(f"Scraping {url}")
        _time.sleep(random.uniform(3, 7))
        response = requests.get(url)
        if response.status_code == 200:
            dynamodb = boto3.resource('dynamodb',
                                      endpoint_url=os.getenv('AWS_DYNAMO_ENDPOINT'),
                                      aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                                      aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                                      region_name=os.getenv('AWS_REGION'))
            ddb_table = dynamodb.Table('results')

            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            current_result = RaceResult(None, None)

            # just look at the <table> with align=center - this contains the result data
            table = soup.find_all('table', {'align': 'center'})
            if len(table) == 0:
                print('No results found for id {}'.format(license_id))
                continue
            for row in table[0].find_all('tr'):
                if is_race_result_hydrated():
                    usac_profile = {
                        'pk_usac_or_event_id': 'USAC#' + str(current_result.result.license),
                        'sk_result': 'PROFILE',
                        'type': 'USER',
                        'name': current_result.result.name,
                        'license': current_result.result.license,
                        'club': current_result.result.club,
                    }
                    try:
                        ddb_table.put_item(Item=usac_profile,
                                           ConditionExpression='attribute_not_exists(pk_usac_or_event_id)')
                    except ddb_table.meta.client.exceptions.ConditionalCheckFailedException:
                        pass  # going to ignore and only write a profile once

                    user_result = {
                        'pk_usac_or_event_id': 'USAC#' + str(current_result.result.license),
                        'sk_result': 'RESULT#' + str(current_result.event.date) + "#" + str(
                            current_result.event.permit),
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
                        ddb_table.put_item(Item=event,
                                           ConditionExpression='attribute_not_exists(pk_usac_or_event_id)')
                    except ddb_table.meta.client.exceptions.ConditionalCheckFailedException:
                        pass

                    event_results = {
                        'pk_usac_or_event_id': 'EVENT#' + str(current_result.event.permit),
                        'sk_result': 'RESULT#' + str(current_result.event.date) + "#" + str(
                            current_result.event.permit) + "#" + str(current_result.result.license),
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
                        ddb_table.put_item(Item=event_results,
                                           ConditionExpression='attribute_not_exists(sk_result)')
                    except ddb_table.meta.client.exceptions.ConditionalCheckFailedException:
                        pass

                    current_result = RaceResult(None, None)

                cols = row.find_all('td')
                if is_event_row():  # event info (header) row
                    span = cols[0].find('span', {'class': 'homearticleheader'})
                    if span:
                        date_event = span.text.strip().split(' - ')
                        try:
                            date = datetime.datetime.strptime(date_event[0], '%m/%d/%Y').date().strftime('%Y-%m-%d')
                        except ValueError:
                            date = '1970-01-01'
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
