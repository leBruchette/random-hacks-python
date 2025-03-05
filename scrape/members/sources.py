import boto3
import os
from dotenv import load_dotenv

load_dotenv()

rankings_url = "https://{sub}.{domain1}{domain2}.{suffix}/{context}/{page}.php?state=&sex=M&disc=Road%3ACRIT&cat=&agemin=1&agemax=99&mode=get_rank".format(
    sub='legacy',
    domain1='usa',
    domain2='cycling',
    suffix='org',
    context='rankings',
    page='points')

dynamodb = boto3.resource('dynamodb',
                          endpoint_url=os.getenv('AWS_DYNAMO_ENDPOINT'),
                          aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                          aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                          region_name=os.getenv('AWS_REGION'))
