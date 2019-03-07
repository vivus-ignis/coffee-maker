#!/usr/bin/env python

import boto3
import time
import re
import sys

eb = boto3.client('elasticbeanstalk')

APP = sys.argv[1]

while True:
    envs = list(
        filter(lambda env: re.search(r"(?i){}".format(APP), env['ApplicationName']),
               eb.describe_environments()['Environments']))

    summary = {env['ApplicationName']: {
        'status': env['Status'], 'health': env['Health']} for env in envs}
    print(summary)

    not_ready = list(
        filter(lambda env_state: env_state['status'] not in ['Ready', 'Terminated'] or env_state['health'] != 'Green',
               map(lambda env: {'status': env['Status'], 'health': env['Health']}, envs)))
    if len(not_ready) == 0:
        break
    else:
        print('Waiting for 30 seconds...')
        time.sleep(30)
print('Ok.')
