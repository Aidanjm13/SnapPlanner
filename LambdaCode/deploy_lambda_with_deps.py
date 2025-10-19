import boto3
import zipfile
import os
import subprocess
import shutil
from dotenv import load_dotenv

def deploy_lambda_with_deps():
    load_dotenv()
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    # Install dependencies to a temp directory
    if os.path.exists('lambda_package'):
        shutil.rmtree('lambda_package')
    os.makedirs('lambda_package')

    subprocess.run(['pip', 'install', 'PyPDF2==3.0.1', '--no-deps', '-t', 'lambda_package'])
    subprocess.run(['pip', 'install', 'typing_extensions', '-t', 'lambda_package'])

    
    # Create deployment package
    with zipfile.ZipFile('lambda_deployment.zip', 'w') as zip_file:
        # Add the lambda function
        zip_file.write('LambdaCode/lambda_function.py', 'lambda_function.py')
        
        # Add dependencies
        for root, dirs, files in os.walk('lambda_package'):
            for file in files:
                file_path = os.path.join(root, file)
                arc_name = os.path.relpath(file_path, 'lambda_package')
                zip_file.write(file_path, arc_name)
    
    # Update Lambda function
    with open('lambda_deployment.zip', 'rb') as zip_file:
        lambda_client.update_function_code(
            FunctionName='SnapPlannerFunction',
            ZipFile=zip_file.read()
        )
    
    # Clean up
    shutil.rmtree('lambda_package')
    os.remove('lambda_deployment.zip')
    print("Lambda function updated with PyPDF2 dependency")

if __name__ == "__main__":
    deploy_lambda_with_deps()