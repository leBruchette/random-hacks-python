import json


with open('members.csv', 'r') as file:
    bulk_data = []
    total_count = 0
    for line in file:
        member_record = line.strip().split('|')

        bulk_data.append(
            {
            "rank": int(member_record[0]),
            "name": member_record[2],
            "age": int(member_record[5]),
            "city": member_record[3],
            "usacId": member_record[4],
            })

with open('members.json', 'a') as json_file:
    json.dump(bulk_data, json_file)

