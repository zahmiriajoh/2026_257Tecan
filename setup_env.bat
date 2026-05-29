@echo off
echo Activating PyLabRobot environment...
call .\env\Scripts\activate

echo Checking and installing dependencies from requirements.txt...
pip install -r requirements.txt --quiet

echo Environment ready!