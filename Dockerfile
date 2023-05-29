FROM public.ecr.aws/lambda/python:3.10

COPY ec2_toggle.py ${LAMBDA_TASK_ROOT}

CMD [ "ec2_toggle.handler" ]
