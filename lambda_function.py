import boto3
import json

ec2 = boto3.client('ec2')


def start_instance(instance_id):
    print(f'Starting instance {instance_id}')
    ec2.start_instances(InstanceIds=[instance_id])


def get_public_dns_name(instance_id):
    # wait until the instance is running, and then get the public ip
    waiter = ec2.get_waiter('instance_running')
    waiter.wait(InstanceIds=[instance_id])
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response['Reservations'][0]['Instances'][0]
    return instance['PublicDnsName'] #ipv4 dns name


def stop_instance(instance_id):
    if (get_instance_state(instance_id) == 'stopped'):
        return
    print(f'Stopping instance {instance_id}')
    ec2.stop_instances(InstanceIds=[instance_id])
    waiter = ec2.get_waiter('instance_stopped')
    waiter.wait(InstanceIds=[instance_id])


def get_instance_state(instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response['Reservations'][0]['Instances'][0]
    return instance['State']['Name']


def lambda_handler(event, context):
    body = json.loads(event['body'])
    instance_id = body['instance_id']

    # states can be: 'pending'|'running'|'shutting-down'|'terminated'|'stopping'|'stopped'
    desired_state = body['desired_state']
    current_state = get_instance_state(instance_id)
    # # i don't think i really like it this way, but whatever
    # if current_state == desired_state:
    #     return {
    #         'statusCode': 200,
    #         'body': f'Instance {instance_id} is already {current_state} {"at " + get_public_dns_name() if desired_state == "running" else ""}'

    #     }

    actions = {
        ('running', 'stopped'): stop_instance,
        ('stopped', 'running'): start_instance,
        ('running', 'running'): start_instance,
        ('stopped', 'stopped'): stop_instance
    }

    action = actions.get((current_state, desired_state))
    if action:
        action(instance_id)
        # if desired state is running, we need to wait until the instance is running
        if desired_state != 'running':
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'instance_id': instance_id,
                    'instance_state': desired_state,
                })
            }
        public_dns_name = get_public_dns_name(instance_id)
        return {
            'statusCode': 200,
            'body': json.dumps({
                'instance_id': instance_id,
                'instance_state': desired_state,
                'public_dns_name': public_dns_name
            })
        }
    else:
        return {
            'statusCode': 400,
            'body': f'Cannot change instance {instance_id} state from {current_state} to {desired_state}'
        }
