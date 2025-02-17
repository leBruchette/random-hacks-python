import json
import requests
from datetime import datetime
from datetimerange import DateTimeRange

response = requests.get("https://candidate.hubteam.com/candidateTest/v3/problem/dataset?userKey=a538fb32e9c48f69e5f601f8d1f8")
response_json = response.json()

results = { 'results': [] }
callsPerCustomer = {}


# splits out the calls for a given customer
for record in response_json['callRecords']:
    if record['customerId'] not in callsPerCustomer:
        callsPerCustomer[record['customerId']] = {'calls': []}
    callsPerCustomer[record['customerId']]['calls'].append(record)
# print("Customers: " + str(len(callsPerCustomer)))
# print(json.dumps(callsPerCustomer, indent=4))


for customer in callsPerCustomer:
    # need a 'range' - start/end, will use this to compare calls against...
    callRanges = []
    for call in callsPerCustomer[customer]['calls']:
        callRanges.append({'start': call['startTimestamp'], 'end': call['endTimestamp']})

    concurrentCalls = {}

    # iterate over the comparison ranges...
    for callRange in callRanges:
        currCallRange = DateTimeRange(start_datetime=datetime.fromtimestamp(callRange['start'] / 1000), end_datetime=datetime.fromtimestamp(callRange['end'] / 1000))

        # and compare each customer call against the current call range
        for currCustomerCall in callsPerCustomer[customer]['calls']:
            customerCallRange = DateTimeRange(start_datetime=datetime.fromtimestamp(currCustomerCall['startTimestamp'] / 1000), end_datetime=datetime.fromtimestamp(currCustomerCall['endTimestamp'] / 1000))

            # if the ranges intersect, we have a concurrent call
            if currCallRange.is_intersection(customerCallRange):
                rangeKey = f"{callRange['start']}_{callRange['end']}"

                # for each range, keep track of the callIds that intersect as well as the specific range per call
                # this will provide a handle on the range having the most concurrent calls
                if rangeKey not in concurrentCalls:
                    concurrentCalls[rangeKey] = {'callIds': set(), 'intersection': []}
                concurrentCalls[rangeKey]['callIds'].add(currCustomerCall['callId'])
                concurrentCalls[rangeKey]['intersection'].append(customerCallRange)


    maxConcurrentCalls = 0
    maxTimeRange = None
    #get the range with the most concurrent calls
    for rangeKey, calls in concurrentCalls.items():
        if len(calls) > maxConcurrentCalls:
            maxConcurrentCalls = len(calls['callIds'])
            maxTimeRange = rangeKey

    # then iterate over the specific callIds' ranges for the max concurrent calls range to determine a point-in-time
    # that all calls share
    overlapTimestamp = 0
    for ranges in concurrentCalls[maxTimeRange].items():
        # print(ranges)
        # sort the range in descending order on the timedelta, thought being as we iterate over each range
        # and find an intersection, N will contain the intersection of N+1, and N+1 will contain the intersection of N+2
        # this might be flawed...
        intersection_ranges = sorted(concurrentCalls[maxTimeRange]['intersection'], key=lambda r: r.timedelta, reverse=True)
        overlapTime = intersection_ranges[0]
        for r in intersection_ranges[1:]:
            if overlapTime.is_intersection(r):
                overlapTime = overlapTime.intersection(r)

        print(overlapTime)
        if overlapTime.start_datetime is None or overlapTime.end_datetime is None:
            overlapTime = 0 # not good
        else:
            overlapTimestamp = int((overlapTime.start_datetime.timestamp() + overlapTime.end_datetime.timestamp()) / 2 * 1000)


    # print("intersectino")
    # for ranges in concurrentCalls[maxTimeRange]['intersection']:
    #     print(datetime.fromtimestamp(overlapTimestamp/1000).strftime('%Y-%m-%dT%H:%M:%S'))
    #     # print(int(overlapTimestamp/1000))
    #     print(ranges)

    results['results'].append({
        'customerId': customer,
        'date': datetime.fromtimestamp(overlapTimestamp / 1000).strftime('%Y-%m-%d'),
        'maxConcurrentCalls': maxConcurrentCalls,
        'timestamp': int(overlapTimestamp),
        'callIds': list(concurrentCalls[maxTimeRange]['callIds'])
    })

    print(json.dumps(results, indent=4))

response = requests.post('https://candidate.hubteam.com/candidateTest/v3/problem/result?userKey=a538fb32e9c48f69e5f601f8d1f8', json=results)
# response = requests.post('https://cyqt90mz1wg00002k6v0gxm7rocyyyyyb.oast.pro', json=results)
print(response.content)