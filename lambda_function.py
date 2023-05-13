import boto3
import json

ec2 = boto3.client('ec2')

def start_instance(instance_id):
    print(f'Starting instance {instance_id}')
    ec2.start_instances(InstanceIds=[instance_id])

def stop_instance(instance_id):
    print(f'Stopping instance {instance_id}')
    ec2.stop_instances(InstanceIds=[instance_id])

def get_instance_state(instance_id):
    response = ec2.describe_instances(InstanceIds=[instance_id])
    instance = response['Reservations'][0]['Instances'][0]
    return instance['State']['Name']

def lambda_handler(event, context):
    body = json.loads(event['body'])
    instance_id = body['instance_id']
    
    # states can be: 
'pending'|'running'|'shutting-down'|'terminated'|'stopping'|'stopped'
    desired_state = body['desired_state']
    current_state = get_instance_state(instance_id)
    # i don't think i really like it this way, but whatever
    if current_state == desired_state:
        return {
            'statusCode': 200,
            'body': f'Instance {instance_id} is already {current_state}'
            
        }
        
    
    actions = {
        ('running', 'stopped'): stop_instance,
        ('stopped', 'running'): start_instance
    }

    action = actions.get((current_state, desired_state))
    if action:
        action(instance_id)
        return {
            'statusCode': 200,
            'body': f'Instance {instance_id} state changed to {desired_state}'
        }
    else:
        return {
            'statusCode': 400,
            'body': f'Cannot change instance {instance_id} state from 
{current_state} to {desired_state}'
        }

