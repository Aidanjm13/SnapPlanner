@echo off
echo Installing dependencies...
pip install -r requirements.txt

echo Deploying Lambda function...
@REM "C:\Users\bravo\AppData\Roaming\Python\Python311\Scripts\ipython3.exe" deploy.py

echo Testing Lambda function...
"C:\Users\bravo\AppData\Roaming\Python\Python311\Scripts\ipython3.exe" test_lambda.py

pause