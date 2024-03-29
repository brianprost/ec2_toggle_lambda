from datetime import datetime
import json
import time
import boto3

ec2 = boto3.client('ec2')
ssm = boto3.client('ssm')


def describe_instance(instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    return response['Reservations'][0]['Instances'][0]


def get_public_dns_name(instance_id):
    instance = describe_instance(instance_id)
    public_dns_name = instance.get('PublicDnsName')
    return public_dns_name


def get_instance_state(instance_id):
    instance = describe_instance(instance_id)
    return instance['State']['Name']


def terminate_instance(instance_id):
    ec2.terminate_instances(InstanceIds=[instance_id])


def start_instance(instance_id):
    if get_instance_state(instance_id) != 'stopped':
        return {
            'statusCode': 400,
            'body': json.dumps({
                'public_dns_name': get_public_dns_name(instance_id),
                'message': f'Instance already running',
            })
        }
    ec2.start_instances(InstanceIds=[instance_id])

    # wait until it has a public ip address, and then get it and assign it
    while True:
        public_dns_name = get_public_dns_name(instance_id)
        if public_dns_name:
            break
        print("Waiting for instance to be running and have a public DNS name...")
        time.sleep(5)

    return {
        'statusCode': 200,
        'body': json.dumps({
            'public_dns_name': public_dns_name,
            'message': f'Started instance {instance_id}',
        })
    }


def stop_instance(instance_id):
    if get_instance_state(instance_id) != 'running':
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': f'Cannot stop an instance that is {get_instance_state(instance_id)}',
            })
        }
    ec2.stop_instances(InstanceIds=[instance_id])
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Stopped instance {instance_id}',
        })
    }


def delete_instance(instance_id):
    current_state = get_instance_state(instance_id)
    if current_state in ['pending', 'running', 'stopping']:
        stop_instance(instance_id)
    terminate_instance(instance_id)
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Terminated instance {instance_id}',
        })
    }


def update_ssm_parameter(key: str, value: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ssm.put_parameter(
        Name=key,
        Description=f'Updated at {timestamp} by ec2_toggle.py',
        Value=value,
        Type='String',
        Overwrite=True
    )


def lambda_handler(event, context):
    body = json.loads(event['body'])
    instance_id = body['instance_id']
    print(f'instance_id: {instance_id}')

    # states can be: 'pending'|'running'|'shutting-down'|'terminated'|'stopping'|'stopped'|'delete'
    desired_state = body['desired_state']
    print(f'desired_state: {desired_state}')

    try:
        if desired_state == 'running':
            return start_instance(instance_id)
        elif desired_state == 'stopped':
            return stop_instance(instance_id)
        elif desired_state == 'delete':
            return delete_instance(instance_id)
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)}),
        }
