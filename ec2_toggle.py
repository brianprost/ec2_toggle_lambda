import boto3
import json

ec2 = boto3.client('ec2')


def get_public_dns_name(instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response['Reservations'][0]['Instances'][0]
    return instance['PublicDnsName'] #ipv4 dns name


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
    try:
        if desired_state == 'running':
            if (current_state != 'stopped'):
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'public_dns_name': get_public_dns_name(instance_id),
                        'message': f'Instance already running',
                    })
                }
            ec2.start_instances(InstanceIds=[instance_id])
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'public_dns_name': get_public_dns_name(instance_id),
                    'message': f'Started instance {instance_id}',
                })
            }
        elif desired_state == 'stopped':
            if (current_state != 'running'):
                return {
                    'statusCode': 400,
                    'body': json.dumps({
                        'message': f'Cannot stop an instance that is {current_state}',
                    })
                }
            ec2.stop_instances(InstanceIds=[instance_id])
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Stopped instance {instance_id}',
                })
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"{e}"
        }