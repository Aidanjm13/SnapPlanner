import boto3
import zipfile
import json

def deploy_lambda():
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    iam_client = boto3.client('iam', region_name='us-east-1')
    
    # Create deployment package
    with zipfile.ZipFile('lambda_deployment.zip', 'w') as zip_file:
        zip_file.write('lambda_function.py')
    
    # IAM role policy
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    
    execution_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream", 
                "logs:PutLogEvents",
                "textract:AnalyzeDocument",
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        }]
    }
    
    # Use existing participant role
    role_arn = 'arn:aws:iam::747526414426:role/WSParticipantRole'
    
    # Deploy Lambda
    with open('lambda_deployment.zip', 'rb') as zip_file:
        try:
            lambda_client.create_function(
                FunctionName='SnapPlannerFunction',
                Runtime='python3.9',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_file.read()},
                Timeout=60
            )
            print("Lambda function created successfully")
        except lambda_client.exceptions.ResourceConflictException:
            zip_file.seek(0)
            lambda_client.update_function_code(
                FunctionName='SnapPlannerFunction',
                ZipFile=zip_file.read()
            )
            print("Lambda function updated successfully")

if __name__ == "__main__":
    deploy_lambda()