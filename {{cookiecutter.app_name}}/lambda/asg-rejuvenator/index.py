import os
import time
import datetime
import json
import boto3

ASG = os.environ['ASG']
RUNTIME_THRESHOLD = os.environ['RUNTIME_THRESHOLD']
REQUEST_ID = None


class RejuvenationFailed(RuntimeError):
    pass


class RejuvenationTimedOut(RuntimeError):
    pass


def rejuvenate(context, payload_instances):
    freeze(ASG)

    asg_client = boto3.client('autoscaling')
    asg_state = single_entry_only(asg_client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[ASG])['AutoScalingGroups'])
    target_group_arn = single_entry_only(asg_state['TargetGroupARNs'])

    if asg_desired_capacity() < 2:
        raise RejuvenationFailed(
            "Authoscaling group {} has too small a DesiredCapacity for instances replacement".format(ASG))

    instances = payload_instances if payload_instances != [] else list(map(
        lambda x: x['InstanceId'], asg_state['Instances']))
    replace_instances(target_group_arn, instances, context)


def single_entry_only(lst):
    assert len(lst) == 1
    return lst[0]


def replace_instances(target_group_arn, instances, context):
    if len(instances) == 0:
        log('All instances in the autoscaling group were replaced')
        return
    if enough_execution_time(context):
        head, *tail = instances
        log('Getting ready to remove instance {} from the list of {}'.format(
            head, instances))

        try:
            terminate_instance(target_group_arn, head, context)
        except RejuvenationTimedOut:
            log('There is not enough execution time left for this lambda invocation, recursing into a new lambda call')
            lambda_recurse(context, instances)
            return

        replace_instances(target_group_arn, tail, context)

    else:
        log('There is not enough execution time left for this lambda invocation, recursing into a new lambda call')
        lambda_recurse(context, instances)


def terminate_instance(target_group_arn, instance_id, context):
    log('Waiting for the target group to stabilize before shutting down instance {}'.format(instance_id))
    wait_until_tg_stabilizes(target_group_arn, context)
    log('Target group is healthy now, going to shutdown instance {}'.format(instance_id))
    asg_client = boto3.client('autoscaling')
    asg_client.set_instance_health(
        InstanceId=instance_id,
        HealthStatus='Unhealthy')


def wait_until_tg_stabilizes(target_group_arn, context):
    log('Pausing before checking the target group health')
    time.sleep(target_group_interval(target_group_arn))

    elb_client = boto3.client('elbv2')

    statuses = [target['TargetHealth']['State']
                for target
                in elb_client.describe_target_health(TargetGroupArn=target_group_arn)['TargetHealthDescriptions']]
    healthy = list(filter(lambda x: x == 'healthy', statuses))

    log('Current target group status: {}'.format(statuses))

    if not len(healthy) >= asg_desired_capacity():
        log('There are still unhealthy instances in the target group')
        if enough_execution_time(context):
            wait_until_tg_stabilizes(target_group_arn, context)
        else:
            raise RejuvenationTimedOut(
                "Target group {} did not reach the all-healthy state during rejuvenation".format(target_group_arn))


def target_group_interval(target_group_arn):
    elb_client = boto3.client('elbv2')
    tg_info = single_entry_only(elb_client.describe_target_groups(
        TargetGroupArns=[target_group_arn])['TargetGroups'])
    return tg_info['HealthCheckIntervalSeconds']


def asg_desired_capacity():
    asg_client = boto3.client('autoscaling')
    asg_state = single_entry_only(asg_client.describe_auto_scaling_groups(
        AutoScalingGroupNames=[ASG])['AutoScalingGroups'])
    return int(asg_state['DesiredCapacity'])


def enough_execution_time(context):
    if context.get_remaining_time_in_millis() / 1000 > int(RUNTIME_THRESHOLD):
        return True
    else:
        return False


def lambda_recurse(context, instances):
    my_arn = context.invoked_function_arn
    lambda_params = {'instances': instances}
    payload = json.dumps(lambda_params)

    log('Passing remaining list of instances to a new lambda call: {}'.format(instances))
    lambda_client = boto3.client('lambda')
    lambda_client.invoke(
        FunctionName=my_arn,
        InvocationType='Event',
        Payload=payload)
    log('Async lambda call issued')


def freeze(asg_name):
    asg_client = boto3.client('autoscaling')
    log('About to suspend autoscaling processes')
    res = asg_client.suspend_processes(
        AutoScalingGroupName=asg_name,
        ScalingProcesses=['AZRebalance', 'ScheduledActions', 'AlarmNotification'])
    log("Autoscaling suspend API call result: {}".format(res))


def thaw(asg_name):
    asg_client = boto3.client('autoscaling')
    log('About to resume autoscaling processes')
    res = asg_client.resume_processes(AutoScalingGroupName=asg_name)
    log("Autoscaling resume API call result: {}".format(res))


def log(message, *args, **kwargs):
    if args or kwargs:
        message = message.format(*args, **kwargs)

    ts = datetime.datetime.fromtimestamp(
        time.time()).strftime('%Y-%m-%d %H:%M:%S')
    print(ts, REQUEST_ID, message)


def lambda_handler(payload, context):
    global REQUEST_ID
    try:
        REQUEST_ID = context.aws_request_id
        instances = []
        if 'instances' in payload:
            log('Received an instances list as a parameter: {}'.format(
                payload['instances']))
            instances = payload['instances']
        rejuvenate(context, instances)
    except Exception as exn:
        log(exn)
        raise
    finally:
        thaw(ASG)
        log('Finishing execution now')
