#!/usr/bin/env python

import boto3
import time
import re
import sys
import itertools

eb = boto3.client('elasticbeanstalk')

APP = sys.argv[1]


def die(msg):
    print("*** {}".format(msg))
    sys.exit(1)


envs = list(
    filter(lambda env: re.search(r"(?i){}".format(APP), env['ApplicationName']),
           eb.describe_environments()['Environments']))

if len(envs) > 1:
    die("Application name is ambiguous: more than 1 EB environment found.")

env_name = envs[0]['EnvironmentName']

events = eb.describe_events(EnvironmentName=env_name)['Events']
events_since_deployment_began = list(itertools.takewhile(
    lambda event: event['Message'] != 'Environment update is starting.', events))
deployment_start_time = events_since_deployment_began[-1]['EventDate']

while True:
    if any(map(lambda x: x['Message'] == 'Environment update completed successfully.', events_since_deployment_began)):
        print('Ok')
        break

    if any(map(lambda x: x['Severity'] in ['ERROR', 'FATAL'], events_since_deployment_began)):
        error_events = list(
            filter(lambda x: x['Severity'] in ['ERROR', 'FATAL'], events_since_deployment_began))
        die("Deployment has failed:\n{}\n---".format(error_events))

    print('Waiting for 30 seconds...')
    time.sleep(30)
    events_since_deployment_began = eb.describe_events(EnvironmentName=env_name,
                                                       StartTime=deployment_start_time)
