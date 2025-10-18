import boto3
import zipfile
import os
from dotenv import load_dotenv

def update_lambda():
    load_dotenv()
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Create deployment package
    with zipfile.ZipFile('lambda_update.zip', 'w') as zip_file:
        zip_file.write('LambdaCode/lambda_function.py', 'lambda_function.py')
    
    # Update Lambda function code
    with open('lambda_update.zip', 'rb') as zip_file:
        lambda_client.update_function_code(
            FunctionName='SnapPlannerFunction',
            ZipFile=zip_file.read()
        )
    
    # Clean up
    os.remove('lambda_update.zip')
    print("Lambda function updated successfully")

if __name__ == "__main__":
    update_lambda()